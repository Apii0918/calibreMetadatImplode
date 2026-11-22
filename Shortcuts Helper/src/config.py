__license__   = 'GPL v3'
__copyright__ = '2026, Comfy.n'
__docformat__ = 'restructuredtext en'

from qt.core import QComboBox, QFormLayout, QLabel, QVBoxLayout, QWidget

from calibre.utils.config import JSONConfig


try:
    load_translations()
except NameError:
    pass

c_ = _


PREFS = JSONConfig('plugins/shortcuts_helper')
KEY_MAIN_ACTION = 'main_action'

ACTION_OPEN_PREFS = 'prefs'
ACTION_SHOW_CURRENT = 'current'

ACTION_CHOICES = (
    (ACTION_OPEN_PREFS, c_('Open Shortcuts Preferences')),
    (ACTION_SHOW_CURRENT, c_('Show Current Shortcuts')),
)

PREFS.defaults[KEY_MAIN_ACTION] = ACTION_OPEN_PREFS


def get_main_action_key():
    value = PREFS.get(KEY_MAIN_ACTION, ACTION_OPEN_PREFS)
    valid_keys = {key for key, _label in ACTION_CHOICES}
    if value not in valid_keys:
        return ACTION_OPEN_PREFS
    return value


class ConfigWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)

        layout = QVBoxLayout(self)
        intro = QLabel(c_('Choose what the toolbar button click opens.'))
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        self.main_action_combo = QComboBox(self)
        for key, label in ACTION_CHOICES:
            self.main_action_combo.addItem(label, key)

        current_key = get_main_action_key()
        current_index = max(0, self.main_action_combo.findData(current_key))
        self.main_action_combo.setCurrentIndex(current_index)
        form.addRow(c_('Direct toolbar click action:'), self.main_action_combo)
        layout.addLayout(form)
        layout.addStretch(1)

    def save_settings(self):
        PREFS[KEY_MAIN_ACTION] = self.main_action_combo.currentData()