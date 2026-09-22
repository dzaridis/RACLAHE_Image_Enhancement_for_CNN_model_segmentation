import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import argparse
import sys
import warnings
warnings.filterwarnings("ignore")

from time import sleep
from rich.progress import Progress

from utils.filereader import *
from utils.Raclahe_Process import *

# Defaults follow the EUCAIM reference node layout, but every path can be
# overridden on the command line (preferred) or via environment variables.
DEFAULT_INPUT = os.getenv('INPUT_DIR', '/home/ds/datasets')
DEFAULT_OUTPUT = os.getenv('OUTPUT_DIR', '/home/ds/persistent-home/output')
DEFAULT_WEIGHTS = os.getenv(
    'WEIGHTS_PATH', '/home/ds/bbox_weights/checkpoint_external.h5')


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='raclahe',
        description='RACLAHE image enhancement for prostate T2-Weighted MR images.')
    parser.add_argument(
        'input_dir', nargs='?', default=DEFAULT_INPUT,
        help='Dataset directory containing one sub-directory per patient '
             '(default: %(default)s)')
    parser.add_argument(
        'output_dir', nargs='?', default=DEFAULT_OUTPUT,
        help='Directory where the enhanced images are written; use a path '
             'under persistent-home so results survive the job '
             '(default: %(default)s)')
    parser.add_argument(
        '--weights', dest='weights_path', default=DEFAULT_WEIGHTS,
        help='Path to the bounding-box U-Net weights (.h5) '
             '(default: %(default)s)')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    user_input = os.path.abspath(os.path.expanduser(args.input_dir))
    user_output = os.path.abspath(os.path.expanduser(args.output_dir))
    weights_path = os.path.expanduser(args.weights_path)

    if not os.path.isdir(user_input):
        sys.exit(f'Error: input directory does not exist or is not a '
                 f'directory: {user_input}')
    if not os.path.isfile(weights_path):
        sys.exit(f'Error: bounding-box model weights not found: '
                 f'{weights_path}\nProvide them with --weights or the '
                 f'WEIGHTS_PATH environment variable.')

    os.makedirs(user_output, exist_ok=True)

    dirs = sorted(os.listdir(user_input))

    print('Raclahe filter application has been started ... ')
    print(f'Input directory: {user_input}')
    print(f'Output directory: {user_output}')
    print(f'Weights path: {weights_path}')
    print(f'Processing {len(dirs)} items...')

    with Progress() as progress:
        task = progress.add_task(
            "[bold green]Raclahe Processing...[/bold green]", total=len(dirs))
        for file in dirs:  # lists the patients
            pat_dir = os.path.join(user_input, file)
            # Skip if not a directory
            if not os.path.isdir(pat_dir):
                progress.update(task, advance=1)
                continue

            try:
                checker = MedicalImageReader(pat_dir)
                raclahe_input = checker.read_image()
                pat_name = str(file)

                metadata = Raclahe_process_nifti(
                    pat_name, weights_path, raclahe_input, user_output, pat_dir)
            except Exception as e:
                print("Info:", f"Raclahe was unable to perform operation on "
                               f"patient {file}: {str(e)}")

            progress.update(task, advance=1)
            sleep(1)
    print('Raclahe filter application has ended ')


if __name__ == '__main__':
    main()
