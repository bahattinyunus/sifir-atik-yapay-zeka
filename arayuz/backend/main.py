import json
import asyncio
import io
import time
import psutil
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel, Field

from database import (
    init_db, save_detection, get_stats, get_recent_detections,
    get_hourly_breakdown, get_settings, update_setting, log_event,
    export_csv_content, get_environmental_impact, get_system_logs
)

# SQLite veri tabanını başlat
init_db()

app = FastAPI(
    title="Sıfır Atık YZ - Akıllı Geri Dönüşüm Backend",
    version="2.0.0",
    description="Edge-AI destekli polimer sınıflandırma ve konveyör bant ayıklama sistemi API servisi."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        text = json.dumps(message)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(text)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()
SERVER_START_TIME = time.time()

# Pydantic Veri Modelleri
class WasteData(BaseModel):
    type: str = Field(..., description="Atık türü: PET, HDPE, Naylon, PUR, Metal, Reject", json_schema_extra={"example": "PET"})
    confidence: float = Field(..., ge=0.0, le=100.0, json_schema_extra={"example": 96.4})
    timestamp: str = Field(..., json_schema_extra={"example": "14:32:05"})
    inference_ms: Optional[float] = Field(default=14.5, description="Model çıkarım süresi ms")
    actuated: Optional[bool] = Field(default=True, description="Fiziksel valf veya servo tetiklendi mi?")
    source: Optional[str] = Field(default="edge-camera", description="Tespit kaynağı")

class ConfigUpdate(BaseModel):
    confidence_threshold: Optional[str] = None
    conveyor_speed_m_s: Optional[str] = None
    valve_delay_ms: Optional[str] = None
    valve_pulse_ms: Optional[str] = None
    active_mode: Optional[str] = None
    camera_resolution: Optional[str] = None

class SimulationRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=20)
    force_type: Optional[str] = None

# Örnek Başlangıç Tohum Verisi (Database boş ise yüklenir)
def seed_initial_data_if_empty():
    stats = get_stats()
    if stats["total_count"] == 0:
        import random
        types = ["PET", "HDPE", "Naylon", "PUR", "Metal", "Reject"]
        weights = [0.35, 0.25, 0.12, 0.10, 0.12, 0.06]
        now = datetime.now()
        for i in range(120):
            chosen = random.choices(types, weights=weights)[0]
            conf = round(random.uniform(85.0, 99.5), 1) if chosen != "Reject" else round(random.uniform(50.0, 74.0), 1)
            t_str = (now).strftime("%H:%M:%S")
            save_detection(chosen, conf, t_str, inference_ms=round(random.uniform(11.0, 22.0), 1), actuated=(chosen != "Reject"), source="seed")
        log_event("INFO", "Sistem tohum verisi başarıyla yüklendi.")

