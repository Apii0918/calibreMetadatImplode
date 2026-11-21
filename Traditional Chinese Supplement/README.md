# 正體中文補強（Traditional Chinese Supplement）

版本：**1.2.0**；作者：**SamLiao & Codex**；授權：GPL v3；最低 calibre：**9.17.0**。本倉庫自行開發，隨整合版 [v1.3.23](https://github.com/SamLaio/calibreMetadatImplode/releases/tag/v1.3.23) 發行。

## 用途與支援範圍

在 calibre 正體中文介面中，自動補齊指定標籤、按鈕、選單、說明與滑鼠提示。支援主介面與 Edit Book，不顯示額外工具列按鈕。

- 偏好設定涵蓋介面外觀、書架、加入書本、搜尋、自訂欄位、下載中繼資料與儲存至磁碟；補翻延遲建立的選項及子視窗。
- 補齊 43 個調校項目中的 24 個英文說明，以及十種工具列／選單配置和 184 個核心快捷鍵的指定文字。快捷鍵可依中文名稱、原文或按鍵組合搜尋。
- 補翻儲存範本與範本函式頁面的操作說明，以及編輯器的無障礙、拼字、文法、改寫建議、分頁、搜尋與語音朗讀等指定文字。
- 書本檢查已核對 calibre 9.19 九個模組的 196 段可翻譯訊息，另涵蓋 Stylelint 全部 32 條啟用規則的 36 種訊息形式與常見 CSS 語法錯誤。
- 保留原有 KFX、簡繁轉換、EPUBCheck、XTC、Goodreads、FictionDB、databazeknih、DeACSM、DeDRM、LCPL、Open With、EpubSplit 等第三方外掛的指定顯示對照。

## 安裝與使用

1. 從 [v1.3.23 發行頁](https://github.com/SamLaio/calibreMetadatImplode/releases/tag/v1.3.23) 下載 `Traditional Chinese Supplement-zh_TW-release.zip` 對應附件。自行打包請使用根目錄的 `build_release.py`。
2. 在 calibre「偏好設定 → 外掛 → 從檔案載入外掛」安裝。
3. 關閉 Edit Book 並重新啟動 calibre，介面語言設為正體中文後自動生效。

支援 `zh_TW`、`zh_Hant`、`zh_Hant_TW`。停用或移除外掛後重新啟動，即恢復原介面。

## 限制

- 依已知來源及原文精確比對；上游改動文字或介面結構後可能需要更新。主要以 Windows、calibre 9.19 核對，未驗收所有版本與平台。
- 保留書籍、書庫、使用者程式與輸入內容，以及選項內部值、快捷鍵識別字、按鍵綁定和檢查器修復行為。此工具只補翻顯示文字，不會自行修復書本。
- 其他第三方外掛的全部子動作、內建範本函式的個別參考文件、閱讀器及轉換記錄尚未全面翻譯。外部引擎未收錄的原始診斷仍可能是英文。
- 補翻發生 Python 例外時，會記錄並略過該元件。

## 來源與驗證

程式由[本倉庫](https://github.com/SamLaio/calibreMetadatImplode/tree/main/Traditional%20Chinese%20Supplement)維護；對照文字與測試樣本來自 calibre 9.18／9.19 及相關外掛介面。完整版本紀錄見 [CHANGELOG](./CHANGELOG.md)。

2026-11-21 在 Windows、calibre 9.19 通過 12 支隔離測試程式，涵蓋原生元件、動態初始化、範本預覽、完整檢查訊息目錄，以及輸入、設定值與快捷鍵保護。測試請使用 `dist/` 下的獨立設定目錄，避免影響日常設定。
