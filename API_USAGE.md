# RACLAHE API Usage Guide

This guide explains how to use the RACLAHE FastAPI REST API for processing medical images.

## Quick Start

### 1. Start the API Server

```bash
# Using Docker Compose (Recommended)
docker-compose up raclahe-api

# Or build and run specifically
docker-compose -f docker-compose.api.yml up --build

# The API will be available at: http://localhost:8000
```

### 2. Access API Documentation

Open your browser and navigate to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check

Check if the API is running and the model is loaded:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-29T12:00:00",
  "weights_available": true
}
```

### Get API Information

```bash
curl http://localhost:8000/info
```

Response:
```json
{
  "api_version": "3.0",
  "model": "RACLAHE",
  "model_description": "Region-Adaptive Contrast Limited Adaptive Histogram Equalization",
  "supported_formats": ["DICOM (.dcm)", "NIfTI (.nii, .nii.gz)"],
  "max_upload_size_mb": 500,
  "weights_path": "/home/ds/BBOX_WEIGHTS/WHOLE GLAND/checkpoint_external.h5",
  "weights_loaded": true,
  "paper": "https://doi.org/10.1038/s41598-023-27671-8"
}
```

### Process Images (Main Endpoint)

Upload DICOM or NIfTI files for processing:

#### Using cURL - DICOM Series

```bash
# Process a DICOM series (multiple files)
curl -X POST http://localhost:8000/process \
  -F "files=@/path/to/dicom/slice1.dcm" \
  -F "files=@/path/to/dicom/slice2.dcm" \
  -F "files=@/path/to/dicom/slice3.dcm" \
  --output raclahe_output.zip
```

#### Using cURL - NIfTI File

```bash
# Process a NIfTI file
curl -X POST http://localhost:8000/process \
  -F "files=@/path/to/image.nii.gz" \
  --output raclahe_output.zip
```

#### Using Python - requests library

```python
import requests

# Process DICOM series
url = "http://localhost:8000/process"
files = [
    ('files', open('slice1.dcm', 'rb')),
    ('files', open('slice2.dcm', 'rb')),
    ('files', open('slice3.dcm', 'rb'))
]

response = requests.post(url, files=files)

if response.status_code == 200:
    with open('raclahe_output.zip', 'wb') as f:
        f.write(response.content)
    print("Processing successful! Output saved to raclahe_output.zip")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

#### Using Python - Upload entire DICOM directory

```python
import requests
import os
from pathlib import Path

def process_dicom_directory(dicom_dir: str, output_zip: str):
    """Upload all DICOM files from a directory"""
    url = "http://localhost:8000/process"
    
    # Collect all DICOM files
    files = []
    for file in Path(dicom_dir).glob("*.dcm"):
        files.append(('files', (file.name, open(file, 'rb'), 'application/dicom')))
    
    if not files:
        print(f"No DICOM files found in {dicom_dir}")
        return
    
    print(f"Uploading {len(files)} DICOM files...")
    
    # Send request
    response = requests.post(url, files=files)
    
    # Close file handles
    for _, (_, file_obj, _) in files:
        file_obj.close()
    
    # Save output
    if response.status_code == 200:
        with open(output_zip, 'wb') as f:
            f.write(response.content)
        print(f"Success! Output saved to {output_zip}")
    else:
        print(f"Error {response.status_code}: {response.json()}")

# Usage
process_dicom_directory('/path/to/dicom/folder', 'output.zip')
```

#### Using Python - Process NIfTI file

```python
import requests

def process_nifti(nifti_file: str, output_zip: str):
    """Process a NIfTI file"""
    url = "http://localhost:8000/process"
    
    with open(nifti_file, 'rb') as f:
        files = [('files', (os.path.basename(nifti_file), f, 'application/gzip'))]
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        with open(output_zip, 'wb') as f:
            f.write(response.content)
        print(f"Success! Output saved to {output_zip}")
    else:
        print(f"Error {response.status_code}: {response.json()}")

# Usage
process_nifti('patient_image.nii.gz', 'enhanced_output.zip')
```

## Complete Python Client Example

