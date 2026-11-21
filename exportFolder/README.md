# Export Folder 1.2.2

在 calibre 書庫右鍵選「匯出到…」，將選取的書直接儲存到預設資料夾。適用於 Windows 版 calibre 9.18 以上。

1. 在「偏好設定 → 外掛」從檔案載入 [Export Folder 安裝包](https://github.com/SamLaio/calibreMetadatImplode/releases/download/v1.3.20/Export.Folder-zh_TW-release.zip)，重新啟動 calibre。
2. 在書庫右鍵選「匯出到… → 管理輸出資料夾…」。按「新增」並輸入名稱，例如「小說」。雙擊路徑欄貼上完整路徑，或選取該列後按「瀏覽…」。可編輯或刪除多筆，按「儲存」套用。
3. 選取一本或多本書，右鍵選「匯出到… → 小說」，直接匯出到該路徑。可從「偏好設定 → 工具列與選單」調整入口位置。

點「輸出範本」會開啟正體中文編輯視窗，提供三行高的輸入區和即時檔名預覽。點「格式優先順序」可從下拉候選選擇格式，新增到清單後拖曳排序，也可移除格式。預設使用 `{title} - {authors}` 和 `EPUB > PDF`。範本採用 calibre 語法，可用 `/` 建立子資料夾，副檔名由匯出的格式決定。

範本編輯視窗下方列出可用變數與正體中文說明。按兩下變數可插入目前游標位置，或取代已選取的文字。自訂欄位請使用書庫中以 `#` 開頭的查詢名稱。

每本書依序選第一個已有的格式。有 EPUB 就匯出 EPUB，只有 PDF 就匯出 PDF。兩種都沒有時會跳過該書並列入匯出報告。每本只輸出一個電子書檔案，封面、OPF 和附加資料檔不另外輸出。

目的地由同一個 calibre 使用者的各書庫共用。輸出資料夾必須已存在，且位於目前書庫之外。外掛沿用 calibre 原生匯出引擎，無須修改 calibre 本體。

本倉庫自行開發，作者為 SamLiao & Codex。[calibre 原生匯出入口](https://github.com/kovidgoyal/calibre/blob/v9.18.0/src/calibre/gui2/actions/save_to_disk.py)


## calibre 9.19 相容性

2026-11-21 在 Windows、calibre 9.19，以獨立設定目錄與暫存資料驗證。在暫存書庫實際匯出 EPUB／PDF，確認逐本格式優先順序、檔名範本與範本編輯視窗。實際裝置傳輸與所有第三方外掛組合尚待驗證。
