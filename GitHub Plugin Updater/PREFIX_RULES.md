# 前綴發行來源規則

適用於 GitHub Plugin Updater **0.3**。第一版內建 `https://github.com/kiwidude68/calibre_plugins`，貼入「管理來源」即可使用，不需要該庫提供 `plugins.json`。另支援 AZW6 單庫單外掛規則，其他庫仍走 JSON 模式；本版沒有通用規則編輯器。

## 外掛如何配對

內建 `src/prefixes.py` 保存 25 支外掛的前綴與 calibre 名稱，已於 2026-11-22 靜態核對上游各目錄的 `__init__.py` 宣告；辨識時不執行 GitHub 原始碼。

| 前綴 | calibre 名稱 | 正式標籤與附件範例 |
| --- | --- | --- |
| `manage_series` | Manage Series | `manage_series-1.5.5`、`manage_series-1.5.5.zip` |
| `count_pages` | Count Pages | `count_pages-1.15.3`、`count_pages-1.15.3.zip` |
| `find_duplicates` | Find Duplicates | `find_duplicates-1.10.11`、`find_duplicates-1.10.11.zip` |

標籤規則為 `prefix-數字版號`，數字前可有 `v`，例如 `count_pages-v1.14.1`；附件必須唯一且恰為「標籤.zip」。固定 ID 由來源擁有者與前綴組成，例如 `kiwidude68.manage-series`，不與本倉庫的 `samlaio.manage-series` 合併。

## 查詢與選版

1. 以每頁 100 筆讀取 GitHub Releases API，不使用整庫 `/releases/latest` 當作全部外掛的最新版。
2. 排除草稿、預發行、不符合標籤及未知前綴；按每支前綴分組，再按數字 tuple 選最大版號，不按發布日期或字串排序。
3. 繼續分頁到列表結束；最多掃描 2000 筆，達上限仍未完成就報錯，不把不完整掃描當作最新結果。
4. 最新版本若缺少唯一 ZIP、同版有多個候選發行、digest 格式錯誤或附件網址不屬於該庫，該項顯示錯誤且不可勾選。不猜包，也不偷偷退回舊版；其他可配對項目照常列出。

整個查詢僅下載 JSON，不先下載 ZIP。已實際驗證該庫 247 筆發行，3 頁 JSON 配對 25 支外掛，零配對錯誤。

## SHA 與版號

這類原包通常沒有本倉庫身分檔，因此不套用本倉庫的內容 SHA 作為遠端校驗值；GitHub API 的附件 `digest` 是完整 ZIP SHA，兩種摘要不可混用。

- 首次明確綁定時，記錄本機 ZIP SHA 作附件基準；安裝成功後，記錄新包的完整 ZIP SHA 與本機內容 SHA。
- 已保存的附件基準仍對應目前本機內容，且與遠端 digest 相同：顯示「附件相同」，不再比較版號。
- digest 不同，或首次沒有基準：比較標籤版號，提示可更新、同版／附件變更或可勾選降版。
- GitHub 沒有提供 digest：明確標示「來源未提供附件 SHA」，退回版號判斷；勾選安裝前再提示校驗不足，不以附件 ID、時間或大小冒充 SHA。

## 同名來源

我們與上游的同名外掛分開顯示，原綁定保留，不因新增來源而改綁或自動安裝。calibre 按名稱安裝，不能讓同名的兩個版本並存。明確勾選另一來源並確認後才覆蓋及改綁；同一批勾選同名的兩個來源會被擋下。

切到上游原包可能失去本倉庫的正體中文與修正。這是來源切換，不是把兩支外掛合併或比較兩條分支誰比較新。

## 勾選後的安裝驗證

確認後才下載指定 Release 的 ZIP。若 GitHub 提供 digest，必須對上其 SHA；未提供時僅計算本機 SHA 留存，無法宣稱檔案與作者公布的摘要一致。

仍檢查下載大小、ZIP 結構與解壓限制，並在載入原包程式前備份舊包與登錄。原包不必包含我們的身分 JSON，但實際 `name` 與 `version` 必須符合規則名稱及標籤；實際最低 calibre 與支援平台也必須相容。主分支原始碼不一定代表正式版，因此不拿 main 的宣告取代下載包的相容性檢查。

安裝後保留啟用／停用狀態，更新綁定及 SHA，失敗則回復。已勾選仍可要求同版重裝、降版或來源切換，但不能繞過名稱、版號、相容性與已提供的 digest 校驗。

本版以隔離測試 ZIP 驗證安裝及回復，尚未對真實 kiwidude ZIP 執行安裝；真實庫只做 JSON 查詢與配對驗證。
