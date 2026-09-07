#!/usr/bin/env bash
# 從原圖重建全部圖層並套所有修補，任何一步驗證失敗就停（不會留下半套狀態）。
# 在 art/live2d 目錄跑：bash refine/rebuild_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python3 build.py | tail -1
python3 refine/patch.py closed refine/out_closed.webp | tail -2
python3 refine/patch.py mouth  refine/out_mouth.webp  | tail -1
cp layers_out/22_lid_R.png layers_out/23_lid_L.png layers_out/42_mouth_A.png layers/
python3 refine/shift_mouth.py
python3 refine/split_sleeve.py
python3 refine/head_mask.py
python3 refine/fix_head_hands.py
python3 mkpsd.py | tail -1
cp glitch.psd "$HOME/glitch-l2d/source/glitch.psd"; cp glitch.psd "$HOME/.wine-cubism/drive_c/glitch/glitch-refined.psd"
echo "rebuild_all 完成，PSD 已複製到 glitch-l2d/source 與 Wine"
