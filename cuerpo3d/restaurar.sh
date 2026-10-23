#!/bin/bash
# Restore the 3D mannequin project into a working folder, ready to pose and render.
#   ./restaurar.sh [folder]          (default: $HOME/cuerpo3d-trabajo)
# Afterwards, in every new terminal:   export GT3D=<folder>
set -e
SRC=$(cd "$(dirname "$0")" && pwd); DST=$(mkdir -p "${1:-$HOME/cuerpo3d-trabajo}" && cd "${1:-$HOME/cuerpo3d-trabajo}" && pwd)
cp -a "$SRC"/. "$DST"/; cd "$DST"; export GT3D="$DST"
mkdir -p w/r ill/r out
if [ ! -x venv/bin/python ]; then
  ${PY:-python3.13} -m venv venv; venv/bin/pip install -q -r requirements.txt
fi
# texture maps of the approved exercises (bent-over row, face pull, deadlift)
ill/mapas.sh maps_v5 "trapezius:1,latissimus_dorsi:1,infraspinatus:1,teres_major:1,teres_minor:1,rhomboid_major:1,deltoid_posterior:1,deltoid_lateral:1"
ill/mapas.sh maps_fp2 "deltoid_posterior:1,trapezius:1,rhomboid_major:1,infraspinatus:1,teres_minor:1"
ill/mapas.sh maps_dl "gluteus_maximus:1,biceps_femoris:1,semitendinosus:1,semimembranosus:1,erector_spinae:1"
echo "Listo. En cada terminal nueva:  export GT3D=$DST"
