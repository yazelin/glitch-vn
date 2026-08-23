#!/usr/bin/env bash
# 把發佈後的 Larch 作品完整玩一次，畫面與聲音一起錄下來。
#
# **Playwright 的 recordVideo 不錄聲音**，所以錄影交給 ffmpeg：
# x11grab 抓 Xvfb 的畫面、pulse 抓一個 null sink 的 monitor。
# 瀏覽器用 PULSE_SINK 導進那個 sink，不會混到桌面其他聲音，
# 也不會被桌面其他聲音污染。
#
# 分段寫檔（每十分鐘一個），中途掛掉只損失一段，最後再無損接起來。
#
#   bash record.sh <發佈網址> [輸出資料夾]
set -euo pipefail
URL="${1:?要給發佈網址}"
OUT="${2:-$HOME/glitch-vn/capture}"
DISP=":77"
SINK="glitchcap"
mkdir -p "$OUT/seg"

cleanup() {
  kill "${FF:-0}" "${XV:-0}" 2>/dev/null || true
  pactl unload-module "${MOD:-0}" 2>/dev/null || true
}
trap cleanup EXIT

MOD=$(pactl load-module module-null-sink sink_name=$SINK \
      sink_properties=device.description=glitchcap)
echo "null sink 建好（module $MOD）"

Xvfb $DISP -screen 0 1280x808x24 -nolisten tcp &
XV=$!
sleep 2

ffmpeg -hide_banner -loglevel error -y \
  -f x11grab -draw_mouse 0 -framerate 25 -video_size 1280x808 -i $DISP.0 \
  -f pulse -i ${SINK}.monitor \
  -vf crop=1280:720:0:88 \
  -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p -g 50 \
  -c:a aac -b:a 160k \
  -f segment -segment_time 600 -reset_timestamps 1 \
  "$OUT/seg/part-%03d.mp4" &
FF=$!
echo "ffmpeg 開錄（PID $FF）"
sleep 2

cd ~/line-sticker-studio
DISPLAY=$DISP PULSE_SINK=$SINK node ~/line-sticker-studio/_play_through.mjs "$URL"

echo "玩完了，收尾"
sleep 3
kill -INT "$FF" 2>/dev/null || true
wait "$FF" 2>/dev/null || true

cd "$OUT/seg"
ls part-*.mp4 | sed "s|^|file '|;s|$|'|" > list.txt
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i list.txt -c copy "$OUT/全書完整版.mp4"
echo "完成：$OUT/全書完整版.mp4"
ffprobe -v error -show_entries format=duration:stream=codec_type -of default=nw=1 "$OUT/全書完整版.mp4"
