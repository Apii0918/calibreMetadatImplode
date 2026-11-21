from qt.core import QComboBox, QListWidget, QSpinBox, QDoubleSpinBox, QTabWidget, QTableWidget, QSignalBlocker
from calibre_plugins.traditional_chinese_supplement.hover_strings import HOVER_TEXT
from calibre_plugins.traditional_chinese_supplement.dialog_strings import DIALOG_OPTIONS, DIALOG_TEXT
from calibre_plugins.traditional_chinese_supplement.tweak_strings import TWEAK_DOCS

DIALOG_MODULES = (
    'calibre.gui2.dialogs.palette',
    'calibre.gui2.dialogs.template_dialog',
    'calibre.gui2.dialogs.plugin_updater',
)

# Only display roles change; toolbar action identifiers remain calibre's own.
def install_toolbar_translation():
    from calibre.gui2.preferences.toolbar import BaseModel
    original = BaseModel.data

    def translated_data(model, index, role=...):
        from qt.core import Qt
        value = original(model, index, role)
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return TEXT.get(value, value)
        return value

    BaseModel.data = translated_data
    return original


def restore_toolbar_translation(original):
    from calibre.gui2.preferences.toolbar import BaseModel
    BaseModel.data = original

TWEAKS = {
    'categories_use_field_for_author_name': (
        '在標籤瀏覽器使用作者或系列的排序欄位名稱',
        "設定標籤瀏覽器與內容伺服器顯示作者、系列名稱時使用的欄位。作者可選 'author' 或 'author_sort'，系列可選 'series' 或 'series_sort'。排序欄位的值可能重複，因此清單可能顯示同名項目。工具提示仍會顯示原本名稱。"),
    'allow_template_database_functions_in_composites': (
        '允許在複合欄位使用範本資料庫函式',
        '設為 True 時，可在複合自訂欄位中使用 book_values() 和 book_count()。這可能使處理速度大幅降低。預設為 False。'),
    'openers_by_scheme': (
        '設定開啟檔案或網址時使用的程式',
        '預設由作業系統的預設程式開啟網址。可依類型指定程式，本機檔案為 "file"，網頁為 "http*"。例如 openers_by_scheme = { "http*": "firefox %u" } 會用 Firefox 開啟網址，%u 會代換成網址。類型支援萬用字元比對。'),
    'calendar_start_day_of_week': (
        '設定日曆彈出視窗每週的第一天',
        '必須填入 Default、Sunday、Monday、Tuesday、Wednesday、Thursday、Friday 或 Saturday，英文拼字須完全相同。'),
    'east_asian_base_language': (
        '設定東亞文字轉寫使用的基準語言',
        "指定將東亞文字轉寫為拉丁字母時使用的基準語言。可填 'ja'（日文）、'kr'（韓文）、'vn'（越南文）或 'zh'（中文）。其他值會採用 calibre 偏好設定的語言；若該語言不在上述清單，則以中文為基準。例如 east_asian_base_language = 'ja'。"),
    'hide_ai_features': (
        '隱藏 AI 功能',
        '隱藏 calibre 介面中提及 AI 的選單項目。AI 功能本來就需要使用者自行啟用，設定 AI 後端之前也不會載入相關程式碼。'),
    'qt_webengine_uses_gpu': (
        '控制 Qt WebEngine 使用 GPU',
        'Qt WebEngine 用於顯示 calibre 閱讀器與編輯器的內容。使用 GPU 可以提高效能，但某些舊系統可能當機或黑畫面，因此預設停用。一般使用時通常感覺不到效能差異。'),
}

