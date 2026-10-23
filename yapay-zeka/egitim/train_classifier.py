"""
Sıfır Atık YZ - Polimer Sınıflandırma Modeli Eğitimi ve Dışa Aktarma
PyTorch tabanlı PolymerEdgeNet modelini eğitir, değerlendirir ve
Edge cihazlarda koşturulmak üzere ONNX ve TorchScript formatlarına ihraç eder.
"""

import os
import sys
import time
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np

# Model mimarisini yükle
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "modeller"))
from model_arch import create_model, POLYMER_CLASSES


class SyntheticPolymerDataset(Dataset):
    """Gerçek veri toplanana kadar eğitim pipeline'ını ve ihracını doğrulamak için sentetik veri üretici."""
    def __init__(self, size: int = 300, num_classes: int = len(POLYMER_CLASSES)):
        self.size = size
        self.num_classes = num_classes
        # Her sınıf için belirgin renk / desen imzası üretir
        self.data = []
        self.labels = []
        for i in range(size):
            label = i % num_classes
            # Belirli polimer sınıfları için temsili renk tonları
            img = np.random.normal(loc=0.5, scale=0.15, size=(3, 224, 224)).astype(np.float32)
            if label == 0:    # PET (mavi/şeffaf)
                img[0] += 0.2
            elif label == 1:  # HDPE (sarı/opak)
                img[0] += 0.3; img[1] += 0.2
            elif label == 2:  # Naylon (mor)
                img[0] += 0.2; img[2] += 0.3
            elif label == 3:  # PUR (turkuaz)
                img[1] += 0.3; img[2] += 0.2
            elif label == 4:  # Metal (gri/parlak)
                img += 0.3
            img = np.clip(img, 0.0, 1.0)
            self.data.append(torch.tensor(img))
            self.labels.append(label)

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]


def train(epochs: int = 5, batch_size: int = 16, lr: float = 0.001, output_dir: str = "yapay-zeka/modeller"):
    os.makedirs(output_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Eğitim] Donanım: {device}")

    # Veri Kümesi
    dataset = SyntheticPolymerDataset(size=240)
    train_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Model, Kayıp Fonksiyonu ve Optimizer
    model = create_model().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    print("[Eğitim] Model eğitimi başlatılıyor...")
    start_t = time.time()
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

        epoch_loss = total_loss / total
        epoch_acc = (correct / total) * 100.0
        print(f"Epoch [{epoch+1}/{epochs}] - Kayıp: {epoch_loss:.4f} - Doğruluk: %{epoch_acc:.2f}")

    train_duration = round(time.time() - start_t, 2)
    print(f"[Eğitim] Tamamlandı! ({train_duration} saniye)")

    # 1. PyTorch Ağırlıkları (.pt) Kaydet
    pt_path = os.path.join(output_dir, "polymer_model.pt")
    torch.save(model.state_dict(), pt_path)
    print(f"[Kayıt] PyTorch ağırlıkları kaydedildi: {pt_path}")

    # 2. TorchScript Formatına İhraç Et (.pt)
    model.eval().to("cpu")
    dummy_input = torch.randn(1, 3, 224, 224)
    scripted_model = torch.jit.trace(model, dummy_input)
    script_path = os.path.join(output_dir, "polymer_model_scripted.pt")
    scripted_model.save(script_path)
    print(f"[Kayıt] TorchScript optimize model ihraç edildi: {script_path}")

    # 3. ONNX Formatına İhraç Et (.onnx)
    try:
        onnx_path = os.path.join(output_dir, "polymer_model.onnx")
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=['input_image'],
            output_names=['class_probabilities'],
            dynamic_axes={'input_image': {0: 'batch_size'}, 'class_probabilities': {0: 'batch_size'}}
        )
        print(f"[Kayıt] ONNX modeli ihraç edildi: {onnx_path}")
    except Exception as e:
        print(f"[ONNX Hatası] {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sıfır Atık Polimer Sınıflandırıcı Eğitimi")
    parser.add_argument("--epochs", type=int, default=3, help="Epoch sayısı")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch boyutu")
    parser.add_argument("--lr", type=float, default=0.001, help="Öğrenme oranı")
    args = parser.parse_args()

    train(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
