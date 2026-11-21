# 欄位助手（Columns Helper）

本倉庫版本：**2.1.1.1**；上游版本：**2.1.1**；作者：**Comfy.n**；正體中文修訂：**SamLiao & Codex**；授權：**GPL v3**。上游最低需求為 calibre **5.44.0**，本倉庫已在 Windows、calibre **9.19** 驗證下述操作。

## 用途

集中預覽、建立與管理 calibre 自訂欄位。提供快速建立連結、欄位套組、欄位說明與範本預覽、搜尋篩選、上下移動及移到最上／最下方。可開啟 calibre 原生範本測試器，並在已安裝 Calibre Config Reports 時跳到對應欄位報告。

套組包含閱讀器註記與進度、Reading Tracker、Reading Goal、個人書評、作者與網路查詢、Kobo Utilities、一般計數、Count Pages、Book List Plus 和 Cover Size Checker 所需的欄位。

## 安裝與操作

1. 在專案根目錄執行 `python build_release.py`，取得 `dist/Columns Helper-zh_TW-release.zip`。
2. 在 calibre「偏好設定 → 外掛 → 從檔案載入外掛」安裝 ZIP，重新啟動。介面語言設為正體中文後，按鈕顯示「欄位助手」。
3. 如未顯示按鈕，從「偏好設定 → 工具列和選單」加入「欄位助手」。
4. 開啟「瀏覽套組」，選取預設欄位，核對查詢名稱、資料類型、說明與範本，再按「建立選取項目」或「全部建立」。也可直接從主視窗的「快速建立」選單新增。
5. 如需測試範本，先在主書庫選取一本書，再從套組預覽開啟範本測試器。
6. 在主視窗核對欄位與順序，按「套用」儲存；新增欄位等變更會提示重新啟動 calibre。未套用就關閉，尚未儲存的欄位定義不會寫入書庫。

## 正體中文語言包

使用原生 gettext 語言包 [zh_TW.po](./src/translations/zh_TW.po)，共 **323 條**訊息，於統一打包時編譯成 `translations/zh_TW.mo`。補齊上游缺漏並修正誤譯，涵蓋工具列、主視窗、欄位套組、說明、右鍵選單、篩選語法提示及範本相關提示。

新增原本未接入翻譯的套組欄位標題與說明。欄位查詢名稱（如 `#read_progress`）、範本公式、篩選語法與其他外掛使用的值保持原樣；其他語言資源保留。升級不會改名既有書庫欄位，中文標題適用於之後建立的預設欄位。

## 限制

- 套組提供欄位定義，不會安裝對應外掛或自動取得其資料。Kobo 閱讀資訊、Count Pages 統計等仍需由相關外掛填入；上次檢視時間需設定 Job Spy。
- 閱讀進度範本 `reading_progress()` 需要 calibre 9.5 以上，工具提示範本需要 calibre 8.10 以上。外掛最低版本不代表所有套組功能都適用於舊版本。
- 篩選語法使用英文關鍵字，如 `type:text`、`hidden:yes`、`not desc:date`；請勿翻譯關鍵字。
- 同一查詢名稱已存在時會選取既有欄位，不會直接覆蓋其定義。可依書庫需求自行調整欄位標題。
- 刪除自訂欄位會影響該欄位中的書庫資料，操作前應備份書庫。還原預設配置只還原欄位顯示與順序。
- 使用 calibre 原生欄位設定介面並在執行期間擴充其功能；未驗證其他平台、舊版 calibre 與所有第三方外掛組合。

## 來源與驗證

來源為 [MobileRead 官方討論串](https://www.mobileread.com/forums/showthread.php?t=372614) 的 [Columns Helper 2.1.1.zip](https://www.mobileread.com/forums/attachment.php?attachmentid=227373&d=1794643905)，2026-11-22 取得。原包 SHA-256：`179d15ff80027f82f9831c92cd831a7f8dc31a5fdf53b6c5447afe1970f0dbeb`。

Windows、calibre 9.19 使用獨立設定目錄與暫存書庫，安裝實際 ZIP 後通過六項原生 Qt 介面測試：語言包與參數完整性、套組預覽／篩選與原生範本測試器、四種排序按鈕、取消新增欄位、四類欄位建立／套用／避免重複及既有書目保護，以及重新開啟資料庫核對。測試以離屏模式執行；不涉及使用者的正式書庫與設定。未發現上述操作需要額外的 calibre 9.19 核心相容性修正。

重跑測試請先打包，再用新的 `dist/` 子目錄設定 `CALIBRE_CONFIG_DIRECTORY`，設定 `QT_QPA_PLATFORM=offscreen`，依序執行 `calibre-customize -a "dist/Columns Helper-zh_TW-release.zip"` 與 `calibre-debug -e "Columns Helper/tests/test_columns_helper.py"`。結果寫入該隔離目錄的 `test-result.json`；確認 `success` 為 `true`。完整變更見 [CHANGELOG](./CHANGELOG.md)。
