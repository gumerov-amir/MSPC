#!/usr/bin/env python3

import os
import platform
import re
import shutil
import sys

if not sys.platform == "win32":
    raise NotImplementedError("This tool is only for windows")

import bs4

import patoolib

import requests

from .. import downloader


url = "https://sourceforge.net/projects/mpv-player-windows/files/libmpv/"

cd = os.getcwd()


def download() -> None:
    r = requests.get(url)
    page = bs4.BeautifulSoup(r.text, features="html.parser")
    table = page.table
    if platform.architecture()[0][0:2] == "64":
        download_url = table.find("a", href=True, title=re.compile("x86_64")).get(
            "href"
        )
    else:
        download_url = table.find("a", href=True, title=re.compile("i686")).get("href")
    downloader.download_file(download_url, os.path.join(cd, "libmpv.7z"))


def extract() -> None:
    try:
        os.mkdir(os.path.join(cd, "libmpv"))
    except FileExistsError:
        shutil.rmtree(os.path.join(cd, "libmpv"))
        os.mkdir(os.path.join(cd, "libmpv"))
    patoolib.extract_archive(
        os.path.join(cd, "libmpv.7z"),
        outdir=os.path.join(cd, "libmpv"),
    )


def move() -> None:
    try:
        os.rename(
            os.path.join(cd, "libmpv", "mpv-2.dll"),
            os.path.join(cd, "mpv.dll"),
        )
    except FileExistsError:
        os.remove(os.path.join(cd, "mpv.dll"))
        os.rename(
            os.path.join(cd, "libmpv", "mpv-2.dll"),
            os.path.join(cd, "mpv.dll"),
        )


def clean() -> None:
    os.remove(os.path.join(cd, "libmpv.7z"))
    shutil.rmtree(os.path.join(cd, "libmpv"))


def main() -> None:
    download()
    extract()
    move()
    clean()


if __name__ == "__main__":
    main()
