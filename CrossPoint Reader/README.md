# CrossPoint Reader

本倉庫版本：**0.2.8.2**；上游基準：**0.2.8**；作者：**CrossPoint Reader**；本地修訂：SamLiao & Codex；授權：**MIT**；最低 calibre：**9.19.0**。本倉庫於 Windows、calibre **9.19** 驗證下述流程。

## 用途與操作

將 CrossPoint 韌體的閱讀器作為 calibre 無線裝置，讀取 EPUB 書單、傳送及刪除書籍。這不是 USB 大量儲存裝置驅動。

1. 執行根目錄 `python build_release.py`，安裝 `dist/CrossPoint Reader-zh_TW-release.zip`，重新啟動 calibre。同名外掛會取代舊版；若先前停用，請先在外掛偏好設定啟用。
2. 讓電腦與閱讀器位於同一可互通的網路，在閱讀器開啟檔案傳輸／calibre 無線模式。
3. 從外掛偏好設定調整主機、WebSocket 連接埠與上傳路徑；預設為 `192.168.4.1`、`81`、`/`。HTTP 檔案服務使用閱讀器的連接埠 80。
4. 驗證成功後才顯示裝置介面，接著使用 calibre「傳送到裝置」。上游的 EPUB 最佳化保留為選用功能，預設關閉，不會自動啟用改圖或改寫排版。
5. 退出／停止外掛後，本次執行不會立即自動重連；從 calibre 的連線控制重新啟動，或重新啟動 calibre 後恢復偵測。

## 本次上游更新

2026-11-23 同步上游 0.2.8 的後續提交 `54f73d7`，新增 EPUB 拆分前後的閱讀位置對照檔，保留 OPF 命名空間、spine 屬性與內文空白；寫入失敗時保留不可用標記，避免沿用過期位置。韌體須支援此對照格式，才能使用位置換算。

## 本地修正

- 舊 0.1.0 接受任何 UDP 回覆，未確認檔案服務便回報連接。新版辨識 CrossPoint 探索回覆及有效連接埠，並確認 `/api/files` 能回傳正確格式，才宣告裝置存在。
- 連線期間約每五秒檢查檔案服務；離線或讀取失敗時清除連線狀態並暫停重試十秒，避免持續誤切裝置介面。
- 書單讀取失敗會明確報錯，不當作空書庫；採用上游目前的 calibre 原生 BookList，避免舊版清單型別不符。
- 修正退出／停止後仍繼續探索，以及探索 socket 未確實關閉的問題。沿用上游設定鍵，保留主機與傳輸選項。

## 限制與驗證

UDP 探索需要區域網路廣播可達；VPN、訪客 Wi-Fi、AP 隔離、防火牆或未開啟閱讀器服務都可能阻擋連線。真實網路在驗證後仍可能中斷，無法保證傳輸期間永遠連線。設定、傳輸進度、摘要、錯誤及文字最佳化提示已加入 134 條原生正體中文翻譯；設定鍵、裝置型號、檔名、通訊指令及參數保持原樣。

2026-11-22 在 Windows、calibre 9.19 重現舊版接受非閱讀器回覆及未驗證就宣告連接；修正版通過 **7 項連線測試及 4 項語言／設定／協定測試**，包含不相關／損壞 UDP、有效回覆、格式錯誤、逾時、服務消失、冷卻、退出／重新啟動、原生書單及實際本機 HTTP 伺服器。使用 `dist/` 下的隔離設定；未以實體 X3／X4、實際無線傳輸或其他平台驗收。

2026-11-23 新增上游位置對照回歸測試，8 項通過，原有 7 項連線及 4 項語言／設定／協定測試亦通過；選用的 Gutenberg EPUB 案例因來源網站維護而未驗證。

先打包，以獨立 `CALIBRE_CONFIG_DIRECTORY` 設定目錄執行 `calibre-debug -e "CrossPoint Reader/tests/test_presence.py"`。測試不接觸正式設定或閱讀器。

## 來源

[crosspoint-reader/calibre-plugins v0.2.8](https://github.com/crosspoint-reader/calibre-plugins/tree/54f73d7e31dedc66c987ba3801fce92d286eccfa)，固定提交 `54f73d7e31dedc66c987ba3801fce92d286eccfa`。通訊格式對照[韌體端點文件](https://github.com/crosspoint-reader/crosspoint-reader/blob/master/docs/webserver-endpoints.md)。上游英文說明保留於安裝包內 `UPSTREAM_README.md`；變更見 [CHANGELOG](./CHANGELOG.md)。