TEXT = {
    'Help for this tweak': '此調校設定的說明',
    'Edit this tweak': '編輯此調校設定',
    'Also apply the above tags when using the "Copy to library" action': '使用「複製到書庫」時也套用上述標籤',
    'Ignore another file extension': '新增要忽略的副檔名',
    'Bookshelf view': '書架檢視', 'Edit metadata': '編輯中繼資料',
    'Change icon theme': '變更圖示主題', 'Adjust colors': '調整顏色',
    'Round the corners of covers:': '封面圓角：', 'no rounding': '不使用圓角',
    'Pixels': '像素', 'Status bar buttons': '狀態列按鈕',
    'Show layout buttons': '顯示版面配置按鈕', 'Show actions button': '顯示動作按鈕',
    'Reset the main window layout': '重設主視窗配置',
    'Emblem style:': '徽章樣式：', 'No emblems': '不顯示徽章',
    'You can change an existing rule by double clicking it.': '按兩下現有規則即可編輯。',
    'Book spine': '書脊', 'Show cover:': '顯示封面：', 'Cropped': '裁切',
    'Opacity:': '不透明度：', 'Template for first line:': '第一行範本：',
    'Template for second line:': '第二行範本：', 'Template for width:': '寬度範本：',
    'Use a custom pages column': '使用自訂頁數欄位', 'Font:': '字型：',
    'Use default font': '使用預設字型', 'Restore default': '還原預設值',
    'Minimum:': '最小值：', 'Maximum:': '最大值：', 'Outline': '外框',
    'Spine text downwards': '書脊文字向下排列', 'Make space for second line': '保留第二行空間',
    'Shelf height:': '書架高度：', 'Duration of hover animation:': '游標停留動畫時間：',
    'Book height variation:': '書本高度變化：', 'Variable': '可變',
    'Expand the hovered cover:': '展開游標停留的封面：',
    'Shift books on the shelf to make room': '移動書架上的書本以騰出空間',
    'Show shadow for hovered cover': '為游標停留的封面顯示陰影',
    'Group divider style:': '群組分隔樣式：', 'Simple text': '簡單文字',
    'Text aligned to the right': '文字靠右對齊', 'Start shelves with divider': '書架以分隔標題開頭',
    'Recount pages': '重新計算頁數', 'Show count failure log': '顯示頁數計算失敗記錄',
}
TEXT.update({name: translated for name, translated in (
    ('Use author_sort and/or series_sort for names in Tag browser', TWEAKS['categories_use_field_for_author_name'][0]),
    ('Allow template database functions in composite columns', TWEAKS['allow_template_database_functions_in_composites'][0]),
    ('Change the programs that are run when opening files/URLs', TWEAKS['openers_by_scheme'][0]),
    ('Set the first day of the week for calendar popups', TWEAKS['calendar_start_day_of_week'][0]),
    ('East Asian language to use for transliteration', TWEAKS['east_asian_base_language'][0]),
    ('Hide AI features', TWEAKS['hide_ai_features'][0]),
    ('Control GPU usage in Qt WebEngine', TWEAKS['qt_webengine_uses_gpu'][0]),
)})
TEXT.update(DIALOG_TEXT)
TEXT.update(DIALOG_OPTIONS)
TEXT.update({
    'Draw text flush with the bottom of the rendered cover': '文字緊貼顯示封面的底部',
    'Corner for emblems shown on top of covers:': '封面上方徽章的角落位置：',
    'Top-left': '左上', 'Top-right': '右上',
    'Bottom-left': '左下', 'Bottom-right': '右下',
    'Show next to cover': '顯示在封面旁',
    'Show on top of cover': '顯示在封面上',
    'Above the spine': '書脊上方', 'Below the spine': '書脊下方',
    'Top of the spine': '書脊頂端', 'Bottom of the spine': '書脊底端',
    'Constant': '固定', 'Constant per group': '群組內固定',
})

