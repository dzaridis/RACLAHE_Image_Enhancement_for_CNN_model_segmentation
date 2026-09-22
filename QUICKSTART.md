# RACLAHE Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- Medical imaging files (DICOM `.dcm` or NIfTI `.nii`/`.nii.gz`)

## Step 1: Prepare Your Data

Organize your medical images in folders:

```
input/
├── patient001/
│   ├── slice001.dcm
│   ├── slice002.dcm
│   └── ...
├── patient002/
│   └── scan.nii.gz
└── ...
```

Each patient folder should contain either:
- Multiple DICOM files (one per slice), OR
- A single NIfTI file

## Step 2: Run with Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd RACLAHE_Image_Enhancement_for_CNN_model_segmentation

# Create directories
mkdir -p input output shared

# Copy your patient data into input/
cp -r /path/to/your/patients/* input/

# Run processing
docker-compose up --build
```

## Step 3: Get Results

Enhanced images will be saved in:
```
output/RACLAHE OUTPUT/
├── patient001/
│   ├── image_1.dcm
│   ├── image_2.dcm
│   └── ...
└── patient002/
    └── patient002.nii.gz
```

---

## Alternative: Run with Docker (without Compose)

```bash
# Build image (run `git lfs pull` first to fetch bbox_weights/)
docker build -t raclahe:3.0 .

# Run with volumes
docker run \
  -v $(pwd)/input:/home/ds/datasets:ro \
  -v $(pwd)/output:/home/ds/persistent-home \
  raclahe:3.0 /home/ds/datasets /home/ds/persistent-home/output
```

---

## EUCAIM Platform

On EUCAIM, volumes are automatically mounted:
- `/home/ds/datasets` → Your input data (read-only)
- `/home/ds/persistent-home` → Your output directory
- `/home/ds/persistent-shared-folder` → Shared storage

Submit the job with `jobman`, passing the input and output directories after
the `--` separator:

```bash
jobman submit -i raclahe -- <INPUT_DIR> <OUTPUT_DIR>
```

```bash
jobman submit -i raclahe -- ~/datasets/87f3be56-4725-45c3-9baa-d338de530f73/ ~/persistent-home/results/
```

Pick an `OUTPUT_DIR` under `persistent-home`, otherwise the results are lost
when the job ends. If both arguments are omitted, the tool falls back to
`/home/ds/datasets` and `/home/ds/persistent-home/output`.

---

## Configuration

| Argument | Description | Default |
| --- | --- | --- |
| `INPUT_DIR` (1st positional) | Dataset directory, one sub-directory per patient | `/home/ds/datasets` |
| `OUTPUT_DIR` (2nd positional) | Where the enhanced images are written | `/home/ds/persistent-home/output` |
| `--weights` | Bounding-box U-Net weights (`.h5`) | `/home/ds/bbox_weights/checkpoint_external.h5` |

The environment variables `INPUT_DIR`, `OUTPUT_DIR` and `WEIGHTS_PATH` are
still honoured as fallbacks; command-line arguments take precedence.

```bash
docker run \
  -v $(pwd)/input:/custom/input:ro \
  -v $(pwd)/output:/custom/output \
  raclahe:3.0 /custom/input /custom/output
```

---

## Troubleshooting

### No output generated
- Check that input folders contain valid DICOM or NIfTI files
- Look at logs: `docker-compose logs`

### Permission errors
- Ensure input/output directories are writable
- Container runs as user 1000:1000

### Processing fails
- Check file format (only `.dcm`, `.nii`, `.nii.gz` supported)
- Verify each patient folder contains only one type (DICOM or NIfTI)
- Review logs for specific error messages

---

## Support

For issues or questions:
- Review the main [README.md](README.md)
- Contact: dimzaridis@gmail.com
- Paper: https://doi.org/10.1038/s41598-023-27671-8

