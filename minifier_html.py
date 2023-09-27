# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import os

import minify_html


def minify_file(filename):
    with open(filename, 'r') as f:
        minified = minify_html.minify(f.read(), minify_js=True, remove_processing_instructions=True)
        minified_size = len(minified)
    with open(filename, 'w') as f:
        f.seek(0)
        f.write(minified)
    return minified_size


def minify(directory):

    files = [directory + '/' + f for f in os.listdir(directory) if os.path.isfile(directory + '/' + f)
             and (f.endswith('html') or f.endswith('css') or f.endswith('js'))]

    total_size = 0
    total_minified_size = 0

    for filename in files:
        size = os.stat(filename).st_size
        minified_size = minify_file(filename)
        total_size += size
        total_minified_size += minified_size
        print(f"{filename}: Size: {total_size}, minified size: {total_minified_size}, "
              f"%{total_minified_size / total_size * 100:.0f}")


def parse_args():
    """Parse the args."""
    parser = argparse.ArgumentParser(
        description='minifier_html.py')
    parser.add_argument('-d', '--directory', type=str, required=True,
                        help='Directory of module to minify')

    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    minify(args.directory)