RULE_HELP = {
    'You can control the color of columns in the book list by creating "rules" that tell calibre what color to use.':
        '建立規則可控制書本清單的欄位顏色。',
    'You can add icons to columns in the book list by creating "rules" that tell calibre what icon to use.':
        '建立規則可在書本清單的欄位加入圖示。',
    'You can add emblems (small icons) that are displayed on the side of covers in the Cover grid by creating "rules" that tell calibre what image to use.':
        '建立規則可指定封面窗格中顯示在封面旁的徽章（小圖示）。',
    'You can add an emblem (small icon) that is displayed on or above the book spine in the bookshelf view by creating "rules" that tell calibre what image to use. Only the first emblem in the list that match the conditions will be displayed.':
        '建立規則可指定書脊上或上方顯示的徽章（小圖示），只會顯示第一個符合條件的徽章。',
    'Click the "Add rule" button below to get started.':
        '按下「加入規則」即可開始。',
    'You can <b>change an existing rule</b> by double clicking it.':
        '按兩下即可<b>編輯現有規則</b>。',
}


TEXT.update({
    'Dark/light:': '深色／淺色：', 'Inherit global setting': '沿用全域設定',
    'Use a custom background': '使用自訂背景', 'Use customs colors': '使用自訂顏色',
    'Light mode': '淺色模式', 'Dark mode': '深色模式',
    'Change color': '變更顏色', 'Change texture': '變更紋理',
    'Text on light spine background': '淺色書脊上的文字', 'Text on dark spine background': '深色書脊上的文字',
    'Outline on light spine background': '淺色書脊上的外框', 'Outline on dark spine background': '深色書脊上的外框',
    'Divider background': '分隔標題背景', 'Line on the divider': '分隔標題線條',
    'Text on the divider': '分隔標題文字', 'The current book highlight': '目前書本的醒目顏色',
    'The selected books highlight': '選取書本的醒目顏色', 'The current and selected book highlight': '目前且已選取書本的醒目顏色',
    'Position of the emblem:': '徽章位置：', 'Duplicate rule': '複製規則',
    'Convert to advanced rule': '轉換為進階規則', 'Open icon folder': '開啟圖示資料夾',
    'Link and note icon size:': '連結與筆記圖示大小：',
    'Categories on separate lines': '各分類分行顯示',
    'Select the custom columns (for this library) to display in the edit metadata dialogs and their order:': '選取中繼資料編輯視窗要顯示的自訂欄位（目前書庫）並調整順序：',
    'Reset list': '重設清單', 'Import list': '匯入清單', 'Export list': '匯出清單',
    'Show all columns in default order when editing metadata': '編輯中繼資料時依預設順序顯示所有欄位',
    'Use two columns for custom columns in the Default layout': '預設配置以兩欄顯示自訂欄位',
    'Elide labels when editing custom columns': '編輯自訂欄位時縮短標籤',
    'Bulk edit custom column label length:': '批次編輯的自訂欄位標籤長度：',
    'Single edit custom column label length:': '單本編輯的自訂欄位標籤長度：',
    'Elision point:': '省略位置：',
    'Only the F2 (Edit) key edits column templates (needs restart)': '僅使用 F2（編輯）鍵編輯欄位範本（需要重新啟動）',
    'Display': '顯示', 'Partitioning and collapsing': '分割與折疊',
    'Hierarchy and searching': '階層與搜尋', 'Value icon rules': '數值圖示規則',
    'Select the categories to display in the Tag browser, and their order': '選取標籤瀏覽器顯示的分類並調整順序',
    'Show links icons': '顯示連結圖示', 'Show notes icons': '顯示筆記圖示',
    'Hide empty categories (columns)': '隱藏空白分類（欄位）',
    'Place icons on the right, in columns': '在右側以欄位排列圖示',
    'Expand tree to show last used item': '展開樹狀清單以顯示上次使用的項目',
    'Show items with only sub-items first': '優先顯示只有子項目的項目',
    'Allow the Tag browser to have keyboard focus': '允許標籤瀏覽器取得鍵盤焦點',
    'Combine letters when fewer items than:': '項目數低於此值時合併字母：',
    'Select categories to partition:': '選取要分割的分類：',
    'Select categories with hierarchical items:': '選取使用階層項目的分類：',
    'Set the order of searches when clicking on items': '設定點選項目時的搜尋順序',
    'Search for books containing the current item': '搜尋包含目前項目的書籍',
    'Search for books containing the current item or its children': '搜尋包含目前項目或其子項目的書籍',
    'Search for books not containing the current item': '搜尋不包含目前項目的書籍',
    'Search for books not containing the current item or its children': '搜尋不包含目前項目及其子項目的書籍',
    'Show icons on categories in the Tag browser': '在標籤瀏覽器的分類顯示圖示',
    'Show icons on values in the Tag browser': '在標籤瀏覽器的數值顯示圖示',
    'Show only categories and values available in the current library': '僅顯示目前書庫可用的分類與數值',
    'Category': '分類', 'Icon file or template': '圖示檔案或範本', 'For children': '套用至子項目',
})

