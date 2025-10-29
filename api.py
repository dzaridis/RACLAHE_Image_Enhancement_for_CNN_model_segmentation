#!/usr/bin/env python3
"""
RACLAHE FastAPI Application
REST API for processing medical images with RACLAHE enhancement
"""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List
import uuid
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GIT_PYTHON_REFRESH'] = "quiet"

from utils.filereader import MedicalImageReader
from utils.Raclahe_Process import Raclahe_process_nifti

import warnings
warnings.filterwarnings("ignore")

# Initialize FastAPI app
app = FastAPI(
    title="RACLAHE Image Enhancement API",
    description="REST API for Region-Adaptive Contrast Limited Adaptive Histogram Equalization on medical images",
    version="3.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
WEIGHTS_PATH = os.getenv('WEIGHTS_PATH', '/home/ds/BBOX_WEIGHTS/WHOLE GLAND/checkpoint_external.h5')
TEMP_DIR = os.getenv('TEMP_DIR', '/tmp/raclahe')
MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', 1024 * 1024 * 500))  # 500MB default

# Create temp directory
os.makedirs(TEMP_DIR, exist_ok=True)


def cleanup_directory(directory: str):
    """Clean up temporary directory"""
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    except Exception as e:
        print(f"Warning: Failed to clean up directory {directory}: {e}")


def create_zip_from_directory(source_dir: str, output_zip: str) -> str:
    """Create a zip file from a directory"""
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    return output_zip


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "RACLAHE Image Enhancement API",
        "version": "3.0",
        "documentation": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "weights_available": os.path.exists(WEIGHTS_PATH)
    }


@app.post("/process")
async def process_images(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="DICOM series files or a single NIfTI file")
):
    """
    Process medical images with RACLAHE enhancement
    
    Upload either:
    - Multiple DICOM files (.dcm) from a single series
    - A single NIfTI file (.nii or .nii.gz)
    
    Returns a zip file containing the enhanced images in the same format as input
    """
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, session_id)
    input_dir = os.path.join(session_dir, "input")
    output_dir = os.path.join(session_dir, "output")
    
    try:
        # Create session directories
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Validate and save uploaded files
        file_types = set()
        total_size = 0
        
        for file in files:
            # Check file extension
            filename = file.filename.lower()
            if filename.endswith('.dcm'):
                file_types.add('dicom')
            elif filename.endswith('.nii') or filename.endswith('.nii.gz'):
                file_types.add('nifti')
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file.filename}. Only .dcm, .nii, and .nii.gz are supported"
                )
            
            # Save file
            file_path = os.path.join(input_dir, file.filename)
            with open(file_path, 'wb') as f:
                content = await file.read()
                total_size += len(content)
                
                if total_size > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Total upload size exceeds maximum allowed size of {MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
                    )
                
                f.write(content)
        
        # Validate file type consistency
        if len(file_types) > 1:
            raise HTTPException(
                status_code=400,
                detail="Mixed file types detected. Please upload either DICOM files or a NIfTI file, not both"
            )
        
        # Validate NIfTI upload (should be single file)
        if 'nifti' in file_types and len(files) > 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple NIfTI files detected. Please upload only one NIfTI file at a time"
            )
        
        print(f"Processing session {session_id}: {len(files)} file(s), type: {file_types}")
        
        # Read medical images
        try:
            checker = MedicalImageReader(input_dir)
            raclahe_input = checker.read_image()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read medical images: {str(e)}"
            )
        
        # Process with RACLAHE
        try:
            patient_name = f"patient_{session_id[:8]}"
            metadata = Raclahe_process_nifti(
                patient_name,
                WEIGHTS_PATH,
                raclahe_input,
                output_dir,
                input_dir
            )
            print(f"Processing completed for session {session_id}")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"RACLAHE processing failed: {str(e)}"
            )
        
        # Find output files
        output_patient_dir = os.path.join(output_dir, "RACLAHE OUTPUT", patient_name)
        
        if not os.path.exists(output_patient_dir):
            raise HTTPException(
                status_code=500,
                detail="Processing completed but output files not found"
            )
        
        # Create zip file
        zip_filename = f"raclahe_output_{session_id[:8]}.zip"
        zip_path = os.path.join(session_dir, zip_filename)
        
        try:
            create_zip_from_directory(output_patient_dir, zip_path)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create zip file: {str(e)}"
            )
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_directory, session_dir)
        
        # Return zip file
        return FileResponse(
            path=zip_path,
            media_type='application/zip',
            filename=zip_filename,
            background=background_tasks
        )
    
    except HTTPException:
        # Clean up on HTTP exceptions
        cleanup_directory(session_dir)
        raise
    
    except Exception as e:
        # Clean up on unexpected errors
        cleanup_directory(session_dir)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.post("/process/batch")
async def process_batch(
    background_tasks: BackgroundTasks,
    patients: List[List[UploadFile]] = File(..., description="Multiple patient folders, each containing DICOM or NIfTI files")
):
    """
    Process multiple patients in batch
    
    Note: This is a simplified batch endpoint. For production use,
    consider implementing a job queue system for long-running batch operations.
    """
    raise HTTPException(
        status_code=501,
        detail="Batch processing endpoint not yet implemented. Please process patients individually."
    )


@app.get("/info")
async def get_info():
    """Get API and model information"""
    return {
        "api_version": "3.0",
        "model": "RACLAHE",
        "model_description": "Region-Adaptive Contrast Limited Adaptive Histogram Equalization",
        "supported_formats": ["DICOM (.dcm)", "NIfTI (.nii, .nii.gz)"],
        "max_upload_size_mb": MAX_UPLOAD_SIZE / (1024 * 1024),
        "weights_path": WEIGHTS_PATH,
        "weights_loaded": os.path.exists(WEIGHTS_PATH),
        "paper": "https://doi.org/10.1038/s41598-023-27671-8"
    }


if __name__ == "__main__":
    # Run the API server
    port = int(os.getenv('API_PORT', 8000))
    host = os.getenv('API_HOST', '0.0.0.0')
    
    print(f"Starting RACLAHE API server on {host}:{port}")
    print(f"Weights path: {WEIGHTS_PATH}")
    print(f"Documentation available at: http://{host}:{port}/docs")
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

