# calibre 9.19 範本函式頁面的靜態說明。程式範例保留可執行語法。
FUNCTION_HELP = '''
<p>您可以在此加入或移除範本處理使用的函式。範本函式以 Python 撰寫，取得書本資訊並處理後，回傳字串結果。這裡定義的函式可像內建函式一樣用於範本。函式必須命名為 <b>evaluate</b>，並採用下列參數形式。</p>
<p><code>evaluate(self, formatter, kwargs, mi, locals, your parameters)</code> → 回傳 Unicode 字串。</p>
<p>evaluate 函式的參數如下。</p>
<ul>
<li><b>formatter</b>：計算目前範本的格式化器實例，可用於遞迴計算範本。</li>
<li><b>kwargs</b>：包含詮釋資料的字典，各欄位的值都放在其中。</li>
<li><b>mi</b>：用於取得欄位資訊的 <i>Metadata</i> 實例。某些情況下可能為 None，例如計算與書本無關的範本時。</li>
<li><b>locals</b>：目前範本程式已指派的區域變數。</li>
<li><b>your parameters</b>：必須提供一個或多個形式參數，數量須與「參數數量」設定一致。若參數數量為 -1，表示接受可變數量的參數，此時最後一個參數必須是 *args。以基本範本模式呼叫函式時，格式化器一律會傳入至少一個參數。</li>
</ul>
<p>下列範例檢查欄位的值。欄位非空白時回傳原值，否則回傳字串 EMPTY。</p>
<p>名稱：my_ifempty<br>參數數量：1<br>說明：my_ifempty(val) 在 val 非空白時回傳 val，否則回傳字串 'EMPTY'。<br>程式碼：</p>
<pre>def evaluate(self, formatter, kwargs, mi, locals, val):
    if val:
        return val
    else:
        return 'EMPTY'</pre>
<p>此函式可在三種範本程式模式中呼叫。</p>
<ul>
<li>單一函式模式：<code>{tags:my_ifempty()}</code></li>
<li>範本程式模式：<code>{tags:'my_ifempty($)'}</code></li>
<li>一般程式模式：<code>program: my_ifempty(field('tags'))</code></li>
</ul>
'''

STORED_HELP = '''
<p>您可以在此建立、編輯（取代）或刪除範本處理使用的儲存範本。在其他範本中，可像呼叫範本函式一樣使用儲存範本，例如 <code>some_name(arg1, arg2...)</code>。</p>
<p>儲存範本必須採用一般程式模式（General Program Mode，GPM）或 Python 範本模式，並以 <code>program:</code> 或 <code>python:</code> 開頭。GPM 儲存範本可使用 <code>arguments()</code> 取得傳入參數，例如 <code>arguments(var1, var2, ...)</code>；傳入值會複製到指定變數。Python 範本的傳入參數位於 <code>context</code> 參數的 <code>arguments</code> 屬性中，形式為清單。傳入參數一律為字串。</p>
<p>例如，下列 GPM 儲存範本檢查清單中是否包含指定項目。找到任一項目時回傳 '1'，否則回傳空字串 ''。</p>
<p>範本名稱：items_in_list<br>範本內容：</p>
<pre>program:
    arguments(lst='No list argument given', items='');
    r = '';
    for l in items:
        if str_in_list(lst, ',', l, '1', '') then
            r = '1';
            break
        fi
    rof;
    r</pre>
<p>呼叫儲存範本的方式如下。</p>
<pre>program: items_in_list($#genre, 'comics, foo')</pre>
<p>更多資訊請參閱範本語言教學。</p>
'''


def translate_function_help(widget):
    for name, prefix, translated in (
        ('textBrowser', 'Here you can add and remove functions', FUNCTION_HELP),
        ('st_textBrowser', 'Here you can create, edit (replace)', STORED_HELP),
    ):
        browser = getattr(widget, name, None)
        if browser is not None and browser.toPlainText().lstrip().startswith(prefix):
            browser.setHtml(translated)