TEXT.update({'<p style="text-indent: 2em; font-size:smaller">\nIf you enable this option then you should set a keyboard shortcut to\nfocus the Tag browser under\n<code>Preferences-&gt;Shortcuts-&gt;Tag browser-&gt;Give\nthe Tag browser keyboard focus</code></p>': '<p>啟用後，請到「偏好設定 → 快捷鍵 → 標籤瀏覽器 → 讓標籤瀏覽器取得鍵盤焦點」設定快捷鍵。</p>', '<p>Note: <b>comments</b>-like columns will always\n                 be displayed at the end unless their "Heading position" is\n                 "Show heading to the side".</p>': '<p>注意：類似評註的欄位會顯示在最後，除非將「標題位置」設為「在側邊顯示標題」。</p>', '<p>View all the defined value icon rules, including template rules.\nRules are defined and edited in the Tag browser context menus. Rules can be deleted in\nthis dialog by selecting the Category cell then using the button, the delete key,\nor the context menu. The value icon rules are defined per-user, not per-library.</p>': '<p>顯示所有數值圖示規則，包括範本規則。請在標籤瀏覽器的右鍵選單建立及編輯規則。選取此處的分類儲存格後，可用按鈕、Delete 鍵或右鍵選單刪除規則。規則依使用者儲存，並由各書庫共用。</p>', "There are two kinds of caches that calibre uses to improve performance when rendering covers. A disk cache that is kept on your hard disk and stores the cover thumbnails and an in memory cache used to ensure flicker free rendering of covers. For best results, keep the memory cache small and the disk cache large, unless you have a lot of extra RAM in your computer and don't mind it being used by the memory cache.": 'calibre 使用兩種快取提升封面顯示效能：磁碟快取儲存封面縮圖，記憶體快取減少顯示閃爍。一般建議使用較小的記憶體快取與較大的磁碟快取；若記憶體充足，也可增加記憶體快取。'})
TEXT.update({
    'Double click to view the central book, instead of single click': '按兩下中央書本開啟閱讀',
    'Cover browser position in the narrow layout:': '窄版配置中的封面瀏覽器位置：',
    'Show next cover during auto scroll after:': '自動捲動至下一個封面的間隔：',
    'Max. font size:': '最大字型大小：',
    'You can press the F11 key to toggle full screen mode.': '可按 F11 鍵切換全螢幕模式。',
    'Pressing Enter changes the examined column': '按 Enter 鍵變更檢查的欄位',
    'Recognize numbers inside text when sorting (needs restart)': '排序時辨識文字中的數字（需要重新啟動）',
    'Lookup name:': '查詢名稱：', 'Description:': '說明：', 'Default value:': '預設值：',
    'Search template:': '搜尋範本：', 'Read progress': '閱讀進度',
    'Pressing OK will require restarting calibre even if nothing was changed': '按下確定後需要重新啟動 calibre，即使沒有變更設定。',
    'Unaccented characters match accented characters and punctuation is ignored': '不含重音的字元可比對含重音字元，並忽略標點符號',
    'Show text next to buttons in the search bar': '在搜尋列按鈕旁顯示文字',
    'Show saved searches as a hierarchy': '以階層顯示已儲存的搜尋',
    'Use keyboard searching in the book list': '在書本清單使用鍵盤搜尋',
    'Keep current search when switching Virtual libraries': '切換虛擬書庫時保留目前搜尋',
    'Folders/path (path)': '資料夾／路徑 (path)',
    'Create rules to transform tags/authors/publishers': '建立標籤、作者與出版社的轉換規則',
    'Add new source': '新增來源',
})

