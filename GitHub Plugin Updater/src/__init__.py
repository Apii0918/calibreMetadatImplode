from calibre.customize import InterfaceActionBase


class GitHubPluginUpdater(InterfaceActionBase):
    name = 'GitHub Plugin Updater'
    description = '追蹤多個 GitHub 發行來源，勾選更新外掛並在安裝前備份。'
    author = 'SamLiao & Codex'
    version = (0, 1)
    minimum_calibre_version = (9, 19, 0)
    supported_platforms = ['windows', 'osx', 'linux']
    actual_plugin = 'calibre_plugins.github_plugin_updater.ui:UpdaterAction'
