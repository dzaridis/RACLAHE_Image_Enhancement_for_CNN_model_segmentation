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

user_input="/dir/input"#str(input())#"/dir/input"
user_output="/dir/output"#str(input())#"/dir/output"
dirs = os.listdir(user_input)
progress=Progress()
print('Raclahe filter application has been started ... ')
with progress:
    task = progress.add_task("[bold green]Raclahe Processing...[/bold green]", total=len(dirs))
    for index,file in enumerate(dirs): # lists the patients
        pat_dir = os.path.join(user_input, file)
        #path_inp=os.path.join(user_input,file)
        checker = MedicalImageReader(pat_dir)
        raclahe_input = checker.read_image()
        pat_name=str(file)
        try:
            w_p="/dir/BBOX_WEIGHTS/WHOLE GLAND/checkpoint_external.h5"#"/dir/BBOX_WEIGHTS/WHOLE GLAND/checkpoint_external.h5"

            metadata=Raclahe_process_nifti(pat_name,w_p,raclahe_input,user_output, pat_dir)
        except:
            print("Info:","Raclahe was unable to perform operation on that patient")
        progress.update(task, advance=1)
        sleep(1)
    print('Raclahe filter application has ended ')