TEXT.update({"<b>Grouped search terms</b> are search names that permit a query to automatically search across more than one column. For example, if you create a grouped search term <code>allseries</code> with the value <code>series, #myseries, #myseries2</code>, then the query <code>allseries:adhoc</code> will find 'adhoc' in any of the columns <code>series</code>, <code>#myseries</code>, and <code>#myseries2</code>.<p> Enter the name of the grouped search term in the drop-down box, enter the list of columns to search in the value box, then push the Save button. <p>Note: Search terms are forced to lower case; <code>MySearch</code> and <code>mysearch</code> are the same term. Search terms cannot be hierarchical. Periods are not allowed in the term name.<p>Grouped search terms can show as User categories in the Tag browser by adding the grouped search term names to the 'Make User categories from' box. Multiple terms are separated by commas. These 'automatic user categories' will be populated with items from the categories included in the grouped search term. <p>Automatic user categories permit you to see all the category items that are in the columns contained in the grouped search term. Using the above <code>allseries</code> example, the automatic user category will contain all the series names in <code>series</code>, <code>#myseries</code>, and <code>#myseries2</code>. This can be useful to check for duplicates, to find which column contains a particular item, or to have hierarchical categories (categories that contain categories). <p>Note: values from non-category columns such as comments won't appear in automatic user categories. ": '<b>群組搜尋字詞</b>可讓單一查詢同時搜尋多個欄位。例如將 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   '<code>allseries</code> '
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   '設為 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   '<code>series, '
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   '#myseries, '
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   '#myseries2</code>，搜尋 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   '<code>allseries:adhoc</code> '
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   '就會在這三個欄位尋找 '
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   'adhoc。<p>在名稱欄輸入群組搜尋字詞，在數值欄輸入以逗號分隔的查詢欄位名稱，再按儲存。名稱一律轉為小寫，不能包含句點或使用階層名稱。<p>將群組搜尋字詞加入「製作使用者分類來源」，即可在標籤瀏覽器顯示自動使用者分類。多個名稱以逗號分隔。分類會彙整群組中各欄位的項目，可用來檢查重複項目、查找項目所在欄位或建立階層分類。評註等非分類欄位的數值不會出現在自動使用者分類中。',
 'You can add emblems (small icons) that are displayed on the side of covers in the Cover grid by creating "rules" that tell calibre what image to use. Click the "Add rule" button below to get started.': '建立規則可指定封面窗格中顯示在封面旁的徽章（小圖示）。按下「加入規則」即可開始。',
 'You can add an emblem (small icon) that is displayed on or above the book spine in the bookshelf view by creating "rules" that tell calibre what image to use. Only the first emblem in the list that match the conditions will be displayed. Click the "Add rule" button below to get started.': '建立規則可指定書架檢視中顯示在書脊上或上方的徽章（小圖示）。只會顯示清單中第一個符合條件的徽章，按下「加入規則」即可開始。',
 'You can control the color of columns in the book list by creating "rules" that tell calibre what color to use. Click the "Add rule" button below to get started.': '建立規則可控制書本清單的欄位顏色，按下「加入規則」即可開始。',
 'You can add icons to columns in the book list by creating "rules" that tell calibre what icon to use. Click the "Add rule" button below to get started.': '建立規則可在書本清單的欄位加入圖示，按下「加入規則」即可開始。',
 'Note that this option affects all searches, including saved searches and restrictions. Therefore, if you use this option, it is best to ensure that you always use prefixes in your saved searches. For example, use "series:Foundation" rather than just "Foundation" in a saved search.': '此選項會影響所有搜尋，包括已儲存的搜尋與搜尋限制。啟用時，建議在已儲存的搜尋中明確指定欄位，例如使用 '
                                                                                                                                                                                                                                                                                              'series:Foundation。',
 'When you search for similar books by right clicking the book and selecting "Similar books", calibre constructs a search using the column lookup names specified below. By changing the lookup name to a grouped search term you can search multiple columns at once.': '在書本上按右鍵並選擇「類似的書籍」時，calibre '
                                                                                                                                                                                                                                                                         '會依下列欄位查詢名稱建立搜尋。使用群組搜尋字詞作為查詢名稱，即可同時搜尋多個欄位。'})


