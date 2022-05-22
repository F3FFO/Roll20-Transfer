#!/usr/bin/env python3
import argparse
import errno
import os
import shutil
import stat
import sys
import requests
import tarfile

WEBDRIVER = "geckodriver"


def error(str):
    if is_ci:
        print(f"\n ! {str}\n")
    else:
        print(f"\n\033[41m{str}\033[0m\n")
    sys.exit(1)


def header(str):
    if is_ci:
        print(f"\n{str}\n")
    else:
        print(f"\n\033[44m{str}\033[0m\n")


def vprint(str):
    if args.verbose:
        print(str)


is_ci = "CI" in os.environ and os.environ["CI"] == "true"

# Environment checks
if sys.version_info < (3, 6):
    vprint(f"Your python verion is {sys.version_info}")
    error("Requires Python 3.6+")


def mv(source, target):
    print(source)
    print(target)
    try:
        shutil.move(source, target)
        vprint(f"mv {source} -> {target}")
    except:
        pass


def cp(source, target):
    try:
        shutil.copyfile(source, target)
        vprint(f"cp {source} -> {target}")
    except:
        pass


def rm(file):
    try:
        os.remove(file)
        vprint(f"rm {file}")
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def download_file(url):
    local_filename = url.split("/")[-1]
    vprint(f"Downloading {local_filename}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    # if chunk:
                    f.write(chunk)

        vprint(f"{local_filename} downloaded!")
        return local_filename
    except:
        error("Cannot download driver.")


def extract_file(local_file):
    vprint(f"Extracting {local_file}...")
    shutil.unpack_archive(local_file, ".", "gztar")
    file = tarfile.open(local_file)
    # extracting file
    file.extractall("./")
    file.close()
    vprint(f"{local_file} extracted!")


def install_webdriver(url):
    file = download_file(url)
    extract_file(file)
    os.chmod(
        WEBDRIVER,
        stat.S_IRUSR
        | stat.S_IWUSR
        | stat.S_IXUSR
        | stat.S_IRGRP
        | stat.S_IXGRP
        | stat.S_IROTH
        | stat.S_IXOTH,
    )
    rm(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Roll20")
    parser.set_defaults(func=lambda x: None)
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")

    args = parser.parse_args()

    url = "https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-linux64.tar.gz"
    install_webdriver(url)
