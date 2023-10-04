# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import os
import tarfile
from pathlib import Path
from pprint import pprint
from urllib.request import urlretrieve

from pypi_json import PyPIJSON


def tar_members_stripped(tar, levels_stripped=1):
    members = []
    for member in tar.getmembers():
        p = Path(member.path)
        member.path = p.relative_to(*p.parts[:levels_stripped])
        members.append(member)
    return members


def download_and_extract(package_name, outdir):

    print(f"download_and_extract({package_name})")
    filename = None
    url = None

    with PyPIJSON() as client:
        requests_metadata = client.get_metadata(package_name)
        pkg = ''
        for i in range(len(requests_metadata.urls)):
            if requests_metadata.urls[i]['packagetype'] == 'sdist':
                pkg = requests_metadata.urls[i]
                break

        pprint(pkg)
        filename = pkg['filename']
        url = pkg['url']

    package_filename = 'deploy/' + filename

    urlretrieve(url, package_filename)

    # open file
    with tarfile.open(package_filename) as f:
        print(f.getmembers())
        f.extractall(path=outdir, members=tar_members_stripped(f, 1))


def parse_args():
    """Parse the args."""
    parser = argparse.ArgumentParser(
        description='get-libs.py')
    parser.add_argument('-o', '--outdir', type=str, required=True,
                        default='build/lib',
                        help='Output directory for module')
    parser.add_argument('-m', '--module', type=str, required=True,
                        help='Module name')

    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    try:
        os.makedirs(args.outdir)
    except Exception as e:
        pprint(e)
        pass

    download_and_extract(args.module, args.outdir)
