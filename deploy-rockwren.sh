mkdir deploy/lib/rockwren
# Rockwren
cp -r rockwren deploy/lib
# Libraries
cp -r phew/phew deploy/lib
cd deploy
../venv/Scripts/mpremote.exe cp -r lib :
