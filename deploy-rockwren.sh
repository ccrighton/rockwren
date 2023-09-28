# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later

mkdir deploy/lib/rockwren
# Rockwren
cp -r rockwren deploy/lib
rm -r deploy/lib/rockwren/__pycache__
# Libraries
cp -r phew/phew deploy/lib
cd deploy
../venv/Scripts/mpremote.exe cp -r lib :