def translate_preferences(widget):
    module = type(widget).__module__
    if module == 'calibre.gui2.preferences.template_functions':
        from calibre_plugins.traditional_chinese_supplement.template_help import translate_function_help
        translate_function_help(widget)
    if module == 'calibre.gui2.preferences.look_feel_tabs.bookshelf_view' and hasattr(widget, '_recount_button_txt'):
        widget._recount_button_txt = TEXT.get(
            widget._recount_button_txt.replace('&', ''), widget._recount_button_txt,
        )
    if module == 'calibre.gui2.preferences.search' and hasattr(widget, 'gst_explanation'):
        browser = widget.gst_explanation
        if browser.toPlainText().startswith('Grouped search terms are search names'):
            for source, translated in TEXT.items():
                if source.startswith('<b>Grouped search terms</b>'):
                    browser.setHtml(translated)
                    break
    if module == 'calibre.gui2.preferences.tweaks' and hasattr(widget, 'tweaks_view'):
        model = widget.tweaks_view.model()
        if model is not None:
            changed = False
            for tweak in model.tweaks:
                entry = TWEAKS.get(tweak.var_names[0])
                name = entry[0] if entry else tweak.name
                doc = TWEAK_DOCS.get(tweak.var_names[0], entry[1] if entry else None)
                if doc is not None:
                    doc = 'ID: ' + tweak.var_names[0] + '\n\n' + doc.strip()
                if doc is not None and (tweak.name != name or tweak.doc != doc):
                    tweak.name = name
                    tweak.doc = doc
                    changed = True
            if changed:
                model.layoutChanged.emit()
                current = widget.tweaks_view.currentIndex()
                if current.isValid():
                    widget.help.setPlainText('此調校設定的說明\n\n' + model.tweaks[current.row()].doc)
            if not getattr(widget, '_chinese_help_connected', False):
                widget.help.textChanged.connect(lambda: translate_tweak_heading(widget.help))
                widget._chinese_help_connected = True
            translate_tweak_heading(widget.help)
    if not (
        module.startswith('calibre.gui2.preferences.look_feel')
        or module == 'calibre.gui2.preferences.toolbar'
        or module == 'calibre.gui2.preferences.template_functions'
        or module == 'calibre.gui2.preferences.create_custom_column'
        or module in DIALOG_MODULES
    ):
        return
    for tab in widget.findChildren(QTabWidget):
        for index in range(tab.count()):
            text = tab.tabText(index)
            tab.setTabText(index, TEXT.get(text.replace('&', ''), text))
    for table in widget.findChildren(QTableWidget):
        for index in range(table.columnCount()):
            item = table.horizontalHeaderItem(index)
            if item is not None:
                item.setText(TEXT.get(item.text(), item.text()))
    for child in [widget, *widget.findChildren(QListWidget), *widget.findChildren(QComboBox),
                  *widget.findChildren(QSpinBox), *widget.findChildren(QDoubleSpinBox)]:
        if isinstance(child, QListWidget):
            with QSignalBlocker(child):
                for index in range(child.count()):
                    item = child.item(index)
                    text = item.text()
                    translated = TEXT.get(text.replace("&", ""), text)
                    if translated != text:
                        item.setText(translated)
        elif isinstance(child, QComboBox) and not child.isEditable():
            with QSignalBlocker(child):
                for index in range(child.count()):
                    text = child.itemText(index)
                    translated = TEXT.get(text.replace("&", ""), text)
                    if translated != text:
                        child.setItemText(index, translated)
        elif isinstance(child, (QSpinBox, QDoubleSpinBox)):
            text = child.specialValueText()
            child.setSpecialValueText(TEXT.get(text.replace("&", ""), text))
            if child.suffix() in (' milliseconds', ' chars'):
                child.setSuffix({' milliseconds': ' 毫秒', ' chars': ' 字元'}[child.suffix()])


