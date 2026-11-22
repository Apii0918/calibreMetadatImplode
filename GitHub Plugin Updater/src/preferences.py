from calibre.gui2.preferences import AbortInitialize, ConfigWidgetBase

from .ui import UpdaterDialog


class ConfigWidget(ConfigWidgetBase):
    supports_restoring_to_defaults = False

    def genesis(self, gui):
        self.gui = gui

    def initialize(self):
        try:
            UpdaterDialog(self.gui).exec()
        finally:
            self.deleteLater()
        # Return to the preferences grid: updates are applied inside the dialog.
        raise AbortInitialize()
