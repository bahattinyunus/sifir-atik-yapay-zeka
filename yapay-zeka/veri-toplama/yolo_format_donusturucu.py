"""
Sıfır Atık YZ - YOLO Veri Seti Format Dönüştürücü ve Bölücü
Toplanan ham polimer fotoğraflarını YOLOv8/YOLOv9 formatına dönüştürür.
Train (%80) ve Validation (%20) klasörlerini otomatik oluşturur, etiketler yazar.
"""

import os
import shutil
import random
import argparse
from typing import List

CLASS_MAP = {
    "PET": 0,
    "HDPE": 1,
    "Naylon": 2,
    "PUR": 3,
    "Metal": 4,
    "Reject": 5
}

def convert_dataset(input_dir: str = "dataset", output_dir: str = "dataset_yolo", split_ratio: float = 0.8):
    print("=" * 60)
    print("Sıfır Atık YZ - YOLO Format Dönüştürücü")
    print(f"Girdi: {input_dir} -> Çıktı: {output_dir}")
    print("=" * 60)

    train_img_dir = os.path.join(output_dir, "images", "train")
    val_img_dir = os.path.join(output_dir, "images", "val")
    train_lbl_dir = os.path.join(output_dir, "labels", "train")
    val_lbl_dir = os.path.join(output_dir, "labels", "val")

    for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        os.makedirs(d, exist_ok=True)

    total_images = 0
    for class_name, class_id in CLASS_MAP.items():
        src_folder = os.path.join(input_dir, class_name)
        if not os.path.exists(src_folder):
            continue

        files = [f for f in os.listdir(src_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        random.shuffle(files)
        total_images += len(files)

        split_idx = int(len(files) * split_ratio)
        train_files = files[:split_idx]
        val_files = files[split_idx:]

        for subset, flist in [("train", train_files), ("val", val_files)]:
            target_img_dir = train_img_dir if subset == "train" else val_img_dir
            target_lbl_dir = train_lbl_dir if subset == "train" else val_lbl_dir

            for fname in flist:
                src_path = os.path.join(src_folder, fname)
                base_name = os.path.splitext(fname)[0]
                dst_img_path = os.path.join(target_img_dir, fname)
                dst_lbl_path = os.path.join(target_lbl_dir, f"{base_name}.txt")

                shutil.copy2(src_path, dst_img_path)
                # Standart merkezlenmiş YOLO BBox: <class> <x_center> <y_center> <width> <height>
                with open(dst_lbl_path, "w", encoding="utf-8") as f:
                    f.write(f"{class_id} 0.500000 0.500000 0.700000 0.700000\n")

        print(f"[{class_name}] {len(train_files)} eğitim, {len(val_files)} doğrulama görüntüsü aktarıldı.")

    print(f"\n[Sonuç] Toplam {total_images} görüntü YOLO formatına dönüştürüldü.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Veri kümesini YOLO formatına dönüştür")
    parser.add_argument("--input", default="dataset", help="Girdi veri klasörü")
    parser.add_argument("--output", default="dataset_yolo", help="YOLO çıktı klasörü")
    parser.add_argument("--split", type=float, default=0.8, help="Eğitim oranı")
    args = parser.parse_args()

    convert_dataset(input_dir=args.input, output_dir=args.output, split_ratio=args.split)
