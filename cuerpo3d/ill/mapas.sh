#!/bin/bash
# Texture maps for one exercise (3-5 min): borders, per-muscle shading and the red of the worked muscles.
#   ill/mapas.sh <folder> "<muscle:intensity,...>"      (names from ill/spec, without .L/.R; groups like trapezius work)
#   e.g. ill/mapas.sh maps_fp2 "deltoid_posterior:1,trapezius:1,rhomboid_major:1,infraspinatus:1,teres_minor:1"
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/ill
D=$1; LIST=$2; mkdir -p $D; cp curves_base.npz $D/curves.npz
SRR=0.35 $S/venv/bin/python -I linemap.py pv/bla.npz $D "$LIST" > /dev/null
CSMAX=0.012 CCSM=150 LNEAR=0.008 NDOT=0.0 DOME=pv/bla_dome.npz LSTR=$D/lstr_lut.npy LDW=25 $S/venv/bin/python -I bakemaps.py pv/bla.npz $D 2>&1 | grep -i "error\|trace" -A3
$S/venv/bin/python -I redmap.py pv/bla.npz $D "$LIST"
rm -f $D/lstr.*.png
