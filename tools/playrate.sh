#!/bin/bash
# 通關率：三種走法各跑幾輪，統計走到哪一個結局。
# 用法：tools/playrate.sh <輸出目錄> <每種走法幾輪> [同時幾個]
set -u
BASE=${1:?} N=${2:-3} PAR=${3:-3}
mkdir -p "$BASE"
run(){ local pol=$1; local seed=$2; local d="$BASE/$pol-$seed"; mkdir -p "$d"
  OUT=$d POLICY=$pol SEED=$seed timeout 2400 node tools/autoplay.mjs >"$d/stdout.txt" 2>&1
  local t="$d/transcript.txt"; local r=中斷
  grep -q '選「把筆記寫完」' "$t" 2>/dev/null && r=好結局
  [ "$r" = 中斷 ] && grep -q '選「翻到倒數第三頁」' "$t" 2>/dev/null && r=短結局
  local days=$(grep -o '=== 板 第 [0-9]* 天' "$t" 2>/dev/null | tail -1 | grep -o '[0-9]*')
  local outs=$(grep -o '出門 [0-9]* 次' "$t" 2>/dev/null | tail -1 | grep -o '[0-9]*')
  echo "$pol	$seed	$r	第${days:-?}天	出門${outs:-?}次" >> "$BASE/tally.tsv"
}
for pol in notes explore random; do for s in $(seq 1 "$N"); do
  while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do wait -n; done
  run "$pol" "$s" & done; done
wait
echo "=== 通關率"; sort "$BASE/tally.tsv"
awk -F'\t' '{c[$1"\t"$3]++} END{for(k in c) print k"\t"c[k]}' "$BASE/tally.tsv" | sort