def translate_tweak_heading(editor):
    text = editor.toPlainText()
    if text.startswith('Help for this tweak'):
        with QSignalBlocker(editor):
            editor.setPlainText(text.replace('Help for this tweak', '此調校設定的說明', 1))


def translate_hover(widget):
    ancestor = widget
    while ancestor is not None:
        module = type(ancestor).__module__
        if module.startswith(('calibre.gui2.preferences.', 'calibre.gui2.convert.')) or module in DIALOG_MODULES or module == 'calibre.gui2.keyboard':
            break
        ancestor = ancestor.parentWidget()
    if ancestor is None:
        return
    if hasattr(widget, 'placeholderText'):
        source = widget.placeholderText()
        translated = TEXT.get(source, source)
        if translated != source:
            widget.setPlaceholderText(translated)
    for getter, setter in (
        (widget.toolTip, widget.setToolTip),
        (widget.statusTip, widget.setStatusTip),
        (widget.whatsThis, widget.setWhatsThis),
    ):
        source = getter()
        translated = HOVER_TEXT.get(source, DIALOG_TEXT.get(source, source))
        if translated != source:
            setter(translated)

TEXT.update({
    'The toolbar (strip with buttons at the top) in calibre is different depending on whether a device is connected or not. Choose which toolbar you would like to customize:': 'calibre 頂端的工具列會依是否連接裝置而有所不同。請選擇要自訂的工具列或選單：',
    'The buttons on the search bar': '搜尋列上的按鈕',
    'Find rule:': '尋找規則：',
    'Press Enter to find the next matching rule': '按 Enter 尋找下一個符合的規則',
    'You can specify rules to transform HTML here. Click the "Add rule" button below to get started.': '您可以在此指定轉換 HTML 的規則，按下「加入規則」即可開始。',
    'Add alt text to images': '為圖片加入替代文字',
    'AirDrop books': '透過 AirDrop 分享書本',
    'Share the selected books via AirDrop': '透過 AirDrop 分享選取的書本',
    'All actions': '所有動作',
    'Show a menu of all available actions, including from third party plugins.\nThis menu is not available when looking at books on a device': '顯示所有可用動作的選單，包括第三方外掛的動作。\n瀏覽裝置上的書本時無法使用此選單。',
    'Auto scroll through the book list, particularly useful with the cover browser open': '自動捲動書本清單，搭配封面瀏覽器使用時特別方便',
    'Book list header menu': '書本清單欄位標題選單',
    'Show the book list header context menu': '顯示書本清單欄位標題的右鍵選單',
    'Browse notes': '瀏覽備註',
    'Column tooltips': '欄位提示文字',
    'Define a custom tooltip for values in a column': '為欄位中的數值設定自訂提示文字',
    'Create your own adventure': '創作自己的冒險故事',
    'Play a "Create your own Adventure" game, in which the story is written by an AI as you play it': '遊玩「創作自己的冒險故事」遊戲，由 AI 隨著遊戲進行撰寫故事',
    'Layout actions': '版面配置動作',
    "Save and restore layout item sizes, and add/remove/toggle layout items such as the search bar, tag browser, etc. Item sizes in saved layouts are saved as a percentage of the window size. Restoring a layout doesn't change the window size, instead fitting the items into the current window.": '儲存與還原版面項目的大小，並加入、移除或切換搜尋列、標籤瀏覽器等項目。項目大小會依視窗尺寸的百分比儲存；還原時會配合目前視窗大小調整項目。',
    'Discuss book with AI': '與 AI 討論書本',
    'AI generate cover': '使用 AI 產生封面',
    'Generate covers for books using AI': '使用 AI 為書本產生封面',
    'Manage categories': '管理分類',
    'Manage categories: authors, tags, series, etc.': '管理作者、標籤、系列等分類',
    'Open book folder': '開啟書本資料夾',
})

