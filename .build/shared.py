import os
import sys
from typing import Optional

site_dir = 'build'


def downgrade_image(path: str, max_resolution=None, extension=None):
    relative_path = removeprefix(removeprefix(path, 'assets/'), 'resized/')
    compressed_path = os.path.join('assets/resized', os.path.dirname(relative_path))
    (name, old_extension) = os.path.splitext(os.path.basename(relative_path))

    name = removesuffix(name, '-min')
    name_parts = name.split('-')
    if name_parts and safe_int(name_parts[-1]):
        name = removesuffix(name, '-' + name_parts[-1])
    if extension is None:
        extension = old_extension

    def extract_resolution(file_path: str) -> int:
        parts = os.path.basename(removesuffix(os.path.splitext(file_path)[0], '-min')).split('-')
        if parts and safe_int(parts[-1]):
            return safe_int(parts[-1])
        else:
            return sys.maxsize

    def is_in_family(file: str) -> bool:
        matches_start = os.path.basename(file).startswith(name)
        matches_end = file.endswith(extension)
        matches_middle = len(removeprefix(file, name).split('-')) == 3

        return matches_start and matches_middle and matches_end

    compressed_files = []
    if os.path.exists(compressed_path):
        compressed_files = list(filter(
            lambda file: is_in_family(file), os.listdir(compressed_path)))
    if max_resolution:
        compressed_files = list(filter(
            lambda file: extract_resolution(file) <= max_resolution, compressed_files))
    compressed_files.sort(key=lambda file: extract_resolution(file))

    return os.path.join(compressed_path, compressed_files[-1]) if compressed_files else None


def safe_int(val: str) -> Optional[int]:
    try:
        return int(val)
    except ValueError:
        return None


# TODO remove these two once python 3.9 is the default
# See https://www.python.org/dev/peps/pep-0616/

def removeprefix(self: str, prefix: str) -> str:
    if self.startswith(prefix):
        return self[len(prefix):]
    else:
        return self[:]


def removesuffix(self: str, suffix: str) -> str:
    # suffix='' should not call self[:-0].
    if suffix and self.endswith(suffix):
        return self[:-len(suffix)]
    else:
        return self[:]
