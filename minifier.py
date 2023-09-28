# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import os
from pprint import pprint

import python_minifier


def minify(directory):

    files = [directory + '/' + f for f in os.listdir(directory)
             if os.path.isfile(directory + '/' + f) and f.endswith('py')]

    total_size = 0
    total_minified_size = 0

    for filename in files:
        size = os.stat(filename).st_size
        minified_size = 0
        minified = None
        with open(filename) as f:
            minified = python_minifier.minify(f.read())
            minified_size = len(minified)
            total_size += size
        with open(filename, 'w') as f:
            f.write(minified)
        total_minified_size += minified_size
        print(f"{filename}: Size: {total_size}, minified size: {total_minified_size}, "
              f"%{total_minified_size / total_size * 100:.0f}")


def parse_args():
    """Parse the args."""
    parser = argparse.ArgumentParser(
        description='minifier.py')
    parser.add_argument('-d', '--directory', type=str, required=True,
                        help='Directory of module to minify')

    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    minify(args.directory)
