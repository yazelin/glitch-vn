#!/usr/bin/env bash
# 在 Wine 底下開 Live2D Cubism Editor 5.3，自動按掉授權對話框。
# 用法：./run-cubism.sh [要開的檔案(Windows 路徑，如 C:\glitch\glitch.psd)]
#
# 授權每次啟動都要重按（Wine 下不會記住），對話框標題是 "Start"，
# 第 4 顆按鈕才是 Start as FREE version。第 3 顆是 42 天 PRO 試用，不要按到。
set -u
export WINEPREFIX="${WINEPREFIX:-$HOME/.wine-cubism}"
export DISPLAY="${DISPLAY:-:1}"
export WINEDEBUG=fixme-all
APP="$WINEPREFIX/drive_c/Program Files/Live2D Cubism 5.3"
LOG="${TMPDIR:-/tmp}/cubism-run.log"

for p in $(pgrep -f 'CECubismEditor[A]pp'); do kill "$p" 2>/dev/null; done
sleep 4

( cd "$APP" && setsid nohup wine CubismEditor5.exe ${1:+"$1"} > "$LOG" 2>&1 < /dev/null & )

# 等 "Start" 對話框，按第 4 顆
echo "等授權對話框…"
for i in $(seq 1 60); do
  sleep 2
  FRAME=$(xwininfo -root -children 2>/dev/null | grep -E '"Start":' | grep -oE '^ *0x[0-9a-f]+' | tr -d ' ')
  [ -n "$FRAME" ] || continue
  CID=$(xwininfo -id "$FRAME" -children 2>/dev/null | grep 'java\.exe' | grep -oE '0x[0-9a-f]+' | head -1)
  [ -n "$CID" ] || continue
  eval "$(xwininfo -id "$CID" | awk '
    /Absolute upper-left X/{print "AX="$NF}
    /Absolute upper-left Y/{print "AY="$NF}
    /^  Width/{print "W="$NF}
    /^  Height/{print "H="$NF}')"
  # 第 4 顆按鈕在對話框的 (49.9%, 77.2%)
  BX=$(( AX + W * 499 / 1000 )); BY=$(( AY + H * 772 / 1000 ))
  ORIG=$(xdotool getmouselocation --shell | grep -E '^(X|Y)=' | cut -d= -f2 | tr '\n' ' ')
  echo "按 Start as FREE version @ $BX,$BY"
  # 一定要先給焦點：沒有 windowactivate 的話點下去不會生效
  xdotool windowactivate "$FRAME" 2>/dev/null; sleep 1
  xdotool mousemove "$BX" "$BY"; sleep 1; xdotool click 1
  sleep 3
  xdotool mousemove $ORIG
  break
done

# 按完 FREE 還有第二個對話框 "Confirm"：Welcome! Start as FREE version...，要按 OK
echo "等 Confirm 對話框…"
for i in $(seq 1 30); do
  sleep 2
  CF=$(xwininfo -root -children 2>/dev/null | grep -E '"Confirm":' | grep -oE '^ *0x[0-9a-f]+' | tr -d ' ')
  [ -n "$CF" ] || continue
  CC=$(xwininfo -id "$CF" -children 2>/dev/null | grep 'java\.exe' | grep -oE '0x[0-9a-f]+' | head -1)
  [ -n "$CC" ] || continue
  eval "$(xwininfo -id "$CC" | awk '
    /Absolute upper-left X/{print "AX="$NF}
    /Absolute upper-left Y/{print "AY="$NF}
    /^  Width/{print "W="$NF}
    /^  Height/{print "H="$NF}')"
  OX=$(( AX + W*849/1000 )); OY=$(( AY + H*852/1000 ))   # OK 鈕在 (84.9%, 85.2%)
  ORIG=$(xdotool getmouselocation --shell | grep -E '^(X|Y)=' | cut -d= -f2 | tr '\n' ' ')
  echo "按 OK @ $OX,$OY"
  xdotool windowactivate "$CF" 2>/dev/null; sleep 1
  xdotool mousemove "$OX" "$OY"; sleep 1; xdotool click 1
  sleep 2; xdotool mousemove $ORIG
  break
done

# 匯入 PSD 會跳 "Model settings" 問要怎麼處理，預設第一項 Create new model，按 OK
echo "等 Model settings…"
for i in $(seq 1 45); do
  sleep 2
  MS=$(xwininfo -root -children 2>/dev/null | grep -E '"Model settings":' | grep -oE '^ *0x[0-9a-f]+' | tr -d ' ')
  [ -n "$MS" ] || continue
  MC=$(xwininfo -id "$MS" -children 2>/dev/null | grep 'java\.exe' | grep -oE '0x[0-9a-f]+' | head -1)
  [ -n "$MC" ] || continue
  eval "$(xwininfo -id "$MC" | awk '
    /Absolute upper-left X/{print "AX="$NF} /Absolute upper-left Y/{print "AY="$NF}
    /^  Width/{print "W="$NF} /^  Height/{print "H="$NF}')"
  KX=$(( AX + W*417/1000 )); KY=$(( AY + H*945/1000 ))
  ORIG=$(xdotool getmouselocation --shell | grep -E '^(X|Y)=' | cut -d= -f2 | tr '\n' ' ')
  echo "按 OK（Create new model from PSD）@ $KX,$KY"
  xdotool windowactivate "$MS" 2>/dev/null; sleep 1
  xdotool mousemove "$KX" "$KY"; sleep 1; xdotool click 1
  sleep 3; xdotool mousemove $ORIG
  break
done

for i in $(seq 1 60); do
  T=$(xwininfo -root -children 2>/dev/null | grep -oE '"Live2D Cubism Editor[^"]*"' | head -1)
  case "$T" in *"FREE version"*) echo "就緒: $T"; exit 0;; esac
  sleep 2
done
echo "逾時: $(xwininfo -root -children 2>/dev/null | grep -oE '"Live2D Cubism Editor[^"]*"' | head -1)"
exit 1
