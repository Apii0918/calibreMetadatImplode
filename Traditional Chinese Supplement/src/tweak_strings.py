# calibre 9.19 調校設定說明；設定識別字、可填值與程式範例保留原文。
TWEAK_DOCS = {
    'series_index_auto_increment': '''設定書本加入既有系列時，如何指派系列編號。除非指定固定的非整數，否則新編號一律為整數。可用值如下。

    next：大於目前最大編號的第一個可用整數。
    first_free：大於 0 的第一個可用整數。
    next_free：大於目前最小編號的第一個可用整數。
    last_free：小於目前最大編號的第一個可用整數；若沒有空號，使用目前最大編號加 1。
    const：一律指派 1。
    no_change：保留原本的系列編號。
    數字：一律指派指定數字，不加引號，也可使用 0.0。

範例：
    series_index_auto_increment = 'next'
    series_index_auto_increment = 'next_free'
    series_index_auto_increment = 16.5

若要在匯入或加入書本時套用以上規則，請將 use_series_auto_increment_tweak_when_importing 設為 True。預設為 False，此時匯入過程未明確提供編號的書本會使用 1；設為 True 則依 series_index_auto_increment 決定。這項設定僅適用於匯入時未提供編號的情況。如果匯入用的正規表示式已產生 series_index，或讀取書本詮釋資料的外掛已提供編號，一律採用該值。''',
    'authors_completer_append_separator': '''設定完成作者姓名的自動補齊後，是否在文字末尾加入分隔字元，以自動開始補齊下一位作者。可填 True 或 False。''',
    'author_sort_copy_method': '''設定將作者名稱複製到 author_sort 時使用的演算法。下列 fn 代表名字，ln 代表姓氏。

    invert：將 "fn ln" 轉為 "ln, fn"。
    copy：直接複製作者名稱，不作變更。
    comma：名稱中有逗號「,」時使用 copy，否則使用 invert。
    nocomma：將 "fn ln" 轉為 "ln fn"，不加逗號。

變更此設定後，必須重新計算各作者已儲存的排序值。在左側標籤面板的作者上按右鍵，選擇「管理作者」，再按「重新計算所有作者排序值」。

author_name_suffixes 列出作者姓名末尾可忽略的字詞。比對時不區分大小寫，並會自動處理末尾句點。author_name_prefixes 對姓名開頭的字詞採用相同處理。

author_name_copywords 列出的字詞只要出現在作者姓名中，就會使自動產生的排序字串與作者名稱完全相同。例如 "Acme Inc." 的排序值會維持 "Acme Inc."，而不會變成 "Inc., Acme"。

啟用 author_use_surname_prefixes 後，author_surname_prefixes 中的字詞若出現在姓氏前方，會視為姓氏的一部分。例如 "John von Neumann" 會排序為 "von Neumann, John"，而不會變成 "Neumann, John von"。''',
    'categories_use_field_for_author_name': '''設定標籤瀏覽器（左側的作者、系列、出版社等清單）用哪個作者或系列欄位顯示項目名稱。作者可用 'author' 或 'author_sort'，系列可用 'series' 或 'series_sort'。此設定只影響標籤瀏覽器及內容伺服器中分類項目的顯示名稱。

作者與系列名稱保證唯一，但其排序值不一定唯一。因此改用 …_sort 欄位後，清單可能出現重複名稱；這不會破壞資料，但可能造成混淆。無論如何設定，項目的工具提示都會顯示原本名稱。

範例：
    categories_use_field_for_author_name = 'author'
    categories_use_field_for_author_name = 'author_sort'
    categories_use_field_for_series_name = 'series'
    categories_use_field_for_series_name = 'series_sort' ''',
    'gui_pubdate_display_format': '''設定介面中出版日期與時間戳記（日期）的顯示格式。

    d：日期，不補零（1 到 31）。
    dd：日期，補零（01 到 31）。
    ddd：依語系顯示星期縮寫，例如 Mon 到 Sun。
    dddd：依語系顯示完整星期名稱，例如 Monday 到 Sunday。
    M：月份，不補零（1 到 12）。
    MM：月份，補零（01 到 12）。
    MMM：依語系顯示月份縮寫，例如 Jan 到 Dec。
    MMMM：依語系顯示完整月份名稱，例如 January 到 December。
    yy：兩位數年份（00 到 99）。
    yyyy：四位數年份。
    h：小時，不補零；依 am/pm 設定使用 0 到 11 或 0 到 23。
    hh：小時，補零；依 am/pm 設定使用 00 到 11 或 00 到 23。
    m：分鐘，不補零（0 到 59）。
    mm：分鐘，補零（00 到 59）。
    s：秒數，不補零（0 到 59）。
    ss：秒數，補零（00 到 59）。
    ap：使用十二小時制，並以語系對應的小寫 am 或 pm 取代 ap。
    AP：使用十二小時制，並以語系對應的大寫 AM 或 PM 取代 AP。
    aP：使用十二小時制，並以語系對應的 am 或 pm 字串取代 aP。
    Ap：使用十二小時制，並以語系對應的 AM 或 PM 字串取代 Ap。
    iso：包含時間與時區的日期；不能與其他格式混用。

以 2010 年 1 月 9 日為例：
    MMM yyyy ==> Jan 2010    yyyy ==> 2010       dd MMM yyyy ==> 09 Jan 2010
    MM/yyyy ==> 01/2010      d/M/yy ==> 9/1/10   yy ==> 10

未設定時，出版日期使用 MMM yyyy，時間戳記使用 dd MMM yyyy，last_modified_display_format 使用 dd MMM yyyy。''',
    'title_series_sorting': '''控制書庫檢視中書名與系列的排序方式。設為 'library_order' 時，使用書名排序欄位；除非您手動編輯過該欄位，否則會忽略開頭的 The、A 等冠詞。設為 'strictly_alphabetic' 時，直接依原本書名排序。例如 The Client 在 library_order 下排在 C，在 strictly_alphabetic 下排在 T。

此設定影響 calibre 書庫的顯示，不影響裝置。變更前已加入的書本會保留原有排序，直到再次編輯書名。只要進入書名編輯後按 Enter，即使不修改文字，也足以更新排序；也可在批次編輯詮釋資料視窗使用「更新書名排序」一次更新多本書。''',
    'sony_collection_renaming_rules': '''指定 SONY 藏書的重新命名規則，僅在詮釋資料管理設為自動時適用。標準欄位產生的藏書直接使用欄位值作為名稱，例如 series 欄位值為 Darkover 時，藏書名稱就是 Darkover。自訂欄位產生的藏書則會附加欄位名稱，例如自訂系列欄位 My Series 的值為 Darkover 時，預設名稱為 Darkover (My Series)。以下將 Darkover 稱為「值」，My Series 稱為「分類」。兩本書若產生相同的藏書名稱，就會放入同一個藏書。

可為標準或自訂欄位指定命名方式，例如把 Foo 改為 Foo (Tag)，或將多個欄位合併為同一組藏書。例如 series、#my_series_1、#my_series_2 的值都可產生 some_value (Series) 形式的名稱。

兩項設定共同控制命名。sony_collection_renaming_rules 指定各詮釋資料欄位使用的分類名稱，語法如下：
    {'field_lookup_name':'category_name_to_use', 'lookup_name':'name', ...}

sony_collection_name_template 使用與詮釋資料轉換規則及儲存範本相同的範本語言，將值與分類組合成藏書名稱。僅可使用 {category} 與 {value}；{value} 不會空白，{category} 可以空白。預設先放值，再將非空白分類放入括號：
    '{value} {category:|(|)}'

下列前三個範例都假設未變更 sony_collection_name_template。

1）將 series、#series_1、#series_2 合併為同一組藏書，不附加括號：
    sony_collection_renaming_rules={'series':'', '#series_1':'', '#series_2':''}

2）系列產生的藏書附加 (Series)，標籤產生的藏書附加 (Tag)：
    sony_collection_renaming_rules={'series':'Series', 'tags':'Tag'}

3）將 series 與 #myseries 合併，並在名稱末尾附加 (Series)：
    sony_collection_renaming_rules={'series':'Series', '#myseries':'Series'}

4）與範例 2 相同，但將分類放在值前方並以冒號分隔，例如 Series: Darkover。需同時變更兩項設定：
    sony_collection_renaming_rules={'series':'Series', 'tags':'Tag'}
    sony_collection_name_template='{category:||: }{value}' ''',
    'sony_collection_sorting_rules': '''指定 SONY 藏書的排序方式，僅在詮釋資料管理設為自動時適用。可針對各個藏書指定排序用的詮釋資料欄位。設定值為一份清單，每個項目包含產生藏書的欄位清單，以及提供排序值的欄位名稱。

例如下列設定表示：由 pubdate 或 tags 產生的藏書依自訂欄位 #mydate 排序；由 series 產生的藏書依 series_index 排序；其餘藏書依 title 排序。
    [(['pubdate', 'tags'],'#mydate'), (['series'],'series_index'), (['*'], 'title')]

未指定規則的欄位，若為系列藏書則依系列順序排序，否則依書名排序。方括號與圓括號都不可省略，語法如下：
    [ ( [欄位清單], 排序欄位 ), ( [欄位清單], 排序欄位 ) ]

預設為空白清單，表示沒有指定藏書排序規則。''',
    'doubleclick_on_library_view': '''控制在書本清單上按兩下或按 Enter 的行為。可用值如下。

    open_viewer：開啟閱讀器（預設）。
    do_nothing：不執行動作。
    show_book_details：顯示書本詳細資料。
    show_locked_book_details：顯示鎖定的書本詳細資料。
    edit_cell：編輯儲存格。
    edit_metadata：編輯詮釋資料。

選擇 open_viewer、show_book_details、show_locked_book_details 以外的值，會同時停用以單擊編輯欄位的功能。

範例：doubleclick_on_library_view = 'do_nothing'

也可控制書本清單按項目或按像素捲動；預設按項目捲動。''',
    'gui_view_history_size': '''在「閱讀」按鈕上按右鍵，會顯示最近閱讀過的書本清單。此設定控制清單顯示的書本數量。''',
    'change_book_details_font_size_by': '''調整側邊面板中書本詳細資料，以及詮釋資料編輯視窗中評註的字型大小。正數放大，負數縮小。也可用相應設定調整與 AI 對話的元件字型大小。''',
    'preselect_first_completion': '''不預先選取第一個自動補齊項目時，您可以修改文字後直接按 Enter，輸入內容不會被符合的補齊項目覆蓋。若要採用補齊項目，則需先按 Tab 選取，再按 Enter。適合哪種方式，取決於書庫詮釋資料的狀況與您的編輯習慣。

當 preselect_first_completion 為 False 時，若希望 Tab 接受已輸入的文字，而非第一個補齊項目，可將 tab_accepts_uncompleted_text 設為 True。此時必須使用向下或向上方向鍵選取補齊項目。preselect_first_completion 為 True 時，會忽略 tab_accepts_uncompleted_text。''',
    'completion_mode': '''預設只顯示以您輸入文字開頭的補齊候選項目。將 completion_mode 設為 'contains'，可改為顯示任何包含該文字的項目。例如輸入 asi 時，可符合 Asimov 和 Quasimodo；預設只符合 Asimov。

'word-prefix' 模式只比對單字開頭。例如 asi 可符合 Asimov 和 "Isaac Asimov"，不符合 Quasimodo；cat 可符合 cathedral 和 "tabby cat"，不符合 education。

使用 'word-prefix' 時，可透過 extra_word_break_chars 指定額外的單字分隔字元。例如 extra_word_break_chars = '-' 時，輸入 fic 可同時符合 "Science Fiction" 和 "Science-Fiction"，而非僅符合前者。''',
    'many_libraries': '''「複製到書庫」與「快速切換」選單中的書庫，通常依使用頻率排序。當書庫數量超過指定門檻時，會改依字母順序排序。可在此設定門檻，預設為十個書庫。''',
    'cover_drop_exclude': '''將 calibre 支援的圖片檔案拖放到「書本詳細資料」面板時，通常會將它設為封面。若要將某些圖片格式當作電子書檔案儲存，可在此列出格式。

範例：
    cover_drop_exclude = {'tiff', 'webp'}''',
    'exclude_fields_on_paste': '''使用「編輯詮釋資料 → 複製詮釋資料／貼上詮釋資料」時，可指定不貼上的欄位。例如：
    exclude_fields_on_paste = ['cover', 'timestamp', '#mycolumn']

這會排除封面、日期及自訂欄位 mycolumn。也可在「偏好設定 → 快捷鍵 → 編輯詮釋資料」中，為忽略此設定的貼上動作指定快捷鍵。''',
    'template_editor_tab_stop_width': '''以「平均字元寬度」設定範本編輯器的定位點寬度。例如設為 1 時，一個定位點的寬度相當於一個平均字元的寬度。''',
    'value_for_undefined_numbers_when_sorting': '''指定排序時將未定義的數值視為多少。例如設為 -10，未定義數值就會當作 -10 排序。'maximum' 表示可用的最大數值，'minimum' 表示可用的最小數值。直接填入數字時，引號可省略。

範例：
    value_for_undefined_numbers_when_sorting = -100
    value_for_undefined_numbers_when_sorting = '2'
    value_for_undefined_numbers_when_sorting = -0.01
    value_for_undefined_numbers_when_sorting = 'minimum'
    value_for_undefined_numbers_when_sorting = 'maximum' ''',
}

