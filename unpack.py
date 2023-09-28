# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Unpack a module from a sdist package tar file.
"""
import argparse
import os
import tarfile


def strip_directory(t, directory):
    length = len(directory)
    members = []
    for member in t.getmembers():
        if not member.path.startswith(directory):
            raise Exception()
        member.path = member.path[length:]
        members.append(member)
    return members


def unpack(file, directory, module):
    with tarfile.open(file) as tar:
        rootpath = os.path.commonpath(tar.getnames())
        rootpathmember = tar.getmember(rootpath)
        members = tar.getmembers()
        members.remove(rootpathmember)
        members = strip_directory(tar, rootpath)
        members = [member for member in members if member.path.startswith(f"/{module}/")]
        tar.extractall(directory, members=members, filter='data')


def parse_args():
    """Parse the args."""
    parser = argparse.ArgumentParser(
        description='unpack.py')
    parser.add_argument('-f', '--file', type=str, required=True,
                        help='sdist package')
    parser.add_argument('-d', '--directory', type=str, required=True,
                        help='target directory')
    parser.add_argument('-m', '--module', type=str, required=True,
                        help='name of module to extract')

    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    unpack(args.file, args.directory, args.module)
