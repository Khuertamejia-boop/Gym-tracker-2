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
# body v2 (28-10-2026, approved by the owner): upper trapezius and pectorals a little smaller -> w/NB_mc_row2.blend
(cd w && SHRINK="trap_upper:10,pec_clavicular:8,pec_sternal:8" ../venv/bin/python -I ../shrink.py NB_mc_row.blend NB_mc_row2.blend > /dev/null)
# body v3 (28-10-2026): face. The original head of the Blender "Human Base Meshes" realistic male (CC0) -> w/NB_mc_row3.blend
HBM=$DST/hbm; mkdir -p $HBM
[ -f $HBM/human_base_meshes_bundle.blend ] || (cd $HBM && curl -sSL https://mirror.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip -o hbm.zip && unzip -q -j -o hbm.zip '*/human_base_meshes_bundle.blend' && rm -f hbm.zip)
(cd w && ../venv/bin/python -I ../facebuild.py $HBM/human_base_meshes_bundle.blend NB_mc_row2.blend NB_mc_row3.blend > /dev/null)
# texture maps of the approved exercises (bent-over row, face pull, deadlift)
ill/mapas.sh maps_v5 "trapezius:1,latissimus_dorsi:1,infraspinatus:1,teres_major:1,teres_minor:1,rhomboid_major:1,deltoid_posterior:1,deltoid_lateral:1"
ill/mapas.sh maps_fp2 "deltoid_posterior:1,trapezius:1,rhomboid_major:1,infraspinatus:1,teres_minor:1"
NONEFIX=1 ill/mapas.sh maps_row3 "trapezius:1,latissimus_dorsi:1,infraspinatus:1,teres_major:1,teres_minor:1,rhomboid_major:1,deltoid_posterior:1,deltoid_lateral:1"
ill/mapas.sh maps_dl "gluteus_maximus:1,biceps_femoris:1,semitendinosus:1,semimembranosus:1,erector_spinae:1"
NONEFIX=1 ill/mapas.sh maps_curl2 "biceps_brachii.L:1,brachialis.L:1,brachioradialis.L:1"
echo "Listo. En cada terminal nueva:  export GT3D=$DST"
