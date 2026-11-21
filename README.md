# calibreMetadatImplode

本專案將十八個 calibre 外掛並排維護，整合上游程式、正體中文資源與本地修正。各外掛可獨立使用；操作、設定、限制、安裝與打包方式請點各外掛名稱閱讀其 README。

外掛首次加入、歷次升級與整合發行紀錄見 [CHANGELOG](./CHANGELOG.md)。

## 本專案來源、版號與修改點

| 項目 | 說明 |
| --- | --- |
| 專案來源 | [SamLaio/calibreMetadatImplode](https://github.com/SamLaio/calibreMetadatImplode)，本倉庫為整合與修訂來源；各外掛的原作者及授權保留於各自目錄。 |
| 整合發行版號 | **[v1.3.22（2026-11-21）](https://github.com/SamLaio/calibreMetadatImplode/releases/tag/v1.3.22)**。這是整套發行附件的版號，與各外掛在 calibre 顯示的版號分開管理。 |
| 專案層修改 | 將外掛整理為各自的 `src/`，使用 `build_release.py` 統一輸出十八個獨立安裝包到 `dist/`；排除隱藏檔、快取及 `.po` 翻譯來源。Extract ISBN、Generate Cover、Goodreads Sync 與 Hardcover Sync 的翻譯在打包時分別編譯。 |
| 本次變更 | 自製外掛通過 calibre 9.19 相容性驗證；正體中文補強更新至 1.1.4，補翻儲存至磁碟視窗。 |

## 各外掛簡介、來源與版號

正體中文補強已更新為 1.1.4，支援主介面與 Edit Book 的指定顯示文字，附設定儲存與例外攔截測試。

以下先列本倉庫自有外掛，再列有上游來源的外掛，各組依名稱字母升序排列；修改摘要採相同順序。

核對日期：**2026-11-21**。已核對各既有上游，Generate Cover 同版號新增語系修訂，已整合為本倉庫 2.5.4.2；其他外掛沒有新版。GitHub 來源另比對固定基準至目前提交的差異，Markdown Output 核對官方索引，Skip ASCII Text Plugin 核對原專案發行。

| 外掛及完整說明 | 簡介 | 上游來源與比對基準 | 本倉庫版號 |
| --- | --- | --- | --- |
| [Embed Metadata Safe](./Embed%20Metadata%20Safe/README.md) | 清理 EPUB 的特定損壞自訂欄位資料，再嵌入書庫中繼資料。 | [本倉庫自有外掛](./Embed%20Metadata%20Safe/)，作者為 SamLiao 及 codex；沒有獨立上游。 | **1.0.1**；修正 ZIP 安裝層級並縮短按鈕名稱。 |
| [Enhanced Search and Replace](./Enhanced%20Search%20and%20Replace/README.md) | Edit Book 全書文字類型勾選搜尋、定位與取代。 | 本倉庫自行開發；SamLiao & Codex，API 查核 Calibre v9.0.0／v9.17.0。 | **1.2.0**；原始碼逐字取代、錯誤摘要；原始碼搜尋、背景進度與取消、篩選排序，預設十五行並附操作截圖。 |
| [Export Folder](./exportFolder/README.md) | 從書庫右鍵選單直接匯出到預設資料夾。 | 本倉庫自行開發，SamLiao & Codex。 | **1.2.2**。 |
| [Toolbar Manager](./Toolbar%20Manager/README.md) | 右鍵調整工具列按鈕，開啟外掛首頁、選項或移除外掛。 | 本倉庫自行開發；SamLiao & Codex。 | **1.0.0**。 |
| [Traditional Chinese Supplement](./Traditional%20Chinese%20Supplement/README.md) | 補齊指定官方與第三方外掛視窗的正體中文顯示文字。 | 本倉庫自行開發；SamLiao & Codex，核對 calibre 9.18.0 與本機外掛。 | **1.1.4**，補翻儲存至磁碟，並保留 Edit Book 無障礙、拼字與其他指定文字，無工具列按鈕。 |
| [AZW6 Image Merge](./AZW6%20Image%20Merge/README.md) | 將 Amazon AZW6 sidecar 高畫質圖片合併至主書檔。 | Andrew Timson；[HamsterExAstris/calibre-azw6-image-merge，提交 `63f76d4`](https://github.com/HamsterExAstris/calibre-azw6-image-merge/tree/63f76d46e19de901536b9bc7c1a02998f26c439b)，基準 **1.0.0**。 | **1.0.0**，含本地相容性修改。 |
| [Count Pages](./Count%20Pages/README.md) | 計算或下載頁數、字數與可讀性統計，寫入自訂欄位。 | Grant Drake；[kiwidude68/calibre_plugins/count_pages，提交 `d46d919`](https://github.com/kiwidude68/calibre_plugins/tree/d46d9197ac2f78e98f2a774a6afbf8d54d9ce68a/count_pages)，基準 **1.15.3**。 | **1.15.3**，正體中文整合版。 |
| [EpubSplit](./EpubSplit/README.md) | 按目錄或章節將 EPUB 拆成多本新書。 | Jim Miller；[JimmXinu/EpubSplit，標籤 `v3.12.0`](https://github.com/JimmXinu/EpubSplit/tree/a0b31ea9c0c9b439329574c4752b24eaaab67f72)，基準 **3.12.0**。 | **3.12.0**，含本地 EPUB3 修改。 |
| [Extract ISBN](./Extract%20ISBN/README.md) | 從電子書內文擷取 ISBN，確認後更新書庫識別碼。 | Grant Drake；[kiwidude68/calibre_plugins/extract_isbn，提交 `2a2dbb2`](https://github.com/kiwidude68/calibre_plugins/tree/2a2dbb2469ec6e68179cd71ba943db240045d097/extract_isbn)，程式宣告 **1.6.7**。 | **1.6.7.1**，基於上游 1.6.7 的本倉庫修訂版。 |
| [Find Duplicates](./Find%20Duplicates/README.md) | 依設定的書目比對規則找出可能重複的書籍。 | Grant Drake；[kiwidude68/calibre_plugins/find_duplicates，提交 `91b0f23`](https://github.com/kiwidude68/calibre_plugins/tree/91b0f23da54fa8f020ba387e1f13a1321706c0ff/find_duplicates)，基準 **1.10.11**；早期來源為 JimmXinu 分支。 | **1.10.11**，正體中文整合版。 |
| [Generate Cover](./Generate%20Cover/README.md) | 用圖片與書目資料製作自訂封面。 | Grant Drake；[kiwidude68/calibre_plugins/generate_cover](https://github.com/kiwidude68/calibre_plugins/tree/cd41919f50ce650c45f652f05bbb4327f243a171/generate_cover)，基準 2.5.4。 | **2.5.4.2**，正體中文修訂版。 |
| [Goodreads](./Goodreads/README.md) | 從 Goodreads 下載書籍中繼資料與封面。 | Grant Drake；最初由使用者提供的 1.10.0 安裝包匯入，已對照 [kiwidude68/calibre_plugins/goodreads，提交 `2a2dbb2`](https://github.com/kiwidude68/calibre_plugins/tree/2a2dbb2469ec6e68179cd71ba943db240045d097/goodreads)，基準 **1.10.0**。 | **1.10.1**，本倉庫修正版。 |
| [Goodreads Sync](./Goodreads%20Sync/README.md) | 同步 Goodreads 書架、評分、書評與閱讀進度。 | Grant Drake；[上游](https://github.com/kiwidude68/calibre_plugins/tree/main/goodreads_sync)，本機安裝包基準 **1.17.6**。 | **1.17.6.1**，直接正體中文化，保留原同步核心。 |
| [Hardcover Sync](./HardCover%20Sync/README.md) | 同步 Hardcover 清單與閱讀資料，擷取書籍 ISBN。 | Juan York；[jojuyo/calibre-hardcover-sync-plugin](https://github.com/jojuyo/calibre-hardcover-sync-plugin)，上游 GitHub 發行基準 **0.4.0**。 | **0.4.0.1**，真正的 Hardcover 外掛，直接正體中文化。 |
| [Markdown Output](./Markdown%20Output/README.md) | 將書籍轉為 Markdown，保留連結與圖片參照。 | The_book；[原始討論串](https://www.mobileread.com/forums/showthread.php?t=328999)，本機安裝包基準 **1.0.3**。 | **1.0.3.1**，獨立中文設定頁，修正新版 calibre 相容性。 |
| [Modify ePub](./Modify%20ePub/README.md) | 直接清理與修改 EPUB，免經轉檔流程。 | Grant Drake 等；[kiwidude68/calibre_plugins/modify_epub，提交 `683c996`](https://github.com/kiwidude68/calibre_plugins/tree/683c9968aa0302212ee88d769eb598788c88a8b1/modify_epub)，基準 **1.8.14**。 | **1.8.14.1**，正體中文修訂版。 |
| [Send to Kindle](./Send%20to%20Kindle/README.md) | 透過 calibre 電子郵件設定寄書到 Kindle，可指定寄送書名與檔名。 | BookFere／bookfere.com；[bookfere/Send-to-Kindle-Calibre-Plugin，標籤 `v1.1.1`](https://github.com/bookfere/Send-to-Kindle-Calibre-Plugin/tree/e57861e85fcddded1344d784e3c1d4cc4306520c)，基準 **1.1.1**。 | **v1.1.1_r.1**；calibre 數字版號顯示 **1.1.1**。 |
| [Skip ASCII Text Plugin](./Skip%20ASCII%20Text%20Plugin/README.md) | 保留檔名中的中文等原文字元，略過 ASCII 轉寫。 | SamLiao & Codex 重寫；原版為 [shiratori3/calibre-plugins v1.0.0](https://gitee.com/shiratori3/calibre-plugins/releases/tag/v1.0.0)，程式作者欄 Billy Zhou，原版採 BSD 3-Clause。 | **1.0.1**，本倉庫重寫版。 |

## 各外掛修改摘要

以下區分本倉庫修改與採用的上游修正；完整差異、驗證紀錄及限制請見各外掛 README。

| 外掛 | 本倉庫修改點 |
| --- | --- |
| Embed Metadata Safe | 本倉庫自行實作：先移除可解析 JSON 物件中缺少 `datatype` 的 `calibre:user_metadata` 項目，再呼叫 calibre 嵌入流程；加入正體中文介面、進度與取消、錯誤摘要及處理格式設定；工具列按鈕簡稱「嵌入資料」。 |
| Enhanced Search and Replace | 1.1.0 新增 HTML 原始碼搜尋、背景進度／取消及結果篩選／排序，通過 Windows 儲存重開驗收。1.2.0 修正：HTML 原始碼允許逐字取代不完整標籤，失敗訊息縮為摘要。原有功能：全書文字類型勾選搜尋、Regex 群組、即時預覽、純文字保格式／HTML 片段、逐筆／批次取代、狀態保留、定位及復原保護；附測試與操作限制。 |
| Export Folder | 自動加入書庫右鍵選單，提供正體中文範本編輯與格式候選清單，逐本匯出第一個可用格式。 |
| Toolbar Manager | 加入專用圖示及正體中文工具列右鍵管理；移除外掛前確認，保護必要入口並保留原有選單。 |
| Traditional Chinese Supplement | 不顯示工具列／選單按鈕，自動補翻；新增 317 條指定範圍及 12 條共用對照，保留已有中文與設定識別值；15 組自動化及 13 個實際外掛面板驗證，附測試限制及 2026-11-09 驗證歸因更正。 |
| AZW6 Image Merge | 以 calibre 內建 Pillow 取代已移除的 `imghdr`，保留 JPEG 位元特徵備援及 TIFF／WDP 對應；補上中文說明與統一打包。合併主流程沿用上游。 |
| Count Pages | 採用上游 1.15.3 的 Goodreads `.xml` 網址與語系更新；保留正體中文語系別名，補齊 12 個提示至 119 個介面翻譯；還原英文斷句模型並設為二進位，避免 Windows 換行破壞，加入離線回歸測試。 |
| EpubSplit | 解除 EPUB3 阻擋，加入 EPUB3 導覽解析及 EPUB3 輸出，依來源保留 EPUB2／EPUB3；加入 HTML 解析器備援、正體中文翻譯與說明。 |
| Extract ISBN | 修正 ISBN-10 小寫 `x` 校驗、PDF 書尾掃描範圍與方向、缺少格式的錯誤摘要；新增 65 個正體中文介面翻譯、中文說明及 9 組測試，納入共用模組與統一打包。 |
| Find Duplicates | 更新上游至 1.10.11 並整合語系；保留 179 個正體中文介面翻譯、語系別名、中文說明與描述調整。重複書籍比對核心未自行改寫。 |
| Generate Cover | 同步上游塞爾維亞拉丁語翻譯與 2.5.4 文字量測、字重及圖片內距遷移；保留正體中文、自動縮字、背景切換、批次取消、設定匯入與路徑保護、封面 API 及三頁捲動區；補齊旋轉文字匯入與新增翻譯。 |
| Goodreads | 補強書名／作者詞比對、ISBN／ASIN 詳細頁核對與搜尋備援；按引用關係取得系列與作品；修正封面缺少長度標頭、ISBN-13 空值、缺漏日期／評分及重試／逾時處理，加入 8 組離線測試。 |
| Goodreads Sync | 匯入 1.17.6，直接加入正體中文與語系別名；驗證自訂欄位 helper、同步選項內部值與設定儲存，保留原核心。 |
| Hardcover Sync | 更新至上游 0.4.0，保留 ISBN 版本連結與 API 錯誤提示，獨立名稱空間與直接中文翻譯；驗證 API 設定儲存及與 Goodreads Sync 共存，未使用誤標的舊 Goodreads 包。 |
| Markdown Output | 改用獨立中文設定頁，解除對舊 TXT 輸出版面的依賴；保留內部參數，通過實際 EPUB 轉 Markdown 測試。 |
| Modify ePub | 同步上游 1.8.14 的 calibre 9.18 封面替換及移除修正，保護原封面頁樣式與標題；保留邊距修正、正體中文語系、中文說明與描述，加入封面回歸測試。 |
| Send to Kindle | 寄送檔名改用 calibre `mtp_devices.send_template` 與書庫欄位，套用寄送視窗書名並保留 Unicode；修正偏好格式設定鍵為 `preferred_format`，移除介面未使用的格式查詢，保留正體中文與中文說明。 |
| Skip ASCII Text Plugin | 沿用執行期間替換函式、保留 Unicode 而不改寫 calibre 安裝檔的方向；重寫核心與設定介面，作者為 SamLiao & Codex；修正位元組輸入、重複切換及函式還原，避免覆蓋後續外掛替換；保留舊設定識別，加入「文」字勾號圖示、附效果示意的正體中文設定視窗、測試與統一打包，移除原包程式及圖示。 |


## calibre 9.19 相容性

2026-11-21 在 Windows、calibre 9.19，以獨立設定目錄和暫存書庫驗證六支自製外掛。

| 外掛 | 驗證範圍 |
| --- | --- |
| Embed Metadata Safe 1.0.1 | 實際將中繼資料嵌入暫存書庫的 EPUB。 |
| Enhanced Search and Replace 1.2.0 | 搜尋、取代、格式驗證、復原，以及實際編輯器儲存重開。 |
| Export Folder 1.2.2 | 實際匯出 EPUB／PDF、逐本格式優先選擇與範本編輯。 |
| Toolbar Manager 1.0.0 | 19 項隔離測試通過，涵蓋工具列配置與失敗回復。 |
| Traditional Chinese Supplement 1.1.4 | 18 項測試通過，涵蓋語系、元件顯示、設定值保護與自動啟用。 |
| Skip ASCII Text Plugin 1.0.1 | 10 項隔離測試通過，涵蓋 Unicode、切換與函式還原。 |

驗證涵蓋上述操作；實際裝置傳輸及所有第三方外掛組合尚待驗證。
