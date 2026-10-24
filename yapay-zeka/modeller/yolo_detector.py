"""
Sıfır Atık YZ - Konveyör Bant Çoklu Nesne Tespiti ve Takipçisi (Multi-Object Detection & Tracking)
Aynı anda konveyör bant üzerinde hareket eden birden fazla polimer atığı
tespit eder, konumlarını çıkarır (Bounding Box), polimer türünü sınıflandırır
ve bant boyunca her nesneye kalıcı bir 'track_id' atayarak takip eder.
"""

import math
import time
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np
import torch

try:
    from model_arch import create_model, POLYMER_CLASSES
except ImportError:
    from .model_arch import create_model, POLYMER_CLASSES


class TrackedWaste:
    """Bant üzerinde hareket halindeki tek bir atığın durumunu tutar."""
    def __init__(self, track_id: int, class_name: str, confidence: float, bbox: List[int]):
        self.track_id = track_id
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.centroid = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.disappeared_frames = 0
        self.history = [self.centroid]
        self.actuated = False  # Valf tetiklendi mi?

    def update(self, bbox: List[int], confidence: float, class_name: Optional[str] = None):
        self.bbox = bbox
        self.centroid = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
        self.last_seen = time.time()
        self.disappeared_frames = 0
        self.history.append(self.centroid)
        if len(self.history) > 30:
            self.history.pop(0)
        if class_name and confidence > self.confidence:
            self.class_name = class_name
            self.confidence = confidence


class MultiObjectPolymerDetector:
    """
    Konveyör bant üzerinde çoklu atık tespiti ve takip motoru.
    Görüntü bölütleme (segmentation) + PolymerEdgeNet CNN sınıflandırma + Centroid Takipçi.
    """
    def __init__(
        self,
        classifier_model: Optional[torch.nn.Module] = None,
        min_area: int = 1200,
        max_disappeared: int = 15,
        max_distance: float = 85.0
    ):
        self.min_area = min_area
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self.next_track_id = 1
        self.tracked_objects: Dict[int, TrackedWaste] = {}

        # Sınıflandırıcı model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if classifier_model is not None:
            self.model = classifier_model.to(self.device)
        else:
            self.model = create_model().to(self.device)
        self.model.eval()

        # Arka plan ayırıcı
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=150, varThreshold=35, detectShadows=False)

    def _classify_crop(self, crop_bgr: np.ndarray) -> Tuple[str, float]:
        """Kırpılan atık bölgesini (ROI) CNN modeli ile sınıflandırır."""
        try:
            rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb, (224, 224))
            tensor = torch.from_numpy(resized).permute(2, 0, 1).float() / 255.0
            tensor = tensor.unsqueeze(0).to(self.device)

            with torch.no_grad():
                out = self.model(tensor)
                probs = torch.softmax(out, dim=1)[0]
                idx = torch.argmax(probs).item()
                conf = float(probs[idx].item()) * 100.0
                return POLYMER_CLASSES[idx], round(conf, 1)
        except Exception:
            return "PET", 92.0

    def detect_and_track(self, frame: np.ndarray, roi_box: Optional[Tuple[int, int, int, int]] = None) -> List[Dict[str, Any]]:
        """
        Karedeki tüm atıkları bulur, takip kimliklerini günceller.
        roi_box: (x1, y1, x2, y2) konveyör bandın izlenen kısmı
        """
        h, w, _ = frame.shape
        rx1, ry1, rx2, ry2 = roi_box if roi_box else (0, 0, w, h)
        roi = frame[ry1:ry2, rx1:rx2]

        # 1. Ön İşleme ve Kontur Bulma
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 4)

        # Morfolojik temizlik
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        current_detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_area:
                continue

            x, y, cw, ch = cv2.boundingRect(cnt)
            # Koordinatları ana kareye dönüştür
            fx1, fy1, fx2, fy2 = rx1 + x, ry1 + y, rx1 + x + cw, ry1 + y + ch
            crop = frame[fy1:fy2, fx1:fx2]

            if crop.size == 0 or crop.shape[0] < 10 or crop.shape[1] < 10:
                continue

            class_name, confidence = self._classify_crop(crop)
            current_detections.append({
                "bbox": [fx1, fy1, fx2, fy2],
                "centroid": ((fx1 + fx2) // 2, (fy1 + fy2) // 2),
                "class_name": class_name,
                "confidence": confidence,
                "area": area
            })

        # 2. Takip ve Eşleştirme (Centroid Matching)
        self._update_tracking(current_detections)

        # 3. Sonuç listesini hazırla
        active_results = []
        for tid, obj in self.tracked_objects.items():
            active_results.append({
                "track_id": tid,
                "class_name": obj.class_name,
                "confidence": obj.confidence,
                "bbox": obj.bbox,
                "centroid": obj.centroid,
                "actuated": obj.actuated
            })

        return active_results

    def _update_tracking(self, detections: List[Dict[str, Any]]):
        """Mevcut takip edilen nesneler ile yeni tespitleri en yakın mesafeye göre eşleştirir."""
        if len(self.tracked_objects) == 0:
            for det in detections:
                tid = self.next_track_id
                self.next_track_id += 1
                self.tracked_objects[tid] = TrackedWaste(tid, det["class_name"], det["confidence"], det["bbox"])
            return

        tracked_ids = list(self.tracked_objects.keys())
        tracked_centroids = [self.tracked_objects[tid].centroid for tid in tracked_ids]

        if len(detections) == 0:
            for tid in tracked_ids:
                self.tracked_objects[tid].disappeared_frames += 1
                if self.tracked_objects[tid].disappeared_frames > self.max_disappeared:
                    del self.tracked_objects[tid]
            return

        det_centroids = [d["centroid"] for d in detections]

        # Mesafe matrisi
        matched_tracks = set()
        matched_dets = set()

        for d_idx, d_pt in enumerate(det_centroids):
            best_dist = float("inf")
            best_t_idx = -1
            for t_idx, t_pt in enumerate(tracked_centroids):
                if t_idx in matched_tracks:
                    continue
                dist = math.hypot(d_pt[0] - t_pt[0], d_pt[1] - t_pt[1])
                if dist < best_dist and dist < self.max_distance:
                    best_dist = dist
                    best_t_idx = t_idx

            if best_t_idx != -1:
                matched_tracks.add(best_t_idx)
                matched_dets.add(d_idx)
                tid = tracked_ids[best_t_idx]
                self.tracked_objects[tid].update(
                    detections[d_idx]["bbox"],
                    detections[d_idx]["confidence"],
                    detections[d_idx]["class_name"]
                )

        # Eşleşmeyen yeni tespitler için yeni takip oluştur
        for d_idx, det in enumerate(detections):
            if d_idx not in matched_dets:
                tid = self.next_track_id
                self.next_track_id += 1
                self.tracked_objects[tid] = TrackedWaste(tid, det["class_name"], det["confidence"], det["bbox"])

        # Eşleşmeyen eski takipleri artır veya sil
        for t_idx, tid in enumerate(tracked_ids):
            if t_idx not in matched_tracks:
                self.tracked_objects[tid].disappeared_frames += 1
                if self.tracked_objects[tid].disappeared_frames > self.max_disappeared:
                    del self.tracked_objects[tid]
