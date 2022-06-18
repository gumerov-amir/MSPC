#!/usr/bin/env python3

import os
import sys
import subprocess

from ..vars import package_path


locale_path = os.path.join(package_path, "locale")
pot_file_path = os.path.join(locale_path, "mspc.pot")
source_path = package_path
babel_prefix = "{} -m babel.messages.frontend".format(sys.executable)
locale_domain = "mspc"


def extract() -> None:
    code = subprocess.call(
        f"{babel_prefix} extract {source_path} -o {pot_file_path} --keywords=translator.translate -c translators: --copyright-holder=MSPC-team --project=MSPC",
        shell=True,
    )
    if code:
        sys.exit(code)


def update() -> None:
    code = subprocess.call(
        f"{babel_prefix} update -i {pot_file_path} -d {locale_path} -D {locale_domain} --update-header-comment --previous",
        shell=True,
    )
    if code:
        sys.exit(code)


def compile() -> None:
    code = subprocess.call(
        f"{babel_prefix} compile -d {locale_path} -D {locale_domain}", shell=True
    )
    if code:
        sys.exit(code)
