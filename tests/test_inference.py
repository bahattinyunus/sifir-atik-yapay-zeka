import sys
import os
import torch
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "yapay-zeka", "modeller"))
from model_arch import create_model, POLYMER_CLASSES

def test_polymer_edge_net_architecture():
    model = create_model()
    model.eval()

    dummy_tensor = torch.randn(2, 3, 224, 224)
    with torch.no_grad():
        out = model(dummy_tensor)

    assert out.shape == (2, len(POLYMER_CLASSES))
    assert len(POLYMER_CLASSES) == 6
    assert "PET" in POLYMER_CLASSES
    assert "HDPE" in POLYMER_CLASSES
    assert "Naylon" in POLYMER_CLASSES
    assert "PUR" in POLYMER_CLASSES
