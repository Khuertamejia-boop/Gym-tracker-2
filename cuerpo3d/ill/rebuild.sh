#!/bin/bash
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/ill
ROW="trapezius:1,latissimus_dorsi:1,infraspinatus:1,teres_major:1,teres_minor:1,rhomboid_major:1,deltoid_posterior:1,deltoid_lateral:1,biceps_brachii:0.55,brachialis:0.5"
$S/venv/bin/python -I atlas.py pv/bla.npz spec/shared.py spec/back.py spec/leg.py spec/arm.py 2>&1 | grep -v detour | grep PROBLEM
$S/venv/bin/python -I bulge.py pv/bla.npz pv/bla_dome.npz | tail -1
CSMAX=${CSMAX:-0.012} CCSM=${CCSM:-150} LNEAR=${LNEAR:-0.015} NDOT=0.0 DOME=pv/bla_dome.npz $S/venv/bin/python -I bakemaps.py pv/bla.npz ${1:-maps_bla3} 2>&1 | grep -i "error\|trace" -A3
$S/venv/bin/python -I redmap.py pv/bla.npz ${1:-maps_bla3} "$ROW" > /dev/null
$S/venv/bin/python -I stylefields.py pv/bla.npz pv/bla_row2.npz "$ROW" > /dev/null
echo rebuilt