RULE_HELP.update({
    'You can specify rules to transform HTML here.': '您可以在此指定轉換 HTML 的規則。',
})

TEXT.update({
    'Search for a shortcut by name or key combination': '依名稱或按鍵組合搜尋快捷鍵',
    'Main window layout': '主視窗版面配置',
    'Open With': '開啟方式',
    'Hardcover Sync': 'Hardcover 同步',
    'Add data files to selected book records': '為選取的書本紀錄加入資料檔案',
    'Add multiple books from archive (ZIP/RAR/7z)': '從壓縮檔加入多本書（ZIP/RAR/7z）',
    'Bulk generate covers': '批次產生封面',
    'Close all Book details windows': '關閉所有書本詳細資料視窗',
    'Filter book list': '篩選書本清單',
    'Generate covers individually': '逐本產生封面',
    'Give the Tag browser keyboard focus': '將鍵盤焦點移至標籤瀏覽器',
    'Mark all selected books': '標記所有選取的書本',
    'Mark books with text label': '以文字標籤標記書本',
    'Open book data folder': '開啟書本資料檔案資料夾',
    'Open the template documentation editor': '開啟範本文件編輯器',
    'Restore recently deleted': '還原最近刪除的項目',
    'Save and restore layout item sizes, and add/remove/toggle layout items such as the search bar, tag browser, etc. ': '儲存與還原版面項目的大小，並加入、移除或切換搜尋列、標籤瀏覽器等項目。',
    'Show Book details in a separate locked window': '在獨立的鎖定視窗顯示書本詳細資料',
    'Show Book details in a separate window': '在獨立視窗顯示書本詳細資料',
    'Show a menu of all available actions.': '顯示所有可用動作的選單。',
    'Show empty categories (columns)': '顯示空白分類（欄位）',
    'Show item tooltip in a dialog': '在對話框顯示項目提示文字',
    'Show the Group by menu for grouping books in the Bookshelf view': '顯示書架檢視中用來分組書本的「分組依據」選單',
    'Show the Sort by menu': '顯示「排序依據」選單',
    'Sort by number of books': '依書本數量排序',
    'Switch to last used Virtual library': '切換到上次使用的虛擬書庫',
    'Toggle average ratings': '切換平均評分顯示',
    'Toggle counts': '切換數量顯示',
    'Toggle layout between wide and narrow': '切換寬版與窄版配置',
    'Toggle links icons': '切換連結圖示顯示',
    'Toggle notes icons': '切換備註圖示顯示',
    'Toggle showing items with only sub-items first': '切換優先顯示僅含子項目的項目',
})

TEXT.update({
    'Template functions': '範本函式',
    'Program code (Follow Python indenting rules):': '程式碼（請遵守 Python 縮排規則）：',
    'Show only user defined template functions': '只顯示使用者定義的範本函式',
    'Import': '匯入',
    'Edit docs': '編輯說明文件',
    'Go': '執行',
    'A General Program Mode Template': '一般程式模式範本',
})
