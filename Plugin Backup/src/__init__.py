from calibre.customize import InterfaceActionBase

__license__ = 'GPL v3'


class PluginBackup(InterfaceActionBase):
    name = 'Plugin Backup'
    description = '一次備份或批次還原第三方外掛與啟用狀態，可選是否包含設定。'
    author = 'SamLiao & Codex'
    version = (0, 1)
    minimum_calibre_version = (9, 19, 0)
    supported_platforms = ['windows', 'osx', 'linux']
    actual_plugin = 'calibre_plugins.plugin_backup.ui:PluginBackupAction'
