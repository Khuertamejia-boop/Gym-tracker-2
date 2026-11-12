#!/bin/bash
# Male mannequin base with the face and haircut of 12-11-2026 (owner's references: two anatomy illustrations + a photo
# of a skin-fade haircut):  w/NB_mc_row2.blend (body without face)  ->  w/NB_mc_row3.blend (base of every exercise)
#   ./rostro_hombre.sh <human_base_meshes_bundle.blend> [out.blend]        run from the project root, GT3D set
# face: manface.py (squarer jaw and chin, cheekbones, brow ridge, deep-set eyes, narrower nose), calm neutral mouth,
# lower / darker brows, ears closer to the head; hair: skin fade with a lined-up front, darker top with volume and
# grain; eyes: iris with darker rim and fibres, black pupil, catchlight; attributes for the face shading of the renderer.
# The previous face (C + slight smile, buzz cut) is the commented command in restaurar.sh.
set -e
cd "${GT3D:?set GT3D}"; B=${1:?bundle .blend}; O=${2:-w/NB_mc_row3.blend}
MANFACE=1 LIPZ=1.5073 LIPT=0.26 MLINE=0.45 LASHT=0.9 LASHB=0.22 BROWT=0.92 BZB=1.5865 BZT=1.5950 \
  SMILE=${SMILE:-0.0015} SMX=0.013 SMZ=0.010 SMCH=0.0008 LIPDN=${LIPDN:--0.0008} \
  MANSHAPE=1 EARPIN=0.28 HAIRSTYLE=fade HAIRT=${HAIRT:-1.0} HVOL=3 HTOPV=4 FACEATTR=1 EYEV2=1 IRIST=0.80 LIMT=0.18 EYEW=0.40 \
  venv/bin/python -I facebuild.py "$B" w/NB_mc_row2.blend w/NB_mc_row3_pre_aw.blend | grep -E "manface|hair verts|Traceback|Error" || true
# armpit skin weights (11-11-2026): the flank no longer follows the arm, the inner arm no longer follows the torso
venv/bin/python -I armpitweights.py w/NB_mc_row3_pre_aw.blend "$O" > /dev/null
echo "base: $O"