```python
#!/usr/bin/env python3
"""
RACLAHE API Client
"""

import requests
import os
from pathlib import Path
from typing import Union, List

class RACLAHEClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self) -> dict:
        """Check API health"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_info(self) -> dict:
        """Get API information"""
        response = requests.get(f"{self.base_url}/info")
        return response.json()
    
    def process_dicom_directory(self, dicom_dir: str, output_path: str) -> bool:
        """
        Process all DICOM files in a directory
        
        Args:
            dicom_dir: Path to directory containing DICOM files
            output_path: Path where to save the output zip file
        
        Returns:
            True if successful, False otherwise
        """
        files = []
        for file in Path(dicom_dir).glob("*.dcm"):
            files.append(('files', (file.name, open(file, 'rb'), 'application/dicom')))
        
        if not files:
            print(f"No DICOM files found in {dicom_dir}")
            return False
        
        print(f"Uploading {len(files)} DICOM files...")
        
        try:
            response = requests.post(f"{self.base_url}/process", files=files)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"✓ Success! Output saved to {output_path}")
                return True
            else:
                print(f"✗ Error {response.status_code}: {response.json()}")
                return False
        finally:
            # Close file handles
            for _, (_, file_obj, _) in files:
                file_obj.close()
    
    def process_nifti(self, nifti_path: str, output_path: str) -> bool:
        """
        Process a NIfTI file
        
        Args:
            nifti_path: Path to NIfTI file (.nii or .nii.gz)
            output_path: Path where to save the output zip file
        
        Returns:
            True if successful, False otherwise
        """
        with open(nifti_path, 'rb') as f:
            files = [('files', (os.path.basename(nifti_path), f, 'application/gzip'))]
            
            print(f"Uploading {os.path.basename(nifti_path)}...")
            response = requests.post(f"{self.base_url}/process", files=files)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ Success! Output saved to {output_path}")
            return True
        else:
            print(f"✗ Error {response.status_code}: {response.json()}")
            return False


# Example usage
if __name__ == "__main__":
    client = RACLAHEClient("http://localhost:8000")
    
    # Check if API is running
    health = client.health_check()
    print(f"API Status: {health['status']}")
    
    # Get API info
    info = client.get_info()
    print(f"API Version: {info['api_version']}")
    
    # Process DICOM directory
    # client.process_dicom_directory('/path/to/dicom/folder', 'output.zip')
    
    # Process NIfTI file
    # client.process_nifti('/path/to/image.nii.gz', 'output.zip')
```

Save this as `raclahe_client.py` and use it:

```bash
python raclahe_client.py
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

| Status Code | Meaning |
|-------------|---------|
| 200 | Success - Returns zip file |
| 400 | Bad Request - Invalid input (wrong file type, mixed types, etc.) |
| 413 | Payload Too Large - Upload exceeds max size |
| 500 | Internal Server Error - Processing failed |

### Example Error Response

```json
{
  "detail": "Unsupported file type: image.jpg. Only .dcm, .nii, and .nii.gz are supported"
}
```

## Configuration

### Environment Variables

Configure the API using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API host address |
| `API_PORT` | `8000` | API port |
| `WEIGHTS_PATH` | `/home/ds/BBOX_WEIGHTS/...` | Model weights path |
| `TEMP_DIR` | `/tmp/raclahe` | Temporary files directory |
| `MAX_UPLOAD_SIZE` | `524288000` | Max upload size in bytes (500MB) |

### Using .env file

Create a `.env` file:

```env
API_PORT=8000
MAX_UPLOAD_SIZE=1073741824  # 1GB
```

Run with environment file:

```bash
docker-compose -f docker-compose.api.yml up
```

## Performance Tips

1. **File Size**: Compress NIfTI files (.nii.gz) to reduce upload time
2. **Concurrent Requests**: The API can handle multiple requests simultaneously
3. **Network**: Use local deployment for large files
4. **Resources**: Allocate sufficient CPU/memory in docker-compose configuration

## Production Deployment

### With Nginx Reverse Proxy

1. Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream raclahe_api {
        server raclahe-api:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        client_max_body_size 500M;

        location / {
            proxy_pass http://raclahe_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts for long-running requests
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }
    }
}
```

2. Run with nginx:

```bash
docker-compose -f docker-compose.api.yml --profile production up
```

### With SSL/HTTPS

Add SSL certificates and update nginx configuration to handle HTTPS.

## Troubleshooting

### API won't start

```bash
# Check logs
docker-compose logs raclahe-api

# Check if weights file exists
docker-compose exec raclahe-api ls -la /home/ds/BBOX_WEIGHTS/WHOLE\ GLAND/
```

### Upload fails with 413 error

Increase `MAX_UPLOAD_SIZE`:

```bash
MAX_UPLOAD_SIZE=1073741824 docker-compose up raclahe-api
```

### Processing takes too long

- Increase CPU/memory limits in docker-compose.yml
- Process smaller batches
- Check system resources

### Connection refused

Ensure the API is running and port 8000 is accessible:

```bash
# Check if running
docker ps | grep raclahe-api

# Check port
curl http://localhost:8000/health
```

## API Rate Limiting

For production use, consider implementing rate limiting using nginx or a dedicated API gateway.

## Support

For issues or questions:
- API Documentation: http://localhost:8000/docs
- Main README: [README.md](README.md)
- Contact: dimzaridis@gmail.com

