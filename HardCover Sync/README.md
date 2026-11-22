# Hardcover Sync

版本：**0.4.0.2**；原作者：**Juan York**；授權：GPL v3；最低 calibre：**7.7.0**。基於上游 **0.4.0** 的第二次本倉庫修訂。

## 用途

與 Hardcover 同步清單、評分、書評、閱讀狀態、筆記與引文，並可從書籍內文擷取 ISBN。

執行根目錄 `python build_release.py` 取得 `dist/Hardcover Sync-zh_TW-release.zip`，或從[本倉庫發行頁](https://github.com/SamLaio/calibreMetadatImplode/releases)取得對應附件。

## 安裝與使用

1. 在根目錄執行 `python -B build_release.py`，取得 `dist/Hardcover Sync-zh_TW-release.zip`。
2. 在 calibre「偏好設定 → 外掛 → 從檔案載入外掛」安裝並重新啟動。
3. 在「偏好設定 → 外掛」自訂此外掛；依需要從「工具列與選單」加入按鈕，再設定帳號、欄位與同步方向。

若舊安裝出現兩個 Goodreads Sync，先核對並移除誤標為 HardCover 的 **Goodreads Sync 1.16.11**，再安裝真正的 Hardcover Sync。勿將兩個服務的帳號或 API 金鑰混用。

此外掛直接提供中文，不依賴「正體中文補強」外掛。

## 本倉庫修改

- 採用上游 GitHub 0.4.0，保留 ISBN 版本連結與 API 錯誤提示；提供 178 個訊息目錄項目及三種正體中文語系名稱。
- 維持上游 `hardcover_sync` 名稱空間、API 欄位與設定鍵，與 Goodreads Sync 可同時安裝；本地版號為 0.4.0.1。
- 原本名為 `HardCover Sync.zip` 的檔案其實是 Goodreads Sync 1.16.11。本專案沒有把那包舊 Goodreads 程式當作 Hardcover 發行。
- 驗證獨立載入、中文設定頁、API 金鑰／限流／自動上傳設定儲存，以及與 Goodreads Sync 共存。

## 來源

[原始專案／討論串](https://github.com/jojuyo/calibre-hardcover-sync-plugin)。匯入日期：2026-11-09。

本版來源：[上游 0.4.0 發行頁](https://github.com/jojuyo/calibre-hardcover-sync-plugin/releases/tag/hardcover-sync-0.4.0)。先前 0.3.1.1 使用 calibre 官方外掛索引的 0.3.1。

## 測試與限制

本版在 Windows、calibre 9.18.0 通過 9 項測試：外掛載入、設定保存、Qt 選擇視窗、ISBN 與 Hardcover 識別碼寫入測試書庫、模擬 API 成功及錯誤回應，以及翻譯格式與語系別名。上述為 0.4.0.1 的既有測試範圍。

已使用本機儲存的 API 金鑰，在 calibre 9.18.0 成功驗證帳號並讀取真實清單、評分、閱讀狀態及書評；未執行遠端寫入或日常書庫回寫。

同步會變更書庫或遠端資料，請先備份並核對方向。自動化測試使用獨立設定與測試書庫並封鎖網路；另有真實帳號唯讀測試，尚未驗收雙向遠端寫入與所有主視窗操作。

```powershell
$env:CALIBRE_CONFIG_DIRECTORY = Join-Path $PWD 'dist/standalone-qa/config'
$env:QT_QPA_PLATFORM = 'offscreen'
calibre-debug -e "HardCover Sync/tests/test_hardcover_sync.py"
calibre-debug -e "HardCover Sync/tests/test_040_compatibility.py"
python -B "HardCover Sync/tests/test_catalog.py"
```

Windows 注意：若 `HardCover Sync` 與 `Hardcover Sync` 兩筆紀錄指向同一檔案，不要直接刪除其中一個安裝包。先關閉 calibre 並備份設定，再清除舊大小寫名稱的重複登記，保留新版 ZIP 與帳號資料。

2026-11-22 的 0.4.0.2 在 Windows、calibre 9.19 重現並修正首次欄位確認期間關閉／切換書庫後仍還原快取的錯誤。13 項隔離測試通過；原生主視窗在舊版重現相同例外，新版提前關閉與正常確認兩種流程均無例外。未使用正式書庫或執行遠端寫入。新增測試為 `tests/test_initialization_lifecycle.py` 與 `tests/test_gui_shutdown.py`；後者需先在新的 `dist/` 設定目錄安裝 ZIP。
