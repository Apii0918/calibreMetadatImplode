import builtins
import sys

from qt.core import QAction, QApplication
from calibre.utils import localization
from calibre.gui2.tweak_book.plugin import Tool
from calibre_plugins.traditional_chinese_supplement.ui import TranslationFilter
from calibre_plugins.traditional_chinese_supplement.editor_strings import EDITOR_SCOPE, EDITOR_TEXT

CHECK_SCOPE = 'calibre.ebooks.oeb.polish.check'


def is_editor_module(module):
    return any(module == prefix or module.startswith(prefix + '.') for prefix in (EDITOR_SCOPE, CHECK_SCOPE))


def install_editor_gettext():
    if getattr(localization._, '__module__', None) == __name__:
        return

    from importlib import import_module
    check_modules = []
    for suffix in ('accessibility', 'base', 'css', 'fonts', 'images', 'links', 'main', 'opf', 'parsing'):
        module_name = CHECK_SCOPE + '.' + suffix
        try:
            check_modules.append(import_module(module_name))
        except ModuleNotFoundError as error:
            if error.name != module_name:
                raise

    from calibre_plugins.traditional_chinese_supplement.diagnostic_strings import install_diagnostic_translation
    install_diagnostic_translation()

    def for_editor(gettext):
        def translate(text, *args):
            translated = gettext(text, *args)
            if translated in (text, *args[:1]) and translated in EDITOR_TEXT:
                module = sys._getframe(1).f_globals.get('__name__', '')
                if is_editor_module(module):
                    return EDITOR_TEXT[translated]
            return translated
        return translate

    for name in ('_', 'ngettext'):
        original = getattr(localization, name)
        wrapped = for_editor(original)
        setattr(localization, name, wrapped)
        setattr(builtins, name, for_editor(getattr(builtins, name)))
        # Modules imported before the editor tool retain their original gettext reference.
        for module_name, module in tuple(sys.modules.items()):
            if is_editor_module(module_name) and getattr(module, name, None) is original:
                setattr(module, name, wrapped)

    # Class-level help was evaluated before the editor plugin was loaded.
    from html import unescape
    from calibre import prepare_string_for_xml
    for module in check_modules:
        for cls in vars(module).values():
            if isinstance(cls, type) and cls.__module__ == module.__name__:
                for attribute in ('HELP', 'RULE_NAME', 'INDIVIDUAL_FIX'):
                    source = vars(cls).get(attribute)
                    if isinstance(source, str):
                        plain = unescape(source)
                        translated = EDITOR_TEXT.get(plain)
                        if translated is not None:
                            setattr(cls, attribute, prepare_string_for_xml(translated) if attribute == 'HELP' else translated)


class TranslationTool(Tool):
    name = 'traditional-chinese-supplement'
    allowed_in_toolbar = False
    allowed_in_menu = False

    def __init__(self):
        self.translator = TranslationFilter(QApplication.instance())
        self.translator.start()
        if self.translator.active:
            install_editor_gettext()

    def create_action(self, for_toolbar=True):
        action = QAction(QApplication.instance())
        action.setVisible(False)
        return action