TWEAK_DOCS.update({
    'allow_template_database_functions_in_composites': '設為 True 時，可在複合自訂欄位中使用範本資料庫函式 book_values() 與 book_count()。啟用後若在複合欄位使用這些函式，處理速度可能大幅降低。預設為 False。',
    'openers_by_scheme': '''預設由作業系統依已設定的預設程式開啟網址。可在此依網址類型指定要使用的程式。本機檔案的類型為 "file"，網頁連結為 "http*"。

例如 openers_by_scheme = { "http*": "firefox %u" }，會讓 calibre 使用 Firefox 開啟 https://whatever 之類的網址。%u 會代換為要開啟的網址。網址類型支援 glob 萬用字元模式，可用同一筆規則比對多種類型。''',
    'calendar_start_day_of_week': '必須使用下列英文值之一，且拼字須完全相同。Default（預設）、Sunday（星期日）、Monday（星期一）、Tuesday（星期二）、Wednesday（星期三）、Thursday（星期四）、Friday（星期五）或 Saturday（星期六）。',
    'east_asian_base_language': '''設定將東亞文字轉寫為拉丁字母時使用的基準語言。例如使用英文介面，但希望依日文而非中文讀音轉寫時，可使用此設定。可用值如下。

    'ja'：日文。
    'kr'：韓文。
    'vn'：越南文。
    'zh'：中文。

填入其他值時，使用 calibre 偏好設定中的語言作為基準；若該語言不在上述清單，則以中文為基準。

範例：east_asian_base_language = 'ja' ''',
    'hide_ai_features': '隱藏 calibre 使用者介面中的 AI 功能。AI 功能原本就需要使用者自行啟用；設定 AI 後端之前，連相關程式碼都不會載入。此調校設定只是隱藏少數提及 AI 的選單項目及類似介面文字。',
    'qt_webengine_uses_gpu': 'Qt WebEngine 是 calibre 閱讀器與編輯器用來顯示內容的程式庫。它可以使用 GPU 提升效能，但某些較舊系統可能因此當機或出現黑畫面，所以預設停用。一般使用時，通常感覺不到效能差異。',
})
