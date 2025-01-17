import os

from shared import site_dir


def main():
    for subdir, dirs, files in os.walk(site_dir):
        for file in files:
            if file == 'index.html':
                parent_dir = os.path.basename(subdir)
                if parent_dir == "build":
                    continue
                os.rename(os.path.join(subdir, file), os.path.join(os.path.dirname(subdir), f'{parent_dir}.html'))


if __name__ == '__main__':
    main()