seed_initial_data_if_empty()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Bağlantı kurulduğunda anlık güncel istatistikleri hemen istemciye yolla
        stats = get_stats()
        await websocket.send_text(json.dumps({"event": "init_stats", "data": stats}))
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text(json.dumps({"event": "pong", "time": time.time()}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.post("/api/detect")
async def detect_waste(data: WasteData):
    """
    Edge cihazından (Jetson/Raspberry Pi) gelen polimer atık verisini alır,
    SQLite veritabanına kaydeder ve tüm WebSocket istemcilerine canlı yayınlar.
    """
    rec_id = save_detection(
        waste_type=data.type,
        confidence=data.confidence,
        timestamp=data.timestamp,
        inference_ms=data.inference_ms or 0.0,
        actuated=data.actuated if data.actuated is not None else True,
        source=data.source or "edge-device"
    )

    payload = {
        "event": "detection",
        "id": rec_id,
        "type": data.type,
        "confidence": data.confidence,
        "timestamp": data.timestamp,
        "inference_ms": data.inference_ms,
        "actuated": data.actuated,
        "stats": get_stats()
    }
    await manager.broadcast(payload)
    return {"status": "success", "id": rec_id, "message": f"{data.type} atığı kaydedildi ve yayınlandı."}

@app.get("/api/stats")
async def api_get_stats():
    """Özet istatistikler, polimer sınıf dağılımı ve saatlik verim."""
    stats = get_stats()
    hourly = get_hourly_breakdown()
    return {
        "summary": stats,
        "hourly_breakdown": hourly,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/history")
async def api_get_history(limit: int = Query(default=50, le=500)):
    """Son atık tespitlerinin listesi."""
    return get_recent_detections(limit=limit)

@app.get("/api/config")
async def api_get_config():
    """Mevcut sistem parametrelerini döner."""
    return get_settings()

@app.post("/api/config")
async def api_update_config(config: ConfigUpdate):
    """Sistem parametrelerini günceller."""
    data = config.model_dump(exclude_none=True)
    for k, v in data.items():
        update_setting(k, str(v))
    log_event("CONFIG", f"Ayarlar güncellendi: {data}")
    await manager.broadcast({"event": "config_updated", "config": get_settings()})
    return {"status": "success", "updated": data}

@app.get("/api/environmental-impact")
async def api_environmental_impact():
    """Kurtarılan plastik kütlesi, engellenen CO2 salınımı ve tasarruf edilen enerji miktarı."""
    return get_environmental_impact()

@app.get("/api/logs")
async def api_system_logs(limit: int = Query(default=30, le=200)):
    """Sistem olay ve uyarı logları."""
    return get_system_logs(limit=limit)

@app.get("/api/system-status")
async def api_system_status():
    """Sistem donanım kaynaklarını ve çalışma süresini döner."""
    uptime_sec = int(time.time() - SERVER_START_TIME)
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "status": "healthy",
        "uptime_seconds": uptime_sec,
        "uptime_formatted": f"{uptime_sec // 3600}s {(uptime_sec % 3600) // 60}d {uptime_sec % 60}sn",
        "cpu_usage_pct": cpu_percent,
        "ram_usage_pct": mem.percent,
        "ram_available_mb": round(mem.available / (1024 * 1024), 1),
        "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
        "active_ws_clients": len(manager.active_connections)
    }

@app.get("/api/export/csv")
async def api_export_csv():
    """Tüm atık loglarını CSV formatında dışa aktarır."""
    csv_text = export_csv_content()
    filename = f"sifir_atik_rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/api/simulate")
async def api_simulate_detection(req: SimulationRequest):
    """Arayüz üzerinden test amaçlı simüle atık tespitleri tetikler."""
    import random
    types = ["PET", "HDPE", "Naylon", "PUR", "Metal", "Reject"]
    results = []
    for _ in range(req.count):
        waste_type = req.force_type if (req.force_type and req.force_type in types) else random.choice(types)
        confidence = round(random.uniform(84.0, 99.4), 1) if waste_type != "Reject" else round(random.uniform(45.0, 72.0), 1)
        t_str = datetime.now().strftime("%H:%M:%S")
        actuated = (waste_type != "Reject")
        rec_id = save_detection(
            waste_type=waste_type,
            confidence=confidence,
            timestamp=t_str,
            inference_ms=round(random.uniform(12.5, 24.0), 1),
            actuated=actuated,
            source="manual-simulation"
        )
        payload = {
            "event": "detection",
            "id": rec_id,
            "type": waste_type,
            "confidence": confidence,
            "timestamp": t_str,
            "inference_ms": 14.8,
            "actuated": actuated,
            "stats": get_stats()
        }
        await manager.broadcast(payload)
        results.append(payload)
    return {"status": "success", "generated": len(results), "items": results}

@app.post("/api/e-stop")
async def api_emergency_stop():
    """Acil Durdurma (E-STOP) tetikler."""
    update_setting("e_stop_active", "true")
    log_event("WARNING", "ACİL DURDURMA (E-STOP) TETİKLENDİ! Konveyör ve aktüatörler kilitlendi.")
    await manager.broadcast({"event": "emergency_stop", "message": "Konveyör ve valfler kilitlendi."})
    return {"status": "emergency_stop_activated", "timestamp": datetime.now().strftime("%H:%M:%S")}

@app.post("/api/e-stop/reset")
async def api_emergency_stop_reset():
    """Acil Durdurmayı resetler."""
    update_setting("e_stop_active", "false")
    log_event("INFO", "Acil Durdurma sıfırlandı, sistem normal çalışmaya döndü.")
    await manager.broadcast({"event": "emergency_stop_reset", "message": "Sistem normale döndü."})
    return {"status": "system_resumed", "timestamp": datetime.now().strftime("%H:%M:%S")}

# ----------------- CANLI KAMERA / BANT SİMÜLASYONU MJPEG STREAM -----------------
def generate_camera_frames():
    """
    OpenCV kullanarak canlı yapay zeka video akışı oluşturur.
    Kamera bağlıysa gerçek görüntüyü çeker; değilse gerçekçi bir
    bant akışı ve yapay zeka bounding box simülasyonu çizer.
    """
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(0)
    has_real_camera = cap.isOpened()
    
    # Sentetik animasyon için nesne koordinatları
    obj_x = 50
    obj_type = "PET [Şişe]"
    conf = 98.4

    colors = {
        "PET": (248, 189, 56),      # Cyan/Mavi (BGR)
        "HDPE": (11, 158, 245),     # Turuncu
        "Naylon": (200, 100, 255),  # Mor
        "PUR": (50, 220, 180),      # Turkuaz
        "Metal": (180, 180, 180),   # Gri
        "Reject": (50, 50, 239)     # Kırmızı
    }

    try:
        while True:
            if has_real_camera:
                success, frame = cap.read()
                if not success:
                    has_real_camera = False
                    continue
            else:
                # Gerçek kamera yoksa zengin bir konveyör bant görseli üret
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                # Arka plan konveyör bant şeritleri
                frame[120:360, :] = (45, 40, 35)
                # Bant kılavuz çizgileri
                cv2.line(frame, (0, 120), (640, 120), (100, 100, 100), 2)
                cv2.line(frame, (0, 360), (640, 360), (100, 100, 100), 2)
                
                # Bant hareket çizgileri
                stripe_offset = int((time.time() * 150) % 80)
                for x in range(-80 + stripe_offset, 640, 80):
                    cv2.line(frame, (x, 125), (x + 30, 355), (60, 55, 50), 2)

                # Nesne hareketi
                obj_x = int((time.time() * 120) % 600) + 20
                if obj_x < 30:
                    import random
                    cand = random.choice(["PET", "HDPE", "Naylon", "PUR", "Metal", "Reject"])
                    obj_type = cand
                    conf = round(random.uniform(88.0, 99.2), 1)

                base_type = obj_type.split()[0]
                box_color = colors.get(base_type, (0, 255, 0))
                
                # Nesne gövdesi ve Bounding Box
                cv2.rectangle(frame, (obj_x, 190), (obj_x + 90, 290), (30, 30, 30), -1)
                cv2.rectangle(frame, (obj_x, 190), (obj_x + 90, 290), box_color, 2)
                
                # Etiket ve Güven Skoru
                label = f"{obj_type} %{conf}"
                cv2.putText(frame, label, (obj_x - 10, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.55, box_color, 2)
                cv2.putText(frame, "AI INFERENCE: ACTIVE (30 FPS)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (16, 185, 129), 2)
                cv2.putText(frame, f"BANT HIZI: 0.35 m/s | ZAMAN: {datetime.now().strftime('%H:%M:%S')}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
                
                # Algılama Bölgesi (Detection Zone)
                cv2.rectangle(frame, (220, 130), (420, 350), (255, 255, 255), 1)
                cv2.putText(frame, "[ ALGI BOLGESI (ROI) ]", (240, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

            # JPEG formatına kodla
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.04) # ~25 FPS
    finally:
        if has_real_camera:
            cap.release()

@app.get("/video_feed")
def video_feed():
    """Canlı video MJPEG akış endpoint'i."""
    return StreamingResponse(
        generate_camera_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
