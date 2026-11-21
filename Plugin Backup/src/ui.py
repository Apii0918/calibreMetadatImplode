import json
import tempfile
from datetime import datetime
from pathlib import Path

from calibre.gui2 import error_dialog, gprefs
from calibre.gui2.actions import InterfaceAction
from calibre.utils.config import prefs
from calibre.utils.ipc.launch import Worker
from qt.core import (QApplication, QCheckBox, QDialog, QDialogButtonBox, QEvent, QFileDialog, QHBoxLayout,
                     QLabel, QPlainTextEdit, QProcess, QProgressBar, QPushButton,
                     QObject, QTableWidget, QTableWidgetItem, Qt, QVBoxLayout)

from .core import inspect_backup, installed_plugins


def version_text(version):
    return '.'.join(map(str, version)) if version else '未知／載入失敗'


class ImportDialog(QDialog):
    def __init__(self, parent, manifest, installed):
        super().__init__(parent)
        self.setWindowTitle('確認匯入外掛')
        self.resize(760, 480)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('將安裝以下外掛並還原其啟用狀態。同名外掛會被覆蓋，其他外掛保留。', self))
        entries = manifest['plugins']
        table = QTableWidget(len(entries), 4, self)
        table.setHorizontalHeaderLabels(['外掛', '備份版本', '目前版本', '操作'])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, entry in enumerate(entries):
            current = installed.get(entry['name'])
            action = '覆蓋'
            if current is None:
                action = '新增'
            elif entry['version'] and current['version'] and tuple(entry['version']) < tuple(current['version']):
                action = '覆蓋（降版）'
            for col, value in enumerate((entry['name'], version_text(entry['version']),
                                         version_text(current['version']) if current else '未安裝', action)):
                table.setItem(row, col, QTableWidgetItem(value))
        table.horizontalHeader().setStretchLastSection(True)
        table.resizeColumnsToContents()
        layout.addWidget(table)
        self.settings = QCheckBox('一併還原設定（覆蓋目前設定，保留這台電腦的書庫位置）', self)
        self.settings.setEnabled('settings' in manifest)
        layout.addWidget(self.settings)
        layout.addWidget(QLabel('備份包含設定，可選擇是否還原。' if 'settings' in manifest else '此備份未包含設定。', self))
        note = QLabel('匯入後需重新啟動 calibre。請只匯入您信任的外掛備份。', self)
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        self.import_button = buttons.addButton(f'匯入 {len(entries)} 支外掛', QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class BackupDialog(QDialog):
    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self.process = None
        self.temporary = None
        self.output = b''
        self.setWindowTitle('外掛備份與還原')
        self.resize(720, 600)
        layout = QVBoxLayout(self)
        self.heading = QLabel(self)
        layout.addWidget(self.heading)
        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(['全選', '第三方外掛', '版本', '狀態'])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.horizontalHeader().sectionClicked.connect(self.toggle_all)
        self.table.horizontalHeaderItem(0).setToolTip('按一下全選，再按一次取消全選')
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.include_settings = QCheckBox('一併備份設定（勾選匯出：所選外掛；全部匯出：完整設定）', self)
        layout.addWidget(self.include_settings)
        note = QLabel('勾選匯出只含可辨識的專用設定；共用或動態路徑設定請用完整備份。設定可能含帳號或 API 金鑰，請妥善保管。書庫與書檔不在範圍。', self)
        note.setWordWrap(True)
        layout.addWidget(note)
        self.selected_button = QPushButton('匯出勾選', self)
        self.selected_button.clicked.connect(lambda: self.export_plugins(selected=True))
        row = QHBoxLayout()
        row.addWidget(self.selected_button)
        self.export_button = QPushButton('匯出全部', self)
        self.import_button = QPushButton('匯入備份', self)
        self.export_button.clicked.connect(self.export_plugins)
        self.import_button.clicked.connect(self.import_plugins)
        row.addWidget(self.export_button)
        layout.addLayout(row)
        layout.addWidget(self.import_button)
        self.progress = QProgressBar(self)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.status = QLabel('就緒。', self)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.details = QPlainTextEdit(self)
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(130)
        self.details.hide()
        layout.addWidget(self.details)
        footer = QHBoxLayout()
        self.restart_button = QPushButton('重新啟動 calibre', self)
        self.restart_button.hide()
        self.restart_button.clicked.connect(lambda: self.gui.quit(restart=True))
        self.close_button = QPushButton('關閉', self)
        self.close_button.clicked.connect(self.reject)
        footer.addWidget(self.restart_button)
        footer.addStretch()
        footer.addWidget(self.close_button)
        layout.addLayout(footer)
        self.refresh()

    def toggle_all(self, column):
        if column != 0 or self.process is not None:
            return
        checked = all(self.table.item(row, 0).checkState() == Qt.CheckState.Checked
                      for row in range(self.table.rowCount()))
        state = Qt.CheckState.Unchecked if checked else Qt.CheckState.Checked
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(state)

    def refresh(self):
        self.plugins = installed_plugins()
        self.heading.setText(f'目前安裝 {len(self.plugins)} 支第三方外掛（包含停用或載入失敗的外掛）。')
        self.table.setRowCount(len(self.plugins))
        for row, plugin in enumerate(self.plugins):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(row, 0, item)
            for col, value in enumerate((plugin['name'], version_text(plugin['version']), '啟用' if plugin['enabled'] else '停用')):
                self.table.setItem(row, col + 1, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def export_plugins(self, checked=False, selected=False):
        names = [p['name'] for row, p in enumerate(self.plugins)
                 if self.table.item(row, 0).checkState() == Qt.CheckState.Checked] if selected else None
        if selected and not names:
            self.status.setText('請先勾選要匯出的外掛。')
            return
        if not self.plugins:
            self.status.setText('目前沒有可匯出的第三方外掛。')
            return
        filename, _ = QFileDialog.getSaveFileName(self, '匯出外掛備份',
            'calibre-plugins-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.zip', 'ZIP 備份 (*.zip)')
        if filename:
            self.start_worker('export', filename, self.include_settings.isChecked(), names)

    def import_plugins(self):
        filename, _ = QFileDialog.getOpenFileName(self, '選擇外掛備份', '', 'ZIP 備份 (*.zip)')
        if not filename:
            return
        try:
            manifest = inspect_backup(filename)
            confirm = ImportDialog(self, manifest, {p['name']: p for p in self.plugins})
            if confirm.exec() == QDialog.DialogCode.Accepted:
                self.start_worker('import', filename, confirm.settings.isChecked())
        except Exception as error:
            error_dialog(self, '無法匯入', '備份檢查失敗。', det_msg=str(error), show=True)

    def set_busy(self, busy):
        self.table.setEnabled(not busy)
        self.selected_button.setEnabled(not busy)
        self.export_button.setEnabled(not busy)
        self.import_button.setEnabled(not busy)
        self.include_settings.setEnabled(not busy)
        self.close_button.setEnabled(not busy)
        self.restart_button.setEnabled(not busy)
        self.progress.setVisible(busy)

    def start_worker(self, mode, filename, include_settings, names=None):
        if self.process is not None:
            return
        self.mode, self.filename = mode, filename
        self.temporary = tempfile.TemporaryDirectory(prefix='calibre-plugin-backup-')
        self.report = Path(self.temporary.name) / 'result.json'
        self.output = b''
        self.details.clear()
        self.details.hide()
        self.set_busy(True)
        self.progress.setRange(0, 0)
        self.status.setText('正在準備…')
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_progress)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        worker = Worker()
        worker.exe_name = 'calibre-debug'
        executable = worker.executable
        command = [executable] if isinstance(executable, str) else list(executable)
        self.process.start(command[0], command[1:] + ['-c',
            'import calibre.customize.ui; from calibre_plugins.plugin_backup.core import worker; worker()',
            mode, filename, str(self.report), '1' if include_settings else '0', json.dumps(names)])

    def read_progress(self):
        self.output += bytes(self.process.readAllStandardOutput())
        lines = self.output.split(b'\n')
        self.output = lines.pop()[-8192:]
        for line in lines:
            if line.startswith(b'PLUGIN_BACKUP_PROGRESS '):
                try:
                    done, total, name = json.loads(line.split(b' ', 1)[1])
                    self.progress.setRange(0, total)
                    self.progress.setValue(done)
                    self.status.setText(f'{done} / {total}　{name}')
                except (ValueError, TypeError):
                    pass

    def process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.finished(-1)

    def finished(self, code, *args):
        if self.process is None:
            return
        try:
            if code != 0 or not self.report.is_file():
                raise RuntimeError('背景作業未完成，請檢查備份檔與安裝目錄。')
            result = json.loads(self.report.read_text('utf-8'))
            failed = result['failed']
            if self.mode == 'export':
                if failed:
                    self.status.setText('匯出失敗，原有備份保留。')
                else:
                    self.status.setText(f"已匯出 {result['exported']} 支外掛" + ('及設定' if result['settings_included'] else '') + f'。\n{self.filename}')
            else:
                from calibre.customize.ui import config
                config.refresh()
                if result.get('settings_restored'):
                    gprefs.refresh()
                    prefs.refresh()
                self.gui.must_restart_before_config = True
                self.restart_button.show()
                self.status.setText(f"已匯入 {len(result['installed'])} 支外掛，失敗 {len(failed)} 支。請重新啟動 calibre。"
                    + ('\n設定已還原。' if result.get('settings_restored') else '\n設定未還原。'))
            if failed:
                self.details.setPlainText('\n'.join(f"{item['name']}：{item['error']}" for item in failed))
                self.details.show()
        except Exception as error:
            self.status.setText('作業失敗。若已開始匯入，請重新啟動 calibre 再檢查安裝清單。')
            self.details.setPlainText(str(error))
            self.details.show()
        finally:
            self.process.deleteLater()
            self.process = None
            self.temporary.cleanup()
            self.temporary = None
            self.set_busy(False)

    def reject(self):
        if self.process is None:
            super().reject()

    def closeEvent(self, event):
        if self.process is not None:
            event.ignore()
        else:
            super().closeEvent(event)


class PluginBackupAction(InterfaceAction):
    name = 'Plugin Backup'
    dont_add_to = frozenset(('toolbar', 'toolbar-device', 'toolbar-child', 'menubar', 'menubar-device',
                             'context-menu', 'context-menu-device', 'context-menu-cover-browser',
                             'context-menu-split', 'searchbar'))
    action_spec = ('外掛備份', 'save.png', '一次匯出或批次匯入第三方外掛，可選是否包含設定', None)

    def genesis(self):
        self.qaction.setVisible(False)
        self.qaction.triggered.connect(self.open_backup)
        self.preferences_entry = PreferencesEntry(self)
        QApplication.instance().installEventFilter(self.preferences_entry)

    def open_backup(self):
        BackupDialog(self.gui).exec()


class PreferencesEntry(QObject):
    def __init__(self, action):
        super().__init__(action.gui)
        self.action = action

    def eventFilter(self, watched, event):
        if event.type() not in (QEvent.Type.Show, QEvent.Type.Hide):
            return False
        from calibre.gui2.preferences.plugins import ConfigWidget
        if isinstance(watched, ConfigWidget) and event.type() in (QEvent.Type.Show, QEvent.Type.Hide):
            window = watched.window()
            if hasattr(window, 'bb') and isinstance(window.bb, QDialogButtonBox):
                button = getattr(window, '_plugin_backup_button', None)
                if button is None and event.type() == QEvent.Type.Show:
                    button = QPushButton('匯出／匯入外掛…', window)
                    button.setAutoDefault(False)
                    window.bb.addButton(button, QDialogButtonBox.ButtonRole.ActionRole)
                    button.clicked.connect(lambda: BackupDialog(self.action.gui).exec())
                    window._plugin_backup_button = button
                if button is not None:
                    button.setVisible(event.type() == QEvent.Type.Show)
        return False
