"""
Sıfır Atık YZ - Edge AI Model Benchmark ve Performans Test Aracı
TorchScript modelinin veya PyTorch modelinin gecikme (latency),
FPS (saniyedeki kare sayısı), P95/P99 süreleri ve bellek kullanımını ölçer.
"""

import os
import sys
import time
import torch
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), "modeller"))
from model_arch import create_model, POLYMER_CLASSES

def benchmark_model(model_path: str = "yapay-zeka/modeller/polymer_model_scripted.pt", iterations: int = 100):
    print("=" * 60)
    print("Sıfır Atık YZ - Model Çıkarım Benchmark Testi")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Test Donanımı: {device}")

    if os.path.exists(model_path):
        print(f"Yüklenen Model: {model_path} (TorchScript JIT)")
        model = torch.jit.load(model_path, map_location=device)
    else:
        print("Kayıtlı TorchScript modeli bulunamadı, dinamik mimari oluşturuluyor...")
        model = create_model().to(device)

    model.eval()

    # Isınma (Warmup)
    dummy_input = torch.randn(1, 3, 224, 224, device=device)
    for _ in range(15):
        with torch.no_grad():
            _ = model(dummy_input)

    # Benchmark Döngüsü
    latencies = []
    print(f"\n{iterations} adet çıkarım döngüsü koşturuluyor...")
    for i in range(iterations):
        t0 = time.perf_counter()
        with torch.no_grad():
            output = model(dummy_input)
            probs = torch.softmax(output, dim=1)
            pred_idx = torch.argmax(probs, dim=1).item()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0) # milisaniye

    latencies = np.array(latencies)
    avg_lat = np.mean(latencies)
    median_lat = np.median(latencies)
    p95_lat = np.percentile(latencies, 95)
    p99_lat = np.percentile(latencies, 99)
    min_lat = np.min(latencies)
    max_lat = np.max(latencies)
    fps = 1000.0 / avg_lat

    print("\n" + "-" * 40)
    print("[SONUC] BENCHMARK SONUCLARI:")
    print("-" * 40)
    print(f"Ortalama Gecikme (Latency): {avg_lat:.2f} ms")
    print(f"Medyan Gecikme:            {median_lat:.2f} ms")
    print(f"P95 Gecikme:               {p95_lat:.2f} ms")
    print(f"P99 Gecikme:               {p99_lat:.2f} ms")
    print(f"Min / Max:                 {min_lat:.2f} ms / {max_lat:.2f} ms")
    print(f"Teorik Cikarim Hizi (FPS): {fps:.1f} FPS")
    print("-" * 40)

    if avg_lat < 30:
        print("[OK] Mukemmel: Model konveyor bantta yuksek hizli gercek zamanli ayiklama icin fazlasiyla uygundur.")
    elif avg_lat < 70:
        print("[UYARI] Kabul Edilebilir: Standart bant hizlarinda (0.3 - 0.5 m/s) sorunsuz calisir.")
    else:
        print("[DIKKAT] Daha fazla quantizasyon (INT8) veya model budama tavsiye edilir.")

if __name__ == "__main__":
    benchmark_model()
