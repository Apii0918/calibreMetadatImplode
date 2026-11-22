# GitHub 更新清單規格（schema 1）

每個來源以 `github:owner/repo` 小寫作為來源 ID；每支外掛另有穩定且唯一的 `id`。不要以版本或下載檔名組成 ID。來源之間不共用綁定，不跨來源比較版號。

## 清單

最新正式 Release 的 `plugins.json`：

```json
{
  "format": "calibre-github-plugins",
  "schema": 1,
  "source": "github:example/plugins",
  "plugins": [
    {
      "id": "example.my-plugin",
      "name": "My Plugin",
      "version": [0, 1],
      "minimum_calibre_version": [9, 19, 0],
      "supported_platforms": ["windows", "osx", "linux"],
      "asset": "My Plugin.zip",
      "size": 12345,
      "sha256": "替換為包內內容的 64 字元小寫十六進位 SHA-256",
      "package_sha256": "替換為完成的 ZIP 的 64 字元小寫十六進位 SHA-256"
    }
  ]
}
```

`name`、`version`、`minimum_calibre_version`、`supported_platforms` 必須與 calibre 外掛類別宣告一致；`asset` 必須為同次 Release 中唯一的 `.zip` 附件名稱，`size` 為 ZIP 位元組數。GitHub 上傳時會將附件名稱的空白改為句點；清單保留本機原檔名，更新器先比對原名，找不到時再比對空白轉句點的附件名。JSON 不指定任意下載網址，更新器由 GitHub API 對應同次 Release 的附件，避免外部網址注入。

## 包內身分檔

ZIP 根層 `github-plugin-identity.json`：

```json
{
  "id": "example.my-plugin",
  "source": "github:example/plugins",
  "sha256": "與清單 sha256 一致的 64 字元內容 SHA-256"
}
```

身分檔記 ID、來源與內容 `sha256`，不放自己的完整 ZIP SHA，以免自我引用。版號保存在清單與程式宣告，下載後互相核對。

## 製作順序

1. 維護者先更新程式宣告、版號與說明；內容改變時遞增版號。
2. 先封裝程式、說明與翻譯等內容，計算內容 SHA 後放入身分檔；固定 ZIP 項目順序、時間戳與權限，排除產物、快取與翻譯原始檔。
3. 完成並關閉 ZIP 後，計算其位元組大小及完整 ZIP SHA-256，寫入 JSON 的 `size` 與 `package_sha256`；`sha256` 則與身分檔的內容 SHA 相同。兩者均不由版號文字產生。
4. 本倉庫以 `build_release.py` 統一完成上述步驟，輸出至 `dist/`。維護根目錄清單快照，發布時同批上傳 `plugins.json` 與所有列出的 ZIP。
5. 不使用來源檔案修改時間當作版號或雜湊輸入；內容相同應可重現相同 ZIP。內容 SHA 改變時必須更新受影響外掛版號；只有封裝方式不同而內容 SHA 相同時，不視為外掛更新。

GitHub API 使用[最新正式 Release](https://docs.github.com/en/rest/releases/releases#get-the-latest-release)，公開庫無須認證；遇到 API 限流則顯示錯誤，稍後再試，不改追蹤來源。

## 內容 SHA 的確切算法

SHA-256 初始輸入為 UTF-8／ASCII 位元組 `calibre-plugin-content-v1` 加一個 NUL 位元組。按 ZIP 項目檔名的字串升序處理所有檔案，跳過目錄與根層 `github-plugin-identity.json`。每個檔案依序加入：UTF-8 檔名位元組長度（8 位元組無號大端序）、UTF-8 檔名、解壓後檔案大小（8 位元組無號大端序）、解壓後完整內容。最後輸出小寫十六進位摘要。長度欄位避免不同路徑／內容組合混淆；ZIP 時間、權限、壓縮方式與身分檔不納入內容 SHA。

更新檢查僅比較身分檔與清單的 `sha256`；下載後另驗 `package_sha256` 及實際內容 SHA。身分檔本身不是防竄改簽章，來源與 ID 仍須獨立核對。
