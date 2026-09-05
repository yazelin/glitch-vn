# 精修：閉眼與開口素材

`22_lid_R`、`23_lid_L`、`42_mouth_A` 原本是程式合成的測試素材（眼皮是平塗加一道弧、開口是個橢圓）。
這裡是換成正式素材的做法，可重跑。

- `in_geo.webp`：原圖臉部（1x 座標 170,170–380,380 放大到 840），幾何來源。
- `in_style_laugh.webp`：`art/face/face-glitch-laugh.png` 的頭部，畫風錨——正典的閉眼與張嘴。
- `out_closed.webp`／`out_mouth.webp`：`.11` codex-image-service 的輸出（本機 codex 當時沒點數）。
  prompt 要求「只改眼睛／只改嘴，其餘像素不動」，**模型照樣把整張臉重畫**（瀏海走位、臉略放大），
  所以後面只取小區域。
- `patch.py mouth out_mouth.webp`：整臉 ECC 仿射對齊（0.991 通過）→ 取嘴附近跟原圖差異明顯的區域當 alpha。
- `patch.py closed out_closed.webp`：**ECC 對不了睜眼 vs 閉眼**（本來就該不一樣，整臉只有 0.73、每眼視窗 0.15）。
  改抓生成圖裡兩道深色扁長 blob（眼皮線），量中心與寬度做相似變換對到已知眼睛中心，
  **只把深色線條當遮罩疊到既有的 `10_face_base` 膚色上**——不貼皮膚就沒有接縫、沒有外來髮絲、不用對膚色。
  線條遮罩限制在 blob 外擴一圈內，免得髮絲輪廓也被當成線。

驗收：三張新層疊回休息姿態，裁臉放大看接縫（`layers_out` 預覽）。產出已複製進 `../layers/`，
`../mkpsd.py` 組出的 PSD 同步到 `glitch-l2d/source/glitch.psd`。
