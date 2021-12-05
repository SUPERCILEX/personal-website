import os
import sys
from typing import Optional

site_url = 'https://alexsaveau.dev'
site_dir = 'build'
compressed_file_suffix = '-min'


def downgrade_image(path: str, max_resolution=None, extension=None):
    relative_path = path.removeprefix('assets/').removeprefix('resized/')
    compressed_path = os.path.join('assets/resized', os.path.dirname(relative_path))
    (name, old_extension) = os.path.splitext(os.path.basename(relative_path))

    name = strip_compression_suffix(name)
    if extension is None:
        extension = old_extension

    def extract_resolution(file_path: str) -> int:
        parts = os.path.basename(
            os.path.splitext(file_path)[0].removesuffix(compressed_file_suffix)
        ).split('-')
        if parts and safe_int(parts[-1]):
            return safe_int(parts[-1])
        else:
            return sys.maxsize

    def is_in_family(file: str) -> bool:
        matches_start = file.startswith(name)
        matches_end = file.endswith(extension)

        middle = os.path.splitext(file.removeprefix(name))[0]
        middle_parts = middle.removesuffix(compressed_file_suffix).split('-')
        matches_middle = len(middle_parts) <= 2 and middle_parts[0] == ''

        return matches_start and matches_middle and matches_end

    compressed_files = []
    if os.path.exists(compressed_path):
        compressed_files = list(filter(
            lambda file: is_in_family(file), os.listdir(compressed_path)))

    minified_files = list(filter(
        lambda file: os.path.splitext(file)[0].endswith(compressed_file_suffix), compressed_files))
    if len(minified_files) > 0:
        compressed_files = minified_files

    if max_resolution:
        compressed_files = list(filter(
            lambda file: extract_resolution(file) <= max_resolution, compressed_files))
    compressed_files.sort(key=lambda file: extract_resolution(file))

    return os.path.join(compressed_path, compressed_files[-1]) if compressed_files else None


def strip_compression_suffix(name):
    name = name.removesuffix(compressed_file_suffix)
    name_parts = name.split('-')
    if name_parts and safe_int(name_parts[-1]):
        name = name.removesuffix('-' + name_parts[-1])
    return name


def safe_int(val: str) -> Optional[int]:
    try:
        return int(val)
    except ValueError:
        return None
