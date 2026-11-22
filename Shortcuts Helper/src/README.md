# 快捷鍵助手（Shortcuts Helper）

本倉庫版本：**1.1.0.1**；作者：**Comfy.n**；正體中文與本地修訂：SamLiao & Codex；授權：**GPL v3**；最低 calibre 宣告：**5.44.0**。官方附件名稱為 1.1，程式數字基準為 **1.1.0**，故本倉庫追加 `.1`。

## 用途與操作

快速開啟 calibre 的快捷鍵偏好設定，或顯示目前已指定快捷鍵的清單。

1. 執行根目錄 `python build_release.py`，安裝 `dist/Shortcuts Helper-zh_TW-release.zip`，重新啟動 calibre。
2. 將介面語言設為正體中文；若工具列沒有顯示「快捷鍵助手」，在「偏好設定 → 工具列和選單」加入。
3. 點擊工具列按鈕執行預設動作。從下拉選單直接開啟「快捷鍵偏好設定」、「目前快捷鍵」或外掛設定；設定頁可選擇直接點擊的預設動作。
4. 目前快捷鍵清單提供動作、群組、預設及目前按鍵四欄，可搜尋、排序及標示自訂按鍵；關閉時保存視窗大小與欄寬。

清單只顯示目前有指定按鍵的動作；這是檢視工具，不能在表格內改綁定。變更快捷鍵請使用 calibre 原生設定頁。其他外掛所提供的動作／群組名稱沿用其文字，不改寫按鍵、設定識別碼或自訂名稱。

## 正體中文與修正

新增 **25 條原生 gettext 翻譯**，涵蓋工具列、設定、清單、篩選、排序及滑鼠提示；`.po` 在打包時編譯為 `.mo`，不放入安裝包。保留原作者、圖示與外掛識別。

修正 Qt 6 深淺色判定、排序時填表可能造成欄位配對錯誤、刷新時重複連接表頭事件，以及自訂快捷鍵標記在排序後遺失的問題；保持設定值 `prefs`／`current` 不變。移除上游包中誤放的巢狀 ZIP，不納入發行附件。

2026-11-22 在 Windows、calibre **9.19** 通過 **4 項隔離測試**與原生主視窗驗證，涵蓋中文、排序／篩選、列資料與自訂標記、設定保存、兩種動作路由、真實快捷鍵清單與原生快捷鍵設定頁。沒有修改正式書庫或快捷鍵綁定；其他平台、舊版 calibre 與所有其他外掛組合未實測。

先打包，使用 `dist/` 下的獨立 `CALIBRE_CONFIG_DIRECTORY`，設定 `QT_QPA_PLATFORM=offscreen`，執行 `calibre-debug -e "Shortcuts Helper/tests/test_shortcuts_helper.py"`。原生主視窗腳本為 `tests/test_gui.py`，執行前需在該隔離目錄安裝 ZIP。

## 來源

[MobileRead 官方討論串](https://www.mobileread.com/forums/showthread.php?t=372349)及[官方 1.1 附件](https://www.mobileread.com/forums/attachment.php?attachmentid=221928&d=1774065646)，2026-11-22 取得。原包 SHA-256：`9062c0dfb2cf7d02a6b54e9885ef490496d87ba66a4631cfe2fcb0a06654de9d`。完整變更見 [CHANGELOG](./CHANGELOG.md)。
