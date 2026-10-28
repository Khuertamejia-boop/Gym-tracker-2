#!/bin/bash
# Female mannequin bases from the male one (28-10-2026): body (femalebuild.py) + face, bun and eyebrows (facebuild.py)
# + sports top (topbuild.py) -> w/NBF_row3.blend and ill/rest_f.npz.  Pose any exercise with BASEB=NBF_row3.blend and
# render with RESTNPZ=$GT3D/ill/rest_f.npz (and the hair env of ill/style_mujer.env).
#   ./mujer.sh <human_base_meshes_bundle.blend>
S=${GT3D:?set GT3D}; B=$1; cd $S/w
PHYK=${PHYK:-0.25} $S/venv/bin/python -I ../femalebuild.py $B NB_mc_row.blend NBF_row.blend ../ill/rest_f.npz | grep "good\|projected\|height"
SRCBODY=GEO-body_female_realistic RESTNPZ=$S/ill/rest_f.npz CUTZ=1.40 ZOFF=-0.040 HAIRSTYLE=bun HREC=${HREC:--0.010} HVOL=${HVOL:-9} CAPIN=22 HAIRT=${HAIRT:-0.93} IRISA=33 PUPA=11 LASHB=${LASHB:-0.30} LASHT=0.95 HSOFT=0.005 \
  BUNR=${BUNR:-0.042} BUNY=${BUNY:-0.006} BUNZ=${BUNZ:-1.652} BUNFLAT=0.80 $S/venv/bin/python -I ../facebuild.py $B NBF_row.blend NBF_row_h.blend | grep "hair\|clamped"
RESTNPZ=$S/ill/rest_f.npz $S/venv/bin/python -I ../topbuild.py NBF_row_h.blend NBF_row3.blend | grep "top verts"
rm -f NBF_row_h.blend
