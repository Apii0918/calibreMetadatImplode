import re

# Stylelint bundled with calibre 9.19. Captures preserve CSS names and values.
CSS_TEMPLATES = {
    'Unexpected unknown annotation "{0}"': '未知的註記「{0}」',
    'Unexpected unknown at-rule "{0}"': '未知的 @ 規則「{0}」',
    'Unexpected empty block': '不應出現空白區塊',
    'Unexpected invalid hex color "{0}"': '無效的十六進位色碼「{0}」',
    'Unexpected empty comment': '不應出現空白註解',
    'Unexpected missing var function for "{0}"': '「{0}」缺少 var 函式',
    'Unexpected duplicate "{0}"': '不應重複宣告「{0}」',
    'Unexpected shorthand "{0}" after "{1}"': '「{1}」之後不應使用簡寫屬性「{0}」',
    'Unexpected duplicate name {0}': '重複的名稱 {0}',
    'Unexpected missing generic font family': '缺少通用字型族名稱',
    'Expected single space before "{0}" operator': '運算子「{0}」前應有一個空格',
    'Expected single space after "{0}" operator': '運算子「{0}」後應有一個空格',
    'Expected an operator before sign "{0}"': '正負號「{0}」前應有運算子',
    'Unexpected nonstandard direction': '不符合標準的漸層方向',
    'Unexpected unknown function "{0}"': '未知的函式「{0}」',
    'Unexpected !important': '此處不應使用 !important',
    'Unexpected unknown media feature name "{0}"': '未知的媒體特性名稱「{0}」',
    'Expected cell token within string': '字串中應包含網格儲存格標記',
    'Expected same number of cell tokens in each string': '每個字串中的網格儲存格標記數量應相同',
    'Expected single filled-in rectangle for "{0}"': '「{0}」應形成單一且完整填滿的矩形',
    'Expected selector "{0}" to come before selector "{1}"': '選擇器「{0}」應位於選擇器「{1}」之前',
    'Unexpected duplicate @import rule {0}': '重複的 @import 規則 {0}',
    'Unexpected duplicate selector "{0}", first used at line {1}': '重複的選擇器「{0}」，首次出現於第 {1} 行',
    'Unexpected empty source': '不應使用空白樣式來源',
    'Unexpected extra semicolon': '多餘的分號',
    'Unexpected double-slash CSS comment': 'CSS 不應使用雙斜線註解',
    'Unexpected invalid position @import rule': '@import 規則的位置不正確',
    'Unexpected irregular whitespace': '不規則的空白字元',
    'Unexpected unknown property "{0}"': '未知的屬性「{0}」',
    'Unexpected unknown pseudo-class selector "{0}"': '未知的偽類別選擇器「{0}」',
    'Unexpected unknown pseudo-element selector "{0}"': '未知的偽元素選擇器「{0}」',
    'Unexpected unknown type selector "{0}"': '未知的類型選擇器「{0}」',
    'Unexpected newline in string': '字串中不應換行',
    'Unexpected unknown unit "{0}"': '未知的單位「{0}」',
    'Unclosed block': '區塊尚未關閉',
    'Unclosed bracket': '括號尚未關閉',
    'Unclosed string': '字串尚未關閉',
    'Unclosed comment': '註解尚未關閉',
    'Unexpected }': '不應出現右大括號 }',
    'Unknown word {0}': '未知的字詞 {0}',
    'Unknown word': '未知的字詞',
    'Missed semicolon': '缺少分號',
    'Double colon': '重複的冒號',
    'At-rule without name': '@ 規則缺少名稱',
}

CSS_PATTERNS = []
for source, translated in CSS_TEMPLATES.items():
    pattern = re.escape(source)
    for index in (0, 1):
        pattern = pattern.replace(re.escape('{' + str(index) + '}'), '(?P<arg' + str(index) + '>.*?)')
    CSS_PATTERNS.append((re.compile(pattern, re.S), translated))


def translate_css_message(text):
    suffix = re.search(r' \([A-Za-z][\w-]*\)$', text)
    source = text[:suffix.start()] if suffix else text
    for pattern, translated in CSS_PATTERNS:
        match = pattern.fullmatch(source)
        if match is not None:
            values = [match.group('arg' + str(i)) for i in range(len(match.groups()))]
            result = translated.format(*values) if values else translated
            return result + (suffix.group() if suffix else '')
    # shortcut: retain unknown engine messages; extend this catalog when bundled rules change.
    return text


def install_diagnostic_translation():
    from calibre.ebooks.oeb.polish.check import base, css
    original_init = base.BaseError.__init__
    original_css = getattr(css, 'message_to_error', None)

    def initialize(error, msg, name, line=None, col=None):
        if isinstance(msg, str):
            for source, translated in (('Parsing failed: ', '解析失敗：'), ('Invalid image: ', '無效圖片：')):
                if msg.startswith(source):
                    msg = translated + msg[len(source):]
                    break
        original_init(error, msg, name, line, col)

    def message_to_error(message, name, line_offset, rule_metadata):
        # Suppression decisions must still see the original diagnostic and rule.
        error = original_css(message, name, line_offset, rule_metadata)
        if error is not None:
            error.msg = translate_css_message(error.msg)
            source = message.get('text') or ''
            translated = translate_css_message(source)
            if source and translated != source:
                error.HELP = translated + error.HELP[len(source):]
        return error

    base.BaseError.__init__ = initialize
    if original_css is not None:
        css.message_to_error = message_to_error
