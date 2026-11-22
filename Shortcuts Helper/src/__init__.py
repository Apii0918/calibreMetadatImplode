__license__   = 'GPL v3'
__copyright__ = '2026, Comfy.n'
__docformat__ = 'restructuredtext en'

from calibre.customize import InterfaceActionBase

load_translations()

class ShortcutsButtonPlugin(InterfaceActionBase):
    name = 'Shortcuts Helper'
    description = _('Quick access to Shortcuts preferences and current shortcuts list')
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Comfy.n'
    version = (1, 1, 0, 1)
    minimum_calibre_version = (5, 44, 0)
    actual_plugin = 'calibre_plugins.shortcuts_helper.ui:ShortcutsButtonAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from .config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
        if getattr(self, 'actual_plugin_', None):
            try:
                self.actual_plugin_.refresh_action_state()
            except Exception:
                pass