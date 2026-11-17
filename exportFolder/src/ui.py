from functools import partial
from pathlib import Path

from calibre.ebooks import BOOK_EXTENSIONS
from calibre.ebooks.metadata.book.base import Metadata
from calibre.gui2 import choose_dir, error_dialog, gprefs
from calibre.gui2.actions import InterfaceAction
from calibre.gui2.save import Saver
from calibre.library.save_to_disk import config, get_path_components
from calibre.utils.config import JSONConfig
from qt.core import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QListWidget, QMenu, QPlainTextEdit, QPushButton, Qt,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)


prefs = JSONConfig('plugins/export_folder')
prefs.defaults['destinations'] = []
DEFAULT_TEMPLATE = '{title} - {authors}'
DEFAULT_FORMATS = 'EPUB > PDF'


def destinations():
    for entry in prefs['destinations']:
        yield (*entry, DEFAULT_TEMPLATE, DEFAULT_FORMATS) if len(entry) == 2 else entry


class TemplateVariable(QLabel):
    def __init__(self, field, editor, parent):
        super().__init__('{' + field + '}', parent)
        self.editor = editor
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip('按兩下插入變數')

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.editor.insertPlainText(self.text())
            self.editor.setFocus()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class FormatPriorityDialog(QDialog):
    def __init__(self, parent, formats):
        super().__init__(parent)
        self.setWindowTitle('編輯格式優先順序')
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('從上往下選用第一個可用格式。拖曳可調整順序。', self))
        self.priority = QListWidget(self)
        self.priority.addItems([fmt.strip().upper() for fmt in formats.split('>') if fmt.strip()])
        self.priority.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        layout.addWidget(self.priority)

        controls = QHBoxLayout()
        layout.addLayout(controls)
        self.candidates = QComboBox(self)
        self.candidates.addItems(sorted({fmt.upper() for fmt in BOOK_EXTENSIONS}))
        controls.addWidget(self.candidates, 1)
        add = QPushButton('新增格式', self)
        add.clicked.connect(self.add_format)
        controls.addWidget(add)
        remove = QPushButton('移除格式', self)
        remove.clicked.connect(self.remove_format)
        controls.addWidget(remove)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        self.confirm = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.confirm.setEnabled(self.priority.count() > 0)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add_format(self):
        fmt = self.candidates.currentText()
        if fmt not in self.formats():
            self.priority.addItem(fmt)
            self.priority.setCurrentRow(self.priority.count() - 1)
            self.confirm.setEnabled(True)

    def remove_format(self):
        row = self.priority.currentRow()
        if row >= 0:
            self.priority.takeItem(row)
        self.confirm.setEnabled(self.priority.count() > 0)

    def formats(self):
        return [self.priority.item(row).text() for row in range(self.priority.count())]


class DestinationsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('管理輸出資料夾')
        self.resize(960, 360)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(['選單名稱', '輸出路徑', '輸出範本', '格式優先順序'])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 145)
        layout.addWidget(self.table)
        tools = QHBoxLayout()
        for label, callback in (
            ('新增', self.add_destination),
            ('瀏覽…', self.browse),
            ('刪除', self.remove_destination),
        ):
            button = QPushButton(label, self)
            button.clicked.connect(callback)
            tools.addWidget(button)
        tools.addStretch()
        layout.addLayout(tools)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText('儲存')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('取消')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        for entry in destinations():
            self.append_row(*entry)

    def append_row(self, name, folder, template=DEFAULT_TEMPLATE, formats=DEFAULT_FORMATS):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, value in enumerate((name, folder)):
            self.table.setItem(row, column, QTableWidgetItem(value))
        for column, value, edit in (
            (2, template, self.edit_template),
            (3, formats, self.edit_formats),
        ):
            button = QPushButton(value.replace('&', '&&'), self.table)
            button.setProperty('value', value)
            button.clicked.connect(partial(self.edit_cell, button, edit))
            self.table.setCellWidget(row, column, button)
        return row

    def edit_cell(self, button, edit):
        self.table.setCurrentIndex(self.table.indexAt(button.pos()))
        edit(button)

    def edit_template(self, button):
        gui = self.parent()
        selected = gui.library_view.get_selected_ids()
        book_id = selected[0] if selected else 1
        metadata = (gui.current_db.new_api.get_metadata(book_id) if selected
                    else Metadata('範例書名', ['範例作者']))
        opts = config().parse()
        dialog = QDialog(self)
        dialog.setWindowTitle('編輯輸出範本')
        dialog.resize(560, 0)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel('可用 {title} 代表書名、{authors} 代表作者，使用 / 建立子資料夾。', dialog))
        editor = QPlainTextEdit(button.property('value'), dialog)
        editor.setAccessibleName('輸出範本')
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        margins = editor.contentsMargins()
        editor.setFixedHeight(
            3 * editor.fontMetrics().lineSpacing() + margins.top() + margins.bottom()
            + round(2 * editor.document().documentMargin())
        )
        layout.addWidget(editor)
        preview = QLabel(dialog)
        preview.setTextFormat(Qt.TextFormat.PlainText)
        preview.setWordWrap(True)
        layout.addWidget(preview)
        layout.addWidget(QLabel('可用的變數（按兩下插入）', dialog))
        fields = QGridLayout()
        layout.addLayout(fields)
        for index, (field, description) in enumerate((
            ('title', '書名'), ('authors', '作者'),
            ('author_sort', '作者排序'), ('series', '系列'),
            ('series_index', '系列編號'), ('id', '書庫編號'),
            ('isbn', 'ISBN'), ('languages', '語言'),
            ('publisher', '出版社'), ('pubdate', '出版日期'),
            ('pages', '頁數'), ('rating', '評等'),
            ('tags', '標籤'), ('timestamp', '加入日期'),
            ('last_modified', '最後修改日期'), ('#欄位名稱', '自訂欄位的查詢名稱'),
        )):
            row, column = divmod(index, 2)
            token = TemplateVariable(field, editor, dialog)
            fields.addWidget(token, row, column * 2)
            fields.addWidget(QLabel(description, dialog), row, column * 2 + 1)
        fields.setColumnStretch(1, 1)
        fields.setColumnStretch(3, 1)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=dialog,
        )
        confirm = buttons.button(QDialogButtonBox.StandardButton.Ok)
        confirm.setText('確定')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('取消')
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        def update_preview():
            opts.template = editor.toPlainText().strip()
            confirm.setEnabled(bool(opts.template))
            if not opts.template:
                preview.setText('請輸入輸出範本。')
                return
            try:
                path = '/'.join(get_path_components(opts, metadata, book_id, 200))
            except Exception:
                preview.setText('無法預覽此範本。')
            else:
                preview.setText(f'檔名預覽（不含副檔名）\n{path}')

        editor.textChanged.connect(update_preview)
        update_preview()
        if dialog.exec():
            value = editor.toPlainText().strip()
            button.setProperty('value', value)
            button.setText(value.replace('&', '&&'))

    def edit_formats(self, button):
        dialog = FormatPriorityDialog(self, button.property('value'))
        if dialog.exec():
            value = ' > '.join(dialog.formats())
            button.setProperty('value', value)
            button.setText(value)

    def add_destination(self):
        row = self.append_row('', '')
        self.table.setCurrentCell(row, 0)
        self.table.editItem(self.table.item(row, 0))

    def browse(self):
        row = self.table.currentRow()
        if row < 0:
            return
        folder = choose_dir(self, 'export-folder-destination', '選擇輸出資料夾')
        if folder:
            self.table.item(row, 1).setText(folder)

    def remove_destination(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def accept(self):
        entries = []
        names = set()
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text().strip()
            folder = self.table.item(row, 1).text().strip()
            template = self.table.cellWidget(row, 2).property('value')
            formats = self.table.cellWidget(row, 3).property('value')
            if not name or name.casefold() in names or not Path(folder).is_absolute():
                error_dialog(
                    self, '無法儲存設定',
                    f'第 {row + 1} 列需要不重複的名稱與完整資料夾路徑。',
                    show=True,
                )
                return
            names.add(name.casefold())
            entries.append([name, folder, template, formats])
        prefs['destinations'] = entries
        super().accept()


class ExportFolderAction(InterfaceAction):
    name = 'Export Folder'
    action_spec = ('匯出到…', 'save.png', '將選取的書籍匯出到預設資料夾', None)
    action_type = 'current'
    dont_add_to = frozenset({'context-menu-device', 'toolbar-device'})

    def genesis(self):
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)
        self.qaction.triggered.connect(self.manage_destinations)
        self.rebuild_menu()

    def location_selected(self, loc):
        self.qaction.setEnabled(loc == 'library')

    def initialization_complete(self):
        if prefs.get('context_menu_configured'):
            return
        changed = False
        for suffix in ('', '-split', '-cover-browser'):
            key = 'action-layout-context-menu' + suffix
            actions = list(gprefs[key])
            if self.name in actions:
                continue
            index = actions.index('Remove Books') if 'Remove Books' in actions else len(actions)
            actions.insert(index, self.name)
            gprefs[key] = tuple(actions)
            changed = True
        if changed:
            self.gui.build_context_menus()
        prefs['context_menu_configured'] = True

    def rebuild_menu(self):
        self.menu.clear()
        for name, folder, template, formats in destinations():
            action = self.menu.addAction(name.replace('&', '&&'))
            action.triggered.connect(partial(self.export, name, folder, template, formats))
        if prefs['destinations']:
            self.menu.addSeparator()
        self.menu.addAction('管理輸出資料夾…', self.manage_destinations)

    def manage_destinations(self):
        if DestinationsDialog(self.gui).exec():
            self.rebuild_menu()

    def export(self, name, folder, template, formats, checked=False):
        if self.gui.current_view() is not self.gui.library_view:
            return
        try:
            path = Path(folder).resolve(strict=True)
            library = Path(self.gui.current_db.library_path).resolve()
            if not path.is_dir() or path.is_relative_to(library):
                raise ValueError('請選擇書庫以外的資料夾。')
        except (OSError, RuntimeError, ValueError) as err:
            error_dialog(self.gui, '無法匯出', f'{name}\n{folder}\n{err}', show=True)
            return
        priority = tuple(fmt.strip().lower() for fmt in formats.split('>'))

        class DestinationSaver(Saver):
            def __init__(self, book_ids, db, opts, root, parent=None, pool=None):
                opts.template = template
                opts.formats = 'all'
                opts.save_cover = opts.write_opf = opts.save_extra_files = False
                super().__init__(book_ids, db, opts, root, parent=parent, pool=pool)

            def collect_data(self, book_id):
                super().collect_data(book_id)
                metadata, components, available = self.collected_data[book_id]
                chosen = next((fmt for fmt in priority if fmt in available), None)
                if chosen is None:
                    del self.collected_data[book_id]
                    self.errors[book_id].append(('critical', f'沒有符合匯出順序的格式（{formats}）。'))
                    return
                self.collected_data[book_id] = (metadata, components, {chosen})

        self.gui.iactions['Save To Disk'].save_to_disk(
            checked, path=str(path), saver_class=DestinationSaver,
        )
