from utils.filereader import *
from utils.Raclahe_Process import *
from glob import glob
import argparse
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import os
import warnings
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from rich.console import Console
import warnings
from time import sleep
warnings.filterwarnings("ignore")

# EUCAIM-compliant paths - can be overridden via environment variables
user_input = os.getenv('INPUT_DIR', '/home/ds/datasets')
user_output = os.getenv('OUTPUT_DIR', '/home/ds/persistent-home/output')
weights_path = os.getenv('WEIGHTS_PATH', '/home/ds/BBOX_WEIGHTS/WHOLE GLAND/checkpoint_external.h5')

# Create output directory if it doesn't exist
os.makedirs(user_output, exist_ok=True)

# List directories in input path
dirs = os.listdir(user_input)
progress = Progress()
print('Raclahe filter application has been started ... ')
print(f'Input directory: {user_input}')
print(f'Output directory: {user_output}')
print(f'Weights path: {weights_path}')
print(f'Processing {len(dirs)} items...')

with progress:
    task = progress.add_task("[bold green]Raclahe Processing...[/bold green]", total=len(dirs))
    for index, file in enumerate(dirs):  # lists the patients
        pat_dir = os.path.join(user_input, file)
        # Skip if not a directory
        if not os.path.isdir(pat_dir):
            progress.update(task, advance=1)
            continue
            
        try:
            checker = MedicalImageReader(pat_dir)
            raclahe_input = checker.read_image()
            pat_name = str(file)
            
            metadata = Raclahe_process_nifti(pat_name, weights_path, raclahe_input, user_output, pat_dir)
        except Exception as e:
            print("Info:", f"Raclahe was unable to perform operation on patient {file}: {str(e)}")
        
        progress.update(task, advance=1)
        sleep(1)
    print('Raclahe filter application has ended ')


