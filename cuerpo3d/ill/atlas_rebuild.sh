#!/bin/bash
# Rebuild the muscle atlas after editing ill/spec/*.py (about 2 min), then run ill/mapas.sh again for each exercise.
#   Specs: shared + back + leg + arm (+ front.py when it exists).  Writes pv/bla.npz, pv/bla_dome.npz,
#   curves_base.npz (border list used by mapas.sh) and pv/bla_row2.npz (fibres for the renderer).
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/ill
export CSMAX=0.012 CCSM=150      # border smoothing used for the approved atlas (atlas.py and bakemaps.py)
SPECS="spec/shared.py spec/back.py spec/leg.py spec/arm.py"; [ -f spec/front.py ] && SPECS="$SPECS spec/front.py"
$S/venv/bin/python -I atlas.py pv/bla.npz $SPECS 2>&1 | grep -v detour | grep PROBLEM
$S/venv/bin/python -I bulge.py pv/bla.npz pv/bla_dome.npz | tail -1
CSMAX=0.012 CCSM=150 LNEAR=0.008 NDOT=0.0 DOME=pv/bla_dome.npz $S/venv/bin/python -I bakemaps.py pv/bla.npz maps_tmp 2>&1 | grep -i "error\|trace" -A3
cp maps_tmp/curves.npz curves_base.npz; rm -rf maps_tmp
$S/venv/bin/python -I stylefields.py pv/bla.npz pv/bla_row2.npz "trapezius:1" > /dev/null
echo "atlas listo: ahora ill/mapas.sh <carpeta> \"<musculos>\" para cada ejercicio"
