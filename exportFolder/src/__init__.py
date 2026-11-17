from calibre.customize import InterfaceActionBase

__license__ = 'GPL v3'


class ExportFolder(InterfaceActionBase):
    name = 'Export Folder'
    description = '從書庫右鍵選單將選取的書籍匯出到預設資料夾。'
    author = 'SamLiao & Codex'
    version = (1, 2, 2)
    minimum_calibre_version = (9, 18, 0)
    supported_platforms = ['windows']
    actual_plugin = 'calibre_plugins.export_folder.ui:ExportFolderAction'
