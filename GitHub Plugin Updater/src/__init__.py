from calibre.customize import PreferencesPlugin
from calibre.utils.localization import _


class GitHubPluginUpdater(PreferencesPlugin):
    name = 'GitHub Plugin Updater'
    description = '追蹤多個 GitHub 發行來源，勾選更新外掛，可選安裝前備份。'
    author = 'SamLiao & Codex'
    version = (0, 3, 2)
    minimum_calibre_version = (9, 19, 0)
    supported_platforms = ['windows', 'osx', 'linux']
    category = 'Advanced'
    gui_category = _('Advanced')
    category_order = 5
    name_order = 6
    gui_name = 'GitHub 外掛更新'
    icon = 'plugins.png'
    config_widget = 'calibre_plugins.github_plugin_updater.preferences:ConfigWidget'

    def initialize(self):
        from pathlib import Path
        from calibre.utils.config import config_dir
        data = self.load_resources(['images/updater.svg'])['images/updater.svg']
        path = Path(config_dir) / 'plugins' / 'resources' / 'github_plugin_updater' / 'updater.svg'
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        self.icon = str(path)
        from .preferences_layout import install_layout
        install_layout()
