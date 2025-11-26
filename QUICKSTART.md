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
# Build image
docker build -t raclahe:3.0 .

# Run with volumes
docker run \
  -v $(pwd)/input:/home/ds/datasets:ro \
  -v $(pwd)/output:/home/ds/persistent-home \
  raclahe:3.0
```

---

## EUCAIM Platform

On EUCAIM, volumes are automatically mounted:
- `/home/ds/datasets` → Your input data (read-only)
- `/home/ds/persistent-home` → Your output directory
- `/home/ds/persistent-shared-folder` → Shared storage

Simply deploy the image and it will process all patients in the datasets directory.

---

## Configuration

Override paths using environment variables:

```bash
docker run \
  -e INPUT_DIR=/custom/input \
  -e OUTPUT_DIR=/custom/output \
  -v $(pwd)/input:/custom/input:ro \
  -v $(pwd)/output:/custom/output \
  raclage:3.0
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

