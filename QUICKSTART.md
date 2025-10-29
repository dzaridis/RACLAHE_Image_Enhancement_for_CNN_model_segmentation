# RACLAHE Quick Start Guide

Get started with RACLAHE in minutes!

## Prerequisites

- Docker and Docker Compose installed
- Medical imaging files (DICOM or NIfTI format)

## REST API Mode

### Step 1: Start the API

```bash
# Clone and navigate to the repository
git clone <repository-url>
cd RACLAHE_Image_Enhancement_for_CNN_model_segmentation

# Start the API server
docker-compose up --build
```

Wait for the message: `Uvicorn running on http://0.0.0.0:8000`

### Step 2: Test the API

Open a new terminal and test:

```bash
# Quick health check
curl http://localhost:8000/health

# Or run the test script
python test_api.py
```

### Step 3: Process Your Images

#### Using cURL (Command Line)

**For NIfTI files:**
```bash
curl -X POST http://localhost:8000/process \
  -F "files=@/path/to/your/image.nii.gz" \
  --output enhanced.zip
```

**For DICOM series:**
```bash
curl -X POST http://localhost:8000/process \
  -F "files=@/path/to/dicom/slice001.dcm" \
  -F "files=@/path/to/dicom/slice002.dcm" \
  -F "files=@/path/to/dicom/slice003.dcm" \
  --output enhanced.zip
```

#### Using Python

```python
import requests
from pathlib import Path

# Process a NIfTI file
with open('image.nii.gz', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/process',
        files=[('files', ('image.nii.gz', f))]
    )

# Save the result
with open('enhanced.zip', 'wb') as f:
    f.write(response.content)

print("✓ Processing complete!")
```

#### Using the Interactive Docs

1. Open http://localhost:8000/docs in your browser
2. Click on `/process` endpoint
3. Click "Try it out"
4. Upload your files
5. Click "Execute"
6. Download the result

### Step 4: Extract Results

```bash
unzip enhanced.zip
```

Your enhanced images are ready!

---

## Common Commands

```bash
# Start API
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop API
docker-compose down

# Rebuild and start
docker-compose up --build
```

---

## Troubleshooting

### API won't start

```bash
# Check if port 8000 is already in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use a different port
API_PORT=8080 docker-compose up raclahe-api
```

### "Cannot connect to Docker daemon"

Make sure Docker is running:
```bash
docker ps
```

### Upload fails

Check file size - default limit is 500MB:
```bash
# Increase limit to 1GB
MAX_UPLOAD_SIZE=1073741824 docker-compose up raclahe-api
```

### Processing fails

Check logs:
```bash
docker-compose logs raclahe-api
```

Common issues:
- Invalid file format (only .dcm, .nii, .nii.gz supported)
- Corrupted files
- Mixed DICOM and NIfTI files in one request

---

## Next Steps

- 📖 Read [API_USAGE.md](API_USAGE.md) for detailed examples
- 📖 Read [DOCKER_USAGE.md](DOCKER_USAGE.md) for Docker configuration
- 🌐 Explore the interactive API docs at http://localhost:8000/docs
- 📊 Check out the paper: https://doi.org/10.1038/s41598-023-27671-8

---

## Quick Reference

| Endpoint | Purpose |
|----------|---------|
| http://localhost:8000/ | API root |
| http://localhost:8000/docs | Interactive API documentation |
| http://localhost:8000/health | Health check |
| http://localhost:8000/info | API information |
| http://localhost:8000/process | Process images (POST) |

---

## Next Steps

- 📖 Read [API_USAGE.md](API_USAGE.md) for detailed Python examples
- 🌐 Explore the interactive docs at http://localhost:8000/docs
- 📊 Check out the paper: https://doi.org/10.1038/s41598-023-27671-8

## Support

For help:
- Check the logs: `docker-compose logs`
- Read the full documentation in [API_USAGE.md](API_USAGE.md)
- Contact: dimzaridis@gmail.com

