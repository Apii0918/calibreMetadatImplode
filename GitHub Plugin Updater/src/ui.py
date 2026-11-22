import json
import tempfile
from pathlib import Path

from calibre.gui2 import error_dialog, info_dialog, open_local_file
from calibre.gui2.actions import InterfaceAction
from calibre.utils.config import JSONConfig, config_dir
from calibre.utils.ipc.launch import Worker
from qt.core import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPlainTextEdit, QProcess,
                     QPushButton, QTableWidget, QTableWidgetItem, Qt, QVBoxLayout, QMessageBox)

from .core import DEFAULT_REPO, installed_plugins, repository


class UpdaterDialog(QDialog):
    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self.setWindowTitle('GitHub 外掛更新器 0.1')
        self.resize(1000, 650)
        self.prefs = JSONConfig('plugins/github_plugin_updater')
        self.rows, self.process, self.temporary = [], None, None
        self.restart_required = bool(getattr(gui, '_github_plugin_updater_updated', False))
        layout = QVBoxLayout(self)
        note = QLabel('先比對清單與本機身分檔的內容 SHA-256，不同才比較版號。勾選並確認後才下載；安裝前備份舊包與外掛登錄設定。', self)
        note.setWordWrap(True)
        layout.addWidget(note)
        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels(['勾選', '外掛', '目前版號', '來源版號', 'GitHub 來源', '狀態'])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        row = QHBoxLayout()
        self.sources_button = QPushButton('管理來源', self)
        self.sources_button.clicked.connect(self.edit_sources)
        self.check_button = QPushButton('檢查更新', self)
        self.check_button.clicked.connect(self.check)
        self.bind_button = QPushButton('綁定勾選來源', self)
        self.bind_button.clicked.connect(self.bind)
        self.install_button = QPushButton('更新勾選', self)
        self.install_button.clicked.connect(self.install_selected)
        self.backups_button = QPushButton('開啟備份資料夾', self)
        self.backups_button.clicked.connect(self.open_backups)
        for button in (self.sources_button, self.check_button, self.bind_button, self.install_button, self.backups_button):
            row.addWidget(button)
        layout.addLayout(row)
        self.status = QLabel('請先管理來源或按「檢查更新」。未綁定的舊包需勾選後指定來源。', self)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.details = QPlainTextEdit(self)
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(140)
        layout.addWidget(self.details)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        self.restart_button = QPushButton('重新啟動 calibre', self)
        self.restart_button.setEnabled(self.restart_required)
        self.restart_button.clicked.connect(self.restart)
        buttons.addButton(self.restart_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.rejected.connect(self.reject)
        self.close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        layout.addWidget(buttons)

    def restart(self):
        if self.restart_required and self.restart_button.isEnabled() and self.process is None and self.gui is not None:
            self.gui.quit(restart=True)

    def edit_sources(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('管理 GitHub 來源')
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel('每行一個 owner/repo 或 GitHub 庫網址；來源必須在正式 Release 提供 plugins.json。\n加入來源代表信任該來源的程式。只支援公開庫；移除來源不會移除外掛或切換綁定。', dialog))
        text = QPlainTextEdit(dialog)
        text.setPlainText('\n'.join(self.prefs.get('sources', [DEFAULT_REPO])))
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                sources = list(dict((repository(line).lower(), repository(line)) for line in text.toPlainText().splitlines() if line.strip()).values())
                if len(sources) > 30:
                    raise ValueError('來源最多 30 個。')
                self.prefs['sources'] = sources
                self.rows = []
                self.show_rows()
            except Exception as error:
                error_dialog(self, '來源無效', str(error), show=True)

    def selected(self):
        return [entry for row, entry in enumerate(self.rows)
                if self.table.item(row, 0).checkState() == Qt.CheckState.Checked]

    def show_rows(self):
        self.table.setRowCount(len(self.rows))
        for row, entry in enumerate(self.rows):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            if entry['current'] is None:
                item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(row, 0, item)
            current = '.'.join(map(str, entry['current'])) if entry['current'] else '未安裝／載入失敗'
            for col, value in enumerate((entry['name'], current, '.'.join(map(str, entry['version'])), entry['repo'], entry['status']), 1):
                self.table.setItem(row, col, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def bind(self):
        entries = self.selected()
        if not entries:
            return
        if len({e['name'] for e in entries}) != len(entries):
            error_dialog(self, '來源重複', '同一支外掛一次只能綁定一個來源。', show=True)
            return
        text = '\n'.join(f"{e['name']} → {e['repo']}" for e in entries)
        if QMessageBox.question(self, '確認追蹤來源', text + '\n將取代原綁定；官方更新器仍可能更新同名外掛。是否繼續？') != QMessageBox.StandardButton.Yes:
            return
        current = installed_plugins()
        bindings = dict(self.prefs.get('bindings', {}))
        for entry in entries:
            local = current.get(entry['name'])
            if local and local['sha256'] == entry['observed_sha256']:
                bindings[entry['name']] = {'source': entry['source'], 'id': entry['id'], 'accepted_sha256': local['sha256']}
        self.prefs['bindings'] = bindings
        self.check()

    def check(self):
        if self.restart_required:
            info_dialog(self, '請重新啟動', '本次已安裝外掛，重新啟動 calibre 後再檢查。', show=True)
            return
        self.start({'mode': 'check', 'sources': self.prefs.get('sources', [DEFAULT_REPO])})

    def install_selected(self):
        entries = self.selected()
        if not entries:
            return
        if any(not e['eligible'] for e in entries):
            error_dialog(self, '無法更新', '請只勾選「可更新」項目；需要綁定時先綁定來源。同版內容不符需由來源修正版號。', show=True)
            return
        text = '\n'.join(f"{e['name']}：{e['status']}（{e['repo']}）" for e in entries)
        if QMessageBox.question(self, '確認下載與安裝', text + '\n將下載並執行所選來源的外掛程式，備份後覆蓋安裝；完成後需重啟。是否繼續？') == QMessageBox.StandardButton.Yes:
            self.start({'mode': 'install', 'entries': entries})

    def open_backups(self):
        path = Path(config_dir) / 'github-plugin-updater-backups'
        path.mkdir(exist_ok=True)
        open_local_file(str(path))

    def start(self, job):
        if self.process is not None:
            return
        self.mode = job['mode']
        self.temporary = tempfile.TemporaryDirectory(prefix='github-plugin-updater-')
        root = Path(self.temporary.name)
        (root / 'job.json').write_text(json.dumps(job, ensure_ascii=False), encoding='utf-8')
        self.report = root / 'result.json'
        self.status.setText('正在檢查清單…' if self.mode == 'check' else '正在下載、備份與安裝…')
        self.details.clear()
        for button in (self.sources_button, self.check_button, self.bind_button, self.install_button, self.close_button):
            button.setEnabled(False)
        self.restart_button.setEnabled(False)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(lambda: self.process.readAllStandardOutput())
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        worker = Worker()
        worker.exe_name = 'calibre-debug'
        command = worker.executable
        command = [command] if isinstance(command, str) else list(command)
        self.process.start(command[0], command[1:] + ['-c',
            'import calibre.customize.ui; from calibre_plugins.github_plugin_updater.core import worker; worker()',
            str(root / 'job.json'), str(self.report)])

    def process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.finished(-1, None)

    def finished(self, code, status):
        try:
            if code != 0 or not self.report.is_file():
                raise ValueError('背景工作未完成；若正在安裝，請檢查備份並重新啟動 calibre。')
            result = json.loads(self.report.read_text(encoding='utf-8'))
            if result.get('error'):
                raise ValueError(result['error'])
            self.prefs.refresh()
            if self.mode == 'check':
                self.rows = result['rows']
                self.show_rows()
                self.status.setText(f"檢查完成：{sum(e['eligible'] for e in self.rows)} 項可更新。")
                self.details.setPlainText('\n'.join(result['errors']))
            else:
                self.restart_required = bool(result['installed'])
                if self.restart_required and self.gui is not None:
                    self.gui._github_plugin_updater_updated = True
                    self.gui.must_restart_before_config = True
                self.restart_button.setEnabled(self.restart_required)
                self.rows = []
                self.show_rows()
                self.status.setText(f"已安裝 {len(result['installed'])} 支，失敗 {len(result['failed'])} 支。請重新啟動 calibre。")
                self.details.setPlainText('\n'.join(result['failed'] + ['備份：' + p for p in result['backups']]))
        except Exception as error:
            self.status.setText(str(error))
            if self.mode == 'install':
                self.restart_required = True
                self.restart_button.setEnabled(False)
        finally:
            self.process.deleteLater()
            self.process = None
            self.temporary.cleanup()
            self.temporary = None
            for button in (self.sources_button, self.check_button, self.bind_button, self.install_button, self.close_button):
                button.setEnabled(True)

    def reject(self):
        if self.process is None:
            super().reject()

    def closeEvent(self, event):
        if self.process is not None:
            event.ignore()
        else:
            super().closeEvent(event)


class UpdaterAction(InterfaceAction):
    name = 'GitHub Plugin Updater'
    action_spec = ('GitHub 外掛更新', 'plugins/plugin_updater.png', '檢查 GitHub 外掛來源並勾選更新', None)

    def genesis(self):
        self.qaction.triggered.connect(self.open_updater)

    def open_updater(self):
        UpdaterDialog(self.gui).exec()
