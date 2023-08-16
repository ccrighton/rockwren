# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import os

import python_minifier

os.chdir('deploy/lib/phew')

files = [f for f in os.listdir() if os.path.isfile(f) and f.endswith('py')]

total_size = 0
total_minified_size = 0

for filename in files:
    size = os.stat(filename).st_size
    minified_size = 0
    print(f"{filename}: {size}")
    with open(filename) as f:
        minified_size = len(python_minifier.minify(f.read()))
    print(f"{filename}: {minified_size}")
    total_size += size
    total_minified_size += minified_size

print(f"Total size: {total_size}")
print(f"Total minified size: {total_minified_size}")
print(f"Size of output as %:  {total_minified_size/total_size*100}")
