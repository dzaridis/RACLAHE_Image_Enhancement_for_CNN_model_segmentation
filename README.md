# RACLAHE: Region Adaptive MR Image Enhancement for CNN-based Segmentation

RACLAHE (Region-Adaptive Contrast Limited Adaptive Histogram Equalization) is an image enhancement method specifically designed for improving CNN-based segmentation of the prostate and prostatic zones in T2-Weighted MR images.

This repository supports the original publication in Nature's Scientific Reports: *"Region-Adaptive Magnetic Resonance Image Enhancement for improving CNN-based segmentation of the prostate and prostatic zones"* [doi:10.1038/s41598-023-27671-8](https://doi.org/10.1038/s41598-023-27671-8)

---

## 🚀 Quick Start

📖 **See [QUICKSTART.md](QUICKSTART.md) for detailed step-by-step instructions**

```bash
# 1. Prepare your data
mkdir -p input output shared
cp -r /path/to/your/patients/* input/

# 2. Run processing
docker-compose up --build

# 3. Get results from output/RACLAHE OUTPUT/
```

---

## 📋 Requirements

- Docker and Docker Compose
- Medical images in DICOM (`.dcm`) or NIfTI (`.nii`, `.nii.gz`) format

---

## 📁 Input Data Format

Organize your data with one folder per patient:

### DICOM Series
```
input/
├── patient001/
│   ├── slice001.dcm
│   ├── slice002.dcm
│   └── ...
└── patient002/
    ├── slice001.dcm
    └── ...
```

### NIfTI Files
```
input/
├── patient001/
│   └── scan.nii.gz
└── patient002/
    └── scan.nii.gz
```

---

## 📤 Output Format

Enhanced images are saved in the same format as input:

```
output/RACLAHE OUTPUT/
├── patient001/
│   ├── image_1.dcm      (if DICOM input)
│   ├── image_2.dcm
│   └── ...
└── patient002/
    └── patient002.nii.gz (if NIfTI input)
```

---

## 🔧 Usage

### With Docker Compose (Recommended)

```bash
docker-compose up --build
```

### With Docker

```bash
# Build
docker build -t raclage:3.0 .

# Run
docker run \
  -v $(pwd)/input:/home/ds/datasets:ro \
  -v $(pwd)/output:/home/ds/persistent-home \
  raclage:3.0
```

### Custom Paths

The entrypoint accepts two optional positional arguments, `INPUT_DIR` and
`OUTPUT_DIR`:

```
raclahe [INPUT_DIR] [OUTPUT_DIR] [--weights WEIGHTS_PATH]
```

| Argument | Description | Default |
| --- | --- | --- |
| `INPUT_DIR` | Dataset directory, one sub-directory per patient | `/home/ds/datasets` |
| `OUTPUT_DIR` | Where the enhanced images are written | `/home/ds/persistent-home/output` |
| `--weights` | Bounding-box U-Net weights (`.h5`) | `/home/ds/bbox_weights/checkpoint_external.h5` |

```bash
docker run \
  -v /your/input:/custom/input:ro \
  -v /your/output:/custom/output \
  raclahe:3.0 /custom/input /custom/output
```

The equivalent environment variables `INPUT_DIR`, `OUTPUT_DIR` and
`WEIGHTS_PATH` are still honoured; command-line arguments take precedence.

### On the EUCAIM platform

```bash
jobman submit -i raclahe -- <INPUT_DIR> <OUTPUT_DIR>
```

```bash
jobman submit -i raclahe -- ~/datasets/87f3be56-4725-45c3-9baa-d338de530f73/ ~/persistent-home/results/
```

`OUTPUT_DIR` should be a path under `persistent-home`, which is shared between
all desktops and jobs of the user; otherwise the results are lost when the job
ends.

---

## ✅ EUCAIM Platform Compliance

This image is fully EUCAIM-compliant:

- ✅ Runs as non-root user `ds` (uid 1000, gid 1000)
- ✅ Uses standard EUCAIM volume mount points:
  - `/home/ds/datasets` - Input datasets (read-only)
  - `/home/ds/persistent-home` - Output storage
  - `/home/ds/persistent-shared-folder` - Shared storage
- ✅ No internet access required at runtime
- ✅ Batch processing optimized for medical imaging workflows

---

## 🧬 Algorithm Overview

RACLAHE enhances medical images by:

1. **Detecting** the prostate region using a pre-trained U-Net model
2. **Applying** adaptive histogram equalization to the detected region
3. **Preserving** original characteristics in non-prostatic regions
4. **Combining** enhanced and unenhanced regions for the final output

This targeted approach improves CNN segmentation performance by 3-9% (Dice score) across different prostatic regions.

---

## 📊 Citation

If you use RACLAHE in your research, please cite:

```bibtex
@article{zaridis2023region,
  title={Region-adaptive magnetic resonance image enhancement for improving CNN-based segmentation of the prostate and prostatic zones},
  author={Zaridis, Dimitrios I and Mylona, Eugenia and Tachos, Nikolaos and Pezoulas, Vasileios C and Grigoriadis, Grigorios and Tsiknakis, Nikos and Marias, Kostas and Tsiknakis, Manolis and Fotiadis, Dimitrios I},
  journal={Scientific Reports},
  volume={13},
  number={1},
  pages={714},
  year={2023},
  publisher={Nature Publishing Group UK London}
}
```

---

## 🆘 Support

For questions or issues:
- 📖 Read the [QUICKSTART.md](QUICKSTART.md) guide
- 📧 Contact: dimzaridis@gmail.com
- 📄 Paper: https://doi.org/10.1038/s41598-023-27671-8

---

## 📜 License

[![EUPL-1.2 License](https://img.shields.io/badge/License-EUPL--1.2-blue.svg)](https://eupl.eu/1.2/en/)

Licensed under the European Union Public Licence (EUPL) v1.2 - see [LICENSE](LICENSE) and [NOTICE](NOTICE).

---

## 🙏 Acknowledgements

This work is supported by the ProCancer-I project, funded by the European Union's Horizon 2020 research and innovation program under grant agreement No 952159.
