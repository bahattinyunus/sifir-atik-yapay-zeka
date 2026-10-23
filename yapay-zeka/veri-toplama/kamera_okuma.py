"""
Sıfır Atık YZ - Gelişmiş Veri Toplama ve Otonom Etiketleme Aracı
Kameradan veya konveyör bant akışından görüntüleri sınıf klasörlerine göre kaydeder.
Özellikler:
- Sınıf seçimi (1: PET, 2: HDPE, 3: Naylon, 4: PUR, 5: Metal, 6: Reject)
- ROI (Algılama Alanı / Region of Interest) Kılavuz Çerçevesi
- Hareket Algılama (Background Subtractor MOG2) ile Otonom Tetikleme modu (--auto)
"""

import os
import sys
import time
import argparse
import cv2

CLASS_MAP = {
    ord('1'): "PET",
    ord('2'): "HDPE",
    ord('3'): "Naylon",
    ord('4'): "PUR",
    ord('5'): "Metal",
    ord('6'): "Reject"
}

def main():
    parser = argparse.ArgumentParser(description="Polimer Veri Toplama Aracı")
    parser.add_argument("--camera-id", type=int, default=0, help="Kamera aygıt indeksi")
    parser.add_argument("--output-dir", type=str, default="dataset", help="Veri kümesi ana dizini")
    parser.add_argument("--auto", action="store_true", help="Hareket algılandığında otomatik kaydet")
    args = parser.parse_args()

    print("=" * 60)
    print("Sıfır Atık YZ - Akıllı Veri Toplama Aracı")
    print("Tus Kontrolleri:")
    print("  [1] PET   | [2] HDPE  | [3] Naylon")
    print("  [4] PUR   | [5] Metal | [6] Reject")
    print("  [Space] Aktif secili siniftan fotograf kaydet")
    print("  [q] Cikis")
    print("=" * 60)

    # Klasörleri hazırla
    for name in ["PET", "HDPE", "Naylon", "PUR", "Metal", "Reject"]:
        os.makedirs(os.path.join(args.output_dir, name), exist_ok=True)

    cap = cv2.VideoCapture(args.camera_id)
    if not cap.isOpened():
        print(f"[Hata] Kamera (ID: {args.camera_id}) acilamadi.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    current_class = "PET"
    saved_count = 0
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=50, detectShadows=False)
    last_auto_save = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Hata] Goruntu alinamadi.")
            break

        h, w, _ = frame.shape
        # ROI Koordinatları (Ekranın ortasındaki 400x400 bant alanı)
        rx1, ry1 = int(w * 0.25), int(h * 0.20)
        rx2, ry2 = int(w * 0.75), int(h * 0.80)
        roi = frame[ry1:ry2, rx1:rx2]

        display_frame = frame.copy()
        cv2.rectangle(display_frame, (rx1, ry1), (rx2, ry2), (0, 255, 0), 2)
        cv2.putText(display_frame, f"AKTIF SINIF: {current_class}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        cv2.putText(display_frame, f"KAYDEDILEN: {saved_count}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        cv2.putText(display_frame, "[1:PET 2:HDPE 3:Naylon 4:PUR 5:Metal 6:Reject] [BOSLUK: Kaydet]", (30, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Otonom Hareket Tespiti
        if args.auto:
            fg_mask = bg_subtractor.apply(roi)
            motion_pixels = cv2.countNonZero(fg_mask)
            if motion_pixels > 8000 and (time.time() - last_auto_save) > 1.5:
                # Banttan yeni bir atık geçiyor, otonom kaydet
                filename = os.path.join(args.output_dir, current_class, f"{current_class}_{int(time.time()*1000)}.jpg")
                cv2.imwrite(filename, roi)
                saved_count += 1
                last_auto_save = time.time()
                print(f"[Oto-Kayit] {filename} (Hareket: {motion_pixels} px)")

        cv2.imshow("Sifir Atik YZ - Veri Toplama", display_frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key in CLASS_MAP:
            current_class = CLASS_MAP[key]
            print(f"[Secim] Aktif sinif degistirildi: {current_class}")
        elif key == 32: # Boşluk tuşu (Manuel Kaydet)
            filename = os.path.join(args.output_dir, current_class, f"{current_class}_{int(time.time()*1000)}.jpg")
            cv2.imwrite(filename, roi)
            saved_count += 1
            print(f"[Manuel Kayit] {filename}")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nVeri toplama tamamlandi. Toplam {saved_count} goruntu kaydedildi.")

if __name__ == "__main__":
    main()
