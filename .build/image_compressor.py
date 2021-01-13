import os
import shutil
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from subprocess import check_call, STDOUT, PIPE
from typing import List

from shared import site_dir, broken_outputs, removeprefix

assets_dir = 'assets'
output_assets_dir = 'assets/resized'
support_files = ['.png', '.jpg', '.jpeg']
output_formats = {'jpg': 'mozjpeg', 'webp': 'webp', 'avif': 'avif'}
compressed_file_suffix = '-min'
squoosh = '.build/node_modules/.bin/squoosh-cli'


def main():
    pool = ThreadPoolExecutor(max_workers=max(1, int(os.cpu_count() / 2)))
    tasks: List[Future] = []

    for root, subdirs, files in os.walk(assets_dir):
        for file in files:
            tasks.append(pool.submit(compress, root, file))

    for task in tasks:
        task.result()


def compress(parent: str, file: str):
    (file_name, extension) = os.path.splitext(file)
    input_path = os.path.join(parent, file)
    resized = parent.startswith(output_assets_dir)

    if extension not in support_files:
        return
    if not resized and file_name.endswith(compressed_file_suffix):
        raise Exception(f'Illegal file name ending \'{compressed_file_suffix}\': {input_path}')
    if file_name.endswith(compressed_file_suffix):
        return

    for (file_type, command) in output_formats.items():
        output_dir = parent if resized else \
            os.path.join(output_assets_dir, removeprefix(removeprefix(parent, assets_dir), '/'))
        output_file = os.path.join(output_dir, f'{file_name}{compressed_file_suffix}.{file_type}')

        if not os.path.exists(output_file) and output_file not in broken_outputs:
            print(f'Generating {output_file}')

            check_call([
                squoosh,
                input_path,
                '--output-dir',
                output_dir,
                '--suffix',
                compressed_file_suffix,
                f'--{command}',
            ], stdout=PIPE, stderr=STDOUT, timeout=90)
            shutil.copyfile(output_file, os.path.join(site_dir, output_file))

            print(f'Done processing {output_file}')


if __name__ == '__main__':
    main()
