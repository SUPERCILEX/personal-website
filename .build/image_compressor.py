import os
import shutil
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from subprocess import check_call, PIPE
from typing import List

from shared import site_dir, strip_compression_suffix, compressed_file_suffix

assets_dir = 'assets'
output_assets_dir = 'assets/resized'
supported_files = ['.png', '.jpg', '.jpeg', '.svg']
output_formats = ['jpg', 'webp', 'avif']
svgo = '.build/node_modules/.bin/svgo'


def main():
    pool = ThreadPoolExecutor(max_workers=max(1, int(os.cpu_count() / 2)))
    tasks: List[Future] = []

    for root, _, files in os.walk(assets_dir):
        for file in files:
            tasks.append(pool.submit(compress, root, file))

    for task in tasks:
        task.result()
    prune()


def prune():
    src_images = set()

    for root, _, files in os.walk(assets_dir):
        for file in files:
            path = os.path.join(root, file)
            if output_assets_dir not in path:
                src_images.add(os.path.splitext(path)[0])

    for root, _, files in os.walk(output_assets_dir):
        for file in files:
            path = os.path.join(root, file)
            name = strip_compression_suffix(os.path.splitext(file)[0])
            original_path = os.path.join(
                assets_dir,
                os.path.dirname(path).removeprefix(output_assets_dir).removeprefix('/'),
                name
            )

            if original_path not in src_images:
                print(f'Removing stale image: {path}')
                os.remove(path)
                os.remove(os.path.join(site_dir, path))


def compress(parent: str, file: str):
    (file_name, extension) = os.path.splitext(file)
    input_path = os.path.join(parent, file)
    resized = parent.startswith(output_assets_dir)

    if extension not in supported_files:
        return
    if not resized and file_name != strip_compression_suffix(file_name):
        raise Exception(f'Illegal file name ending for compression: {input_path}')
    if file_name.endswith(compressed_file_suffix):
        return

    if extension == '.svg':
        output_dir = \
            os.path.join(output_assets_dir, parent.removeprefix(assets_dir).removeprefix('/'))
        output_file = os.path.join(output_dir, f'{file_name}{compressed_file_suffix}.svg')

        if not os.path.exists(output_file):
            print(f'Generating {output_file}')

            args = [
                svgo,
                input_path,
                '--multipass',
                '--output', output_file,
            ]
            if input_path == 'assets/projects/ftzz/scheduling-order.svg':
                args.extend([
                    '--config',
                    '.build/assets-projects-ftzz-scheduling-order.svgo.config.js',
                ])

            check_call(args, stdout=PIPE, timeout=90)
            resized_output = os.path.join(site_dir, output_file)
            os.makedirs(os.path.dirname(resized_output), exist_ok=True)
            shutil.copyfile(output_file, resized_output)

            print(f'Done processing {output_file}')

        return

    for file_type in output_formats:
        output_dir = parent if resized else \
            os.path.join(output_assets_dir, parent.removeprefix(assets_dir).removeprefix('/'))
        output_file = os.path.join(output_dir, f'{file_name}{compressed_file_suffix}.{file_type}')

        if not os.path.exists(output_file):
            print(f'Generating {output_file}')

            check_call([
                'convert',
                input_path,
                f"{file_type}:{output_file}",
            ], stdout=PIPE, timeout=90)
            resized_output = os.path.join(site_dir, output_file)
            os.makedirs(os.path.dirname(resized_output), exist_ok=True)
            shutil.copyfile(output_file, resized_output)

            print(f'Done processing {output_file}')


if __name__ == '__main__':
    main()
