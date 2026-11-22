# calibreMetadatImplode

本專案將二十二個 calibre 外掛並排維護，整合上游程式、正體中文資源與本地修正。各外掛可獨立使用；操作、設定、限制、安裝與打包方式請點各外掛名稱閱讀其 README。

外掛首次加入、歷次升級與整合發行紀錄見 [CHANGELOG](./CHANGELOG.md)。

## 本專案來源、版號與修改點

| 項目 | 說明 |
| --- | --- |
| 專案來源 | [SamLaio/calibreMetadatImplode](https://github.com/SamLaio/calibreMetadatImplode)，本倉庫為整合與修訂來源；各外掛的原作者及授權保留於各自目錄。 |
| 整合發行版號 | **[v1.3.25（2026-11-22）](https://github.com/SamLaio/calibreMetadatImplode/releases/tag/v1.3.25)**。這是整套發行附件的版號，與各外掛在 calibre 顯示的版號分開管理。 |
| 專案層修改 | 將外掛整理為各自的 `src/`，使用 `build_release.py` 統一輸出二十二個獨立安裝包到 `dist/`；排除隱藏檔、快取及 `.po` 翻譯來源。Columns Helper、Diaps Editing Toolbag、Extract ISBN、Generate Cover、Goodreads Sync、Hardcover Sync 與 Manage Series 的翻譯在打包時分別編譯。 |
| 本次變更 | 新增 Plugin Backup 0.1、Columns Helper 2.1.1.1 與 Diaps Editing Toolbag 0.5.0.1；訂定「完整上游基準版號加本倉庫修訂次數 `.x`」慣例；統一 AZW6 Image Merge、Count Pages、EpubSplit、Find Duplicates、Goodreads 與 Send to Kindle 六支外掛的程式版號與內外說明。 |

## 外掛版號慣例

有上游來源的外掛，本倉庫版號一律採「完整上游基準版號.x」：完整保留上游所有數字段，不修改、截短或假設固定段數；最後另加一段本倉庫修訂次數，從 `.1` 起，同一上游基準每次本地改版依序遞增為 `.2`、`.3`。例如上游 `1.5.0.1.0`，本倉庫第二次修訂為 `1.5.0.1.0.2`。更換上游基準後，修訂次數從 `.1` 重新計算。程式宣告、介面、內外層 README、更新紀錄與發行說明必須一致；上游來源欄保留原始基準版號，歷史發行紀錄不回改。自有外掛及整合發行版號各自管理。

## 各外掛簡介、來源與版號

以下先列本倉庫自有外掛，再列有上游來源的外掛，各組依名稱字母升序排列；修改摘要採相同順序。

文件核對日期：**2026-11-22**。二十二支外掛的名稱、作者、版號、安裝包與本地說明已對照目前程式；上游採表列固定基準，歷次上游更新與整合紀錄見 [CHANGELOG](./CHANGELOG.md)。

| 外掛及完整說明 | 簡介 | 上游來源與比對基準 | 本倉庫版號 |
| --- | --- | --- | --- |
| [Embed Metadata Safe](./Embed%20Metadata%20Safe/README.md) | 清理 EPUB 的特定損壞自訂欄位資料，再嵌入書庫中繼資料。 | [本倉庫自有外掛](./Embed%20Metadata%20Safe/)，作者為 SamLiao 及 codex；沒有獨立上游。 | **1.0.1**；修正 ZIP 安裝層級並縮短按鈕名稱。 |
| [Enhanced Search and Replace](./Enhanced%20Search%20and%20Replace/README.md) | Edit Book 全書文字類型勾選搜尋、定位與取代。 | 本倉庫自行開發；SamLiao & Codex，API 查核 Calibre v9.0.0／v9.17.0。 | **1.2.0**；原始碼逐字取代、錯誤摘要；原始碼搜尋、背景進度與取消、篩選排序，預設十五行並附操作截圖。 |
| [Export Folder](./exportFolder/README.md) | 從書庫右鍵選單直接匯出到預設資料夾。 | 本倉庫自行開發，SamLiao & Codex。 | **1.2.2**。 |
| [Plugin Backup](./Plugin%20Backup/README.md) | 勾選或一次全部匯出／批次匯入第三方外掛與啟用狀態，可選是否包含設定；入口位於外掛偏好設定底部。 | 本倉庫自行開發，SamLiao & Codex。 | **0.1**。 |
| [Toolbar Manager](./Toolbar%20Manager/README.md) | 右鍵調整工具列按鈕，開啟外掛首頁、選項或移除外掛。 | 本倉庫自行開發；SamLiao & Codex。 | **1.0.0**。 |
| [Traditional Chinese Supplement](./Traditional%20Chinese%20Supplement/README.md) | 補齊指定官方與第三方外掛視窗的正體中文顯示文字。 | 本倉庫自行開發；SamLiao & Codex，核對 calibre 9.18／9.19 與相關外掛介面。 | **1.2.0**；擴充偏好設定、動態視窗、快捷鍵、範本與書本檢查翻譯，無額外工具列按鈕。 |
| [AZW6 Image Merge](./AZW6%20Image%20Merge/README.md) | 將 Amazon AZW6 sidecar 高畫質圖片合併至主書檔。 | Andrew Timson；[HamsterExAstris/calibre-azw6-image-merge，提交 `63f76d4`](https://github.com/HamsterExAstris/calibre-azw6-image-merge/tree/63f76d46e19de901536b9bc7c1a02998f26c439b)，基準 **1.0.0**。 | **1.0.0.1**，本倉庫修訂版。 |
| [Columns Helper](./Columns%20Helper/README.md) | 預覽、建立及管理自訂欄位與套組，提供範本測試、篩選及排序。 | Comfy.n；[MobileRead 官方討論串](https://www.mobileread.com/forums/showthread.php?t=372614)，2026-11-22 取得官方 **2.1.1** 安裝包。 | **2.1.1.1**；原生正體中文修訂版，已驗證 calibre 9.19。 |
| [Count Pages](./Count%20Pages/README.md) | 計算或下載頁數、字數與可讀性統計，寫入自訂欄位。 | Grant Drake；[kiwidude68/calibre_plugins/count_pages，提交 `d46d919`](https://github.com/kiwidude68/calibre_plugins/tree/d46d9197ac2f78e98f2a774a6afbf8d54d9ce68a/count_pages)，基準 **1.15.3**。 | **1.15.3.1**，本倉庫修訂版。 |
| [Diaps Editing Toolbag](./Diaps%20Editing%20Toolbag/README.md) | 在編輯書本中批次編輯 HTML 標籤、轉換西文智慧標點及 CSS cm／em 單位。 | DiapDealer（Doug Massay）；[dougmassay/toolbag-calibre-plugin，提交 `4589e1a`](https://github.com/dougmassay/toolbag-calibre-plugin/tree/4589e1ad30421d1a7698fc26464cb20336a61771)，基準 **0.5.0**。 | **0.5.0.1**；正體中文與 calibre 9.19 相容性修訂。 |
| [EpubSplit](./EpubSplit/README.md) | 按目錄或章節將 EPUB 拆成多本新書。 | Jim Miller；[JimmXinu/EpubSplit，標籤 `v3.12.0`](https://github.com/JimmXinu/EpubSplit/tree/a0b31ea9c0c9b439329574c4752b24eaaab67f72)，基準 **3.12.0**。 | **3.12.0.1**，本倉庫修訂版。 |
| [Extract ISBN](./Extract%20ISBN/README.md) | 從電子書內文擷取 ISBN，確認後更新書庫識別碼。 | Grant Drake；[kiwidude68/calibre_plugins/extract_isbn，提交 `2a2dbb2`](https://github.com/kiwidude68/calibre_plugins/tree/2a2dbb2469ec6e68179cd71ba943db240045d097/extract_isbn)，程式宣告 **1.6.7**。 | **1.6.7.1**，基於上游 1.6.7 的本倉庫修訂版。 |
| [Find Duplicates](./Find%20Duplicates/README.md) | 依書目規則找重複書籍，也支援格式檔案的二進位比對。 | Grant Drake；[kiwidude68/calibre_plugins/find_duplicates，提交 `91b0f23`](https://github.com/kiwidude68/calibre_plugins/tree/91b0f23da54fa8f020ba387e1f13a1321706c0ff/find_duplicates)，基準 **1.10.11**；早期來源為 JimmXinu 分支。 | **1.10.11.1**，本倉庫修訂版。 |
| [Generate Cover](./Generate%20Cover/README.md) | 用圖片與書目資料製作自訂封面。 | Grant Drake；[kiwidude68/calibre_plugins/generate_cover](https://github.com/kiwidude68/calibre_plugins/tree/cd41919f50ce650c45f652f05bbb4327f243a171/generate_cover)，基準 2.5.4。 | **2.5.4.2**，正體中文修訂版。 |
| [Goodreads](./Goodreads/README.md) | 從 Goodreads 下載書籍中繼資料與封面。 | Grant Drake；最初由使用者提供的 1.10.0 安裝包匯入，已對照 [kiwidude68/calibre_plugins/goodreads，提交 `2a2dbb2`](https://github.com/kiwidude68/calibre_plugins/tree/2a2dbb2469ec6e68179cd71ba943db240045d097/goodreads)，基準 **1.10.0**。 | **1.10.0.1**，本倉庫修訂版。 |
| [Goodreads Sync](./Goodreads%20Sync/README.md) | 同步 Goodreads 書架、評分、書評與閱讀進度。 | Grant Drake；[上游](https://github.com/kiwidude68/calibre_plugins/tree/main/goodreads_sync)，本機安裝包基準 **1.17.6**。 | **1.17.6.1**，直接正體中文化，保留原同步核心。 |
| [Hardcover Sync](./HardCover%20Sync/README.md) | 同步 Hardcover 清單與閱讀資料，擷取書籍 ISBN。 | Juan York；[jojuyo/calibre-hardcover-sync-plugin](https://github.com/jojuyo/calibre-hardcover-sync-plugin)，上游 GitHub 發行基準 **0.4.0**。 | **0.4.0.1**，真正的 Hardcover 外掛，直接正體中文化。 |
| [Manage Series](./Manage%20Series/README.md) | 集中調整系列名稱、順序、整數及小數編號，支援鎖定與自訂系列欄位。 | Grant Drake；[kiwidude68/calibre_plugins/manage_series，提交 `c01cf614`](https://github.com/kiwidude68/calibre_plugins/tree/c01cf614f0c6da3c996d7010a0fbba4a68623f66/manage_series)，基準 **1.5.5**。 | **1.5.5.1**；原生正體中文語言包與 calibre 9.19 相容性修訂。 |
| [Markdown Output](./Markdown%20Output/README.md) | 將書籍轉為 Markdown，保留連結與圖片參照。 | The_book；[原始討論串](https://www.mobileread.com/forums/showthread.php?t=328999)，本機安裝包基準 **1.0.3**。 | **1.0.3.1**，獨立中文設定頁，修正新版 calibre 相容性。 |
| [Modify ePub](./Modify%20ePub/README.md) | 直接清理與修改 EPUB，免經轉檔流程。 | Grant Drake 等；[kiwidude68/calibre_plugins/modify_epub，提交 `683c996`](https://github.com/kiwidude68/calibre_plugins/tree/683c9968aa0302212ee88d769eb598788c88a8b1/modify_epub)，基準 **1.8.14**。 | **1.8.14.1**，正體中文修訂版。 |
| [Send to Kindle](./Send%20to%20Kindle/README.md) | 透過 calibre 電子郵件設定寄書到 Kindle，可指定寄送書名與檔名。 | BookFere／bookfere.com；[bookfere/Send-to-Kindle-Calibre-Plugin，標籤 `v1.1.1`](https://github.com/bookfere/Send-to-Kindle-Calibre-Plugin/tree/e57861e85fcddded1344d784e3c1d4cc4306520c)，基準 **1.1.1**。 | **1.1.1.1**，本倉庫修訂版。 |
| [Skip ASCII Text Plugin](./Skip%20ASCII%20Text%20Plugin/README.md) | 保留檔名中的中文等原文字元，略過 ASCII 轉寫。 | SamLiao & Codex 重寫；原版為 [shiratori3/calibre-plugins v1.0.0](https://gitee.com/shiratori3/calibre-plugins/releases/tag/v1.0.0)，程式作者欄 Billy Zhou，原版採 BSD 3-Clause。 | **1.0.1**，本倉庫重寫版。 |

## 各外掛修改摘要

以下區分本倉庫修改與採用的上游修正；完整差異、驗證紀錄及限制請見各外掛 README。

| 外掛 | 本倉庫修改點 |
| --- | --- |
| Embed Metadata Safe | 本倉庫自行實作：先移除可解析 JSON 物件中缺少 `datatype` 的 `calibre:user_metadata` 項目，再呼叫 calibre 嵌入流程；加入正體中文介面、進度與取消、錯誤摘要及處理格式設定；工具列按鈕簡稱「嵌入資料」。 |
| Enhanced Search and Replace | 1.1.0 新增 HTML 原始碼搜尋、背景進度／取消及結果篩選／排序，通過 Windows 儲存重開驗收。1.2.0 修正：HTML 原始碼允許逐字取代不完整標籤，失敗訊息縮為摘要。原有功能：全書文字類型勾選搜尋、Regex 群組、即時預覽、純文字保格式／HTML 片段、逐筆／批次取代、狀態保留、定位及復原保護；附測試與操作限制。 |
| Export Folder | 自動加入書庫右鍵選單，提供正體中文範本編輯與格式候選清單，逐本匯出第一個可用格式。 |
| Plugin Backup | 新增偏好設定底部入口、全選切換、兩列匯出／匯入按鈕；勾選模式只含所選外掛可辨識專用設定，全部模式可備份完整設定及工具列按鈕位置；提供相容性與校驗檢查、進度及失敗回復；保留本機書庫位置，通過 10 項格式測試、4 項安裝 API 測試與原生 GUI 往返驗證。 |
| Toolbar Manager | 加入專用圖示及正體中文工具列右鍵管理；移除外掛前確認，保護必要入口並保留原有選單。 |
| Traditional Chinese Supplement | 1.2.0 補翻偏好設定、工具列、快捷鍵、範本及編輯器文法／改寫介面；核對 43 個調校項目、184 個核心快捷鍵、196 段書本檢查訊息與 32 條啟用 CSS 規則，保留設定、輸入與修復行為。 |
| AZW6 Image Merge | 以 calibre 內建 Pillow 取代已移除的 `imghdr`，保留 JPEG 位元特徵備援及 TIFF／WDP 對應；補上中文說明與統一打包。合併主流程沿用上游。 |
| Columns Helper | 匯入上游 2.1.1，補齊並修正 323 條原生正體中文訊息，套組欄位標題與說明及工具列接入翻譯；保留查詢名稱與範本公式，通過 calibre 9.19 六項原生 Qt 介面與寫回測試。 |
| Count Pages | 採用上游 1.15.3 的 Goodreads `.xml` 網址與語系更新；保留正體中文語系別名，補齊 12 個提示至 119 個介面翻譯；還原英文斷句模型並設為二進位，避免 Windows 換行破壞，加入離線回歸測試。 |
| Diaps Editing Toolbag | 新增 71 條原生正體中文與兩份內建中文說明，修正 Qt 6、批次錯誤傳遞、目前檔案結果清單、Python 3 撇號例外詞及衝突快捷鍵；通過七項隔離測試及三項功能的原生編輯器儲存重開驗證。 |
| EpubSplit | 解除 EPUB3 阻擋，加入 EPUB3 導覽解析及 EPUB3 輸出，依來源保留 EPUB2／EPUB3；加入 HTML 解析器備援、正體中文翻譯與說明。 |
| Extract ISBN | 修正 ISBN-10 小寫 `x` 校驗、PDF 書尾掃描範圍與方向、缺少格式的錯誤摘要；新增 65 個正體中文介面翻譯、中文說明及 9 組測試，納入共用模組與統一打包。 |
| Find Duplicates | 更新上游至 1.10.11 並整合語系；保留 179 個正體中文介面翻譯、語系別名、中文說明與描述調整。重複書籍比對核心未自行改寫。 |
| Generate Cover | 同步上游塞爾維亞拉丁語翻譯與 2.5.4 文字量測、字重及圖片內距遷移；保留正體中文、自動縮字、背景切換、批次取消、設定匯入與路徑保護、封面 API 及三頁捲動區；補齊旋轉文字匯入與新增翻譯。 |
| Goodreads | 補強書名／作者詞比對、ISBN／ASIN 詳細頁核對與搜尋備援；按引用關係取得系列與作品；修正封面缺少長度標頭、ISBN-13 空值、缺漏日期／評分及重試／逾時處理，加入 8 組離線測試。 |
| Goodreads Sync | 匯入 1.17.6，直接加入正體中文與語系別名；驗證自訂欄位 helper、同步選項內部值與設定儲存，保留原核心。 |
| Hardcover Sync | 更新至上游 0.4.0，保留 ISBN 版本連結與 API 錯誤提示，獨立名稱空間與直接中文翻譯；驗證 API 設定儲存及與 Goodreads Sync 共存，未使用誤標的舊 Goodreads 包。 |
| Manage Series | 保留上游系列管理功能；新增 67 條原生正體中文語系對照，修正 Qt 6、自訂系列欄位選取與小數累加精度，通過七項隔離測試及實際安裝包的 GUI 寫回、關閉重開驗證。 |
| Markdown Output | 改用獨立中文設定頁，解除對舊 TXT 輸出版面的依賴；保留內部參數，通過實際 EPUB 轉 Markdown 測試。 |
| Modify ePub | 同步上游 1.8.14 的 calibre 9.18 封面替換及移除修正，保護原封面頁樣式與標題；保留邊距修正、正體中文語系、中文說明與描述，加入封面回歸測試。 |
| Send to Kindle | 寄送檔名改用 calibre `mtp_devices.send_template` 與書庫欄位，套用寄送視窗書名並保留 Unicode；修正偏好格式設定鍵為 `preferred_format`，移除介面未使用的格式查詢，保留正體中文與中文說明。 |
| Skip ASCII Text Plugin | 沿用執行期間替換函式、保留 Unicode 而不改寫 calibre 安裝檔的方向；重寫核心與設定介面，作者為 SamLiao & Codex；修正位元組輸入、重複切換及函式還原，避免覆蓋後續外掛替換；保留舊設定識別，加入「文」字勾號圖示、附效果示意的正體中文設定視窗、測試與統一打包，移除原包程式及圖示。 |


## calibre 9.19 相容性

2026-11-21 在 Windows、calibre 9.19，以獨立設定目錄和暫存書庫驗證六支自製外掛，另驗證 Manage Series。

2026-11-22 另以實際安裝包在隔離設定與測試書庫驗證 Plugin Backup 0.1、Columns Helper 2.1.1.1，並在測試 EPUB 驗證 Diaps Editing Toolbag 0.5.0.1。

| 外掛 | 驗證範圍 |
| --- | --- |
| Plugin Backup 0.1 | 10 項格式／設定測試、4 項安裝 API 測試及原生偏好設定 GUI 往返通過，涵蓋底部入口、可選設定、停用狀態、覆蓋與失敗回復。 |
| Columns Helper 2.1.1.1 | 六項原生 Qt 離屏測試通過，涵蓋語言包、預覽／篩選、範本測試器、排序、取消、四類欄位儲存、避免重複與資料庫重開。 |
| Diaps Editing Toolbag 0.5.0.1 | 七項隔離測試與兩階段原生 Edit Book 測試通過，涵蓋三項功能、對話框／翻譯、取消與錯誤回復呼叫、原生儲存及另一程序重新開啟。 |
| Embed Metadata Safe 1.0.1 | 實際將中繼資料嵌入暫存書庫的 EPUB。 |
| Enhanced Search and Replace 1.2.0 | 搜尋、取代、格式驗證、復原，以及實際編輯器儲存重開。 |
| Export Folder 1.2.2 | 實際匯出 EPUB／PDF、逐本格式優先選擇與範本編輯。 |
| Toolbar Manager 1.0.0 | 19 項隔離測試通過，涵蓋工具列配置與失敗回復。 |
| Traditional Chinese Supplement 1.2.0 | 12 支隔離測試程式通過，涵蓋原生元件、動態視窗、完整診斷目錄、設定值與輸入保護。 |
| Manage Series 1.5.5.1 | 七項隔離測試及實際安裝包的原生 GUI 寫回、關閉重開驗證通過，涵蓋系列編號、自訂欄位、取消及資料保護。 |
| Skip ASCII Text Plugin 1.0.1 | 10 項隔離測試通過，涵蓋 Unicode、切換與函式還原。 |

驗證涵蓋上述操作；實際裝置傳輸及所有第三方外掛組合尚待驗證。
