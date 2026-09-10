# Real Satellite Tropical Cyclone Dataset (NASA IMPACT)

## Dataset Overview

- **Source**: NASA IMPACT Tropical Cyclone Wind Estimation Dataset (v1.0)
- **Satellite Sensor**: NOAA Geostationary Operational Environmental Satellites (GOES) Clean IR (10.7 µm)
- **License**: Creative Commons Attribution 4.0 International (CC-BY-4.0)
- **DOI**: [10.34911/rdnt.xs53up](https://doi.org/10.34911/rdnt.xs53up) / [IEEE JSTARS 10.1109/JSTARS.2020.3011907](http://doi.org/10.1109/JSTARS.2020.3011907)

## Structure & Leakage-Free Splits

Images are partitioned by **storm identity** so that no storm appears in multiple splits:

```
data/processed/satellite/
├── catalog.json                # Complete metadata for every image
├── provenance.yaml             # Official provenance and metrics
└── images/
    ├── train/
    │   ├── cyclone/            # Cyclone / Tropical Storm images
    │   └── non_cyclone/        # Depression / Ambient images
    ├── validation/
    │   ├── cyclone/
    │   └── non_cyclone/
    └── test/
        ├── cyclone/
        └── non_cyclone/
```

## ML ResNet Usage Guide (PyTorch)

```python
import torchvision.transforms as T
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader

transform = T.Compose([
    T.Resize((224, 224)),
    T.Grayscale(num_output_channels=3), # Replicate to 3 channels for pretrained ResNet
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

train_ds = ImageFolder('data/processed/satellite/images/train', transform=transform)
val_ds = ImageFolder('data/processed/satellite/images/validation', transform=transform)
test_ds = ImageFolder('data/processed/satellite/images/test', transform=transform)

train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
```
