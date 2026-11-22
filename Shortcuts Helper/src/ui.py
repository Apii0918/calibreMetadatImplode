__license__   = 'GPL v3'
__copyright__ = '2026, Comfy.n'
__docformat__ = 'restructuredtext en'

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import Application
import os

try:
    load_translations()
except NameError:
    pass

c_ = _

from .config import (
    ACTION_CHOICES,
    ACTION_OPEN_PREFS,
    ACTION_SHOW_CURRENT,
    get_main_action_key,
)

def _is_dark_theme():
    try:
        if QApplication is None:
            return False
        app = QApplication.instance()
        if not app:
            return False
        palette = app.palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        text_color = palette.color(QPalette.ColorRole.WindowText)
        return text_color.lightness() > window_color.lightness()
    except Exception:
        return False

def _call_get_icons(icon_name, plugin_path=None, plugin_name=None):
    gi = globals().get('get_icons', None)
    if not callable(gi):
        try:
            from calibre.customize.zipplugin import get_icons as gi  # noqa
        except Exception:
            gi = None
    if not callable(gi):
        return None

    candidates = []

    # Calibre plugins conventionally store images under images/ in the zip.
    # Some zip builders on Windows can end up with backslashes in member names.
    # Try both path separators to be safe (notably for Calibre 5.44).
    icon_name_backslash = icon_name.replace('/', '\\') if isinstance(icon_name, str) else icon_name
    icon_base = icon_name.replace('images/', '') if icon_name.startswith('images/') else icon_name
    icon_base_backslash = icon_base.replace('/', '\\') if isinstance(icon_base, str) else icon_base

    # Most common (injected) get_icons signatures
    candidates.append((icon_name,))
    if icon_name_backslash != icon_name:
        candidates.append((icon_name_backslash,))
    if icon_name.startswith('images/'):
        candidates.append((icon_base,))
        if icon_base_backslash != icon_base:
            candidates.append((icon_base_backslash,))

    # Some environments expose a get_icons that wants a plugin name
    if plugin_name:
        candidates.append((icon_name, plugin_name))
        if icon_name_backslash != icon_name:
            candidates.append((icon_name_backslash, plugin_name))
        if icon_name.startswith('images/'):
            candidates.append((icon_base, plugin_name))
            if icon_base_backslash != icon_base:
                candidates.append((icon_base_backslash, plugin_name))

    # Raw zipplugin.get_icons wants (zfp, name_or_list)
    if plugin_path:
        candidates.append((plugin_path, icon_name))
        if icon_name_backslash != icon_name:
            candidates.append((plugin_path, icon_name_backslash))
        if icon_name.startswith('images/'):
            candidates.append((plugin_path, icon_base))
            if icon_base_backslash != icon_base:
                candidates.append((plugin_path, icon_base_backslash))

    for args in candidates:
        try:
            icon = gi(*args)
            if icon is not None and hasattr(icon, 'isNull') and not icon.isNull():
                return icon
        except TypeError:
            continue
        except Exception:
            continue
    return None

def _get_plugin_icon(icon_name, plugin_path=None, plugin_name=None):
    if QIcon is None:
        return None

    # Prefer plugin-provided get_icons (injected by plugin loader on older Calibre)
    icon = _call_get_icons(icon_name, plugin_path=plugin_path, plugin_name=plugin_name)
    if icon is not None:
        return icon

    # Calibre 6+ supports QIcon.ic (theme + cache)
    try:
        ic = getattr(QIcon, 'ic', None)
        if callable(ic):
            icon = ic(icon_name)
            if icon is not None and not icon.isNull():
                return icon
    except Exception:
        pass

    # Try Calibre resource lookup (I is usually injected by the loader)
    try:
        I_func = globals().get('I', None)
        if callable(I_func):
            icon = QIcon(I_func(icon_name))
            if icon is not None and not icon.isNull():
                return icon
    except Exception:
        pass

    # Development/unzipped fallback: load from local images folder
    try:
        if QPixmap is not None:
            local_path = os.path.join(os.path.dirname(__file__), icon_name.replace('images/', 'images' + os.sep))
            if os.path.exists(local_path):
                pix = QPixmap()
                if pix.load(local_path):
                    icon = QIcon(pix)
                    if icon is not None and not icon.isNull():
                        return icon
    except Exception:
        pass

    # Last resort: try to load directly from the plugin zip file (for installed plugins)
    try:
        if plugin_path and os.path.exists(plugin_path):
            import zipfile
            with zipfile.ZipFile(plugin_path, 'r') as zf:
                # Try the icon name as is, and without 'images/' prefix
                possible_names = [icon_name]
                if icon_name.startswith('images/'):
                    possible_names.append(icon_name[len('images/'):])
                for name in possible_names:
                    try:
                        data = zf.read(name)
                        if data:
                            pix = QPixmap()
                            if pix.loadFromData(data):
                                icon = QIcon(pix)
                                if icon is not None and not icon.isNull():
                                    return icon
                    except KeyError:
                        continue
    except Exception:
        pass

    return QIcon()

from qt.core import QMenu, QAction, QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, Qt, QKeySequence, QAbstractItemView, QLineEdit, QHBoxLayout, QLabel, QIcon, QPixmap, QApplication, QCheckBox, QColor, QToolButton, QPalette
from calibre.utils.config import JSONConfig

class CurrentShortcutsDialog(QDialog):
    def __init__(self, gui, parent=None):
        super().__init__(parent)
        self.setWindowTitle(c_('Current Shortcuts'))
        # Set theme-aware icon
        icon_name = 'images/iconplugin_light.png' if not _is_dark_theme() else 'images/iconplugin_dark.png'
        icon = _get_plugin_icon(icon_name, plugin_name='Shortcuts Helper')
        if icon and not icon.isNull():
            self.setWindowIcon(icon)
        self.setModal(False)
        self.resize(700, 500)
        self.gui = gui
        self.prefs = JSONConfig('plugins/shortcuts_helper')
        layout = QVBoxLayout(self)

        # Filter layout
        filter_layout = QHBoxLayout()
        filter_label = QLabel(c_('Filter:'))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(c_('Search shortcuts...'))
        self.filter_edit.setToolTip(c_('Filter shortcuts by action, group, default, or current keys'))
        self.filter_edit.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_edit)

        # Checkbox for custom shortcuts coloring
        self.color_custom_checkbox = QCheckBox(c_('Use colour if Current is Custom'))
        self.color_custom_checkbox.setChecked(self.prefs.get('color_custom_shortcuts', True))
        self.color_custom_checkbox.stateChanged.connect(self.on_color_custom_changed)
        filter_layout.addStretch()
        filter_layout.addWidget(self.color_custom_checkbox)

        layout.addLayout(filter_layout)

        self.table = QTableWidget(self)
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        self.table.horizontalHeader().customContextMenuRequested.connect(self.on_header_context_menu)
        layout.addWidget(self.table)
        self.populate_table()

        # Apply CCR scrollbar styling
        self.setStyleSheet("""
            QScrollBar::handle {
               border: 1px solid #5B6985;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(140, 172, 204, 0.25);
                min-height: 24px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(140, 172, 204, 0.45);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-origin: margin;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(140, 172, 204, 0.25);
                min-width: 24px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(140, 172, 204, 0.45);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
            QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
                width: 0px;
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        # Restore geometry
        geom = self.prefs.get('dialog_geometry')
        if geom:
            self.restoreGeometry(geom)

        # Restore column widths
        self.restore_column_widths()

    def closeEvent(self, event):
        # Save geometry
        self.prefs['dialog_geometry'] = bytearray(self.saveGeometry())
        # Save column widths
        self.save_column_widths()
        super().closeEvent(event)

    def save_column_widths(self):
        widths = {}
        for col in range(self.table.columnCount()):
            widths[str(col)] = self.table.columnWidth(col)
        self.prefs['column_widths'] = widths

    def restore_column_widths(self):
        widths = self.prefs.get('column_widths', {})
        for col in range(self.table.columnCount()):
            w = widths.get(str(col))
            if w:
                self.table.setColumnWidth(col, w)

    def on_color_custom_changed(self, state):
        self.prefs['color_custom_shortcuts'] = bool(state)
        self.populate_table()  # Refresh to apply coloring

    def populate_table(self):
        self.table.setSortingEnabled(False)
        keyboard = getattr(self.gui, 'keyboard', None)
        if not keyboard:
            return
        # CCR logic: show only currently assigned shortcuts (filter_type == 4)
        shortcuts_list = []
        for unique_name, shortcut in keyboard.shortcuts.items():
            name = shortcut.get('name', '')
            # Group
            group = None
            try:
                for g, names in keyboard.groups.items():
                    if unique_name in names:
                        group = g
                        break
            except Exception:
                group = ''
            if not group:
                group = ''
            # Default
            default_text = 'None'
            default_keys = shortcut.get('default_keys', ()) or ()
            if default_keys:
                try:
                    pieces = []
                    for k in default_keys:
                        qs = QKeySequence(k)
                        pieces.append(qs.toString(QKeySequence.SequenceFormat.NativeText))
                    default_text = ', '.join(filter(None, pieces)) or 'None'
                except Exception:
                    default_text = ', '.join(str(x) for x in default_keys) or 'None'
            # Assigned (current)
            keys = keyboard.keys_map.get(unique_name, ())
            if keys:
                try:
                    assigned_text = ', '.join(str(k.toString(QKeySequence.SequenceFormat.NativeText)) for k in keys)
                except Exception:
                    assigned_text = ', '.join(str(k) for k in keys)
            else:
                assigned_text = 'None'
            # Only show if assigned (current) is not None
            if assigned_text and assigned_text != 'None':
                # Check if current is custom (different from default)
                is_custom = assigned_text != default_text
                shortcuts_list.append((name, group, default_text, assigned_text, is_custom))
        # Sort by group, then name
        shortcuts_list.sort(key=lambda x: (x[1].lower(), x[0].lower()))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([c_('Action'), c_('Group'), c_('Default'), c_('Current')])
        self.table.setRowCount(len(shortcuts_list))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Set up custom sorting for Current column
        self.table.horizontalHeader().setSortIndicatorShown(True)
        # Right-click menu for Current column header
        self.table.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        for row, (name, group, default_text, assigned_text, is_custom) in enumerate(shortcuts_list):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(group))
            self.table.setItem(row, 2, QTableWidgetItem(c_(default_text)))
            current_item = QTableWidgetItem(assigned_text)
            current_item.setData(Qt.ItemDataRole.UserRole, is_custom)
            if self.color_custom_checkbox.isChecked() and is_custom:
                # Use theme-appropriate color for custom shortcuts
                if _is_dark_theme():
                    # In dark theme, use a subtle blue highlight
                    current_item.setBackground(QColor(100, 150, 255, 80))  # Semi-transparent blue
                else:
                    # In light theme, use yellow
                    current_item.setBackground(Qt.GlobalColor.yellow)  # Color custom shortcuts
            self.table.setItem(row, 3, current_item)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.apply_filter(self.filter_edit.text())

    def on_header_clicked(self, logicalIndex):
        if logicalIndex == 3:  # Current column
            # Use default sorting for Current column (alphabetic)
            self.table.sortItems(logicalIndex, Qt.SortOrder.AscendingOrder)
        else:
            self.table.sortItems(logicalIndex, self.table.horizontalHeader().sortIndicatorOrder())

    def on_header_context_menu(self, pos):
        header = self.table.horizontalHeader()
        logicalIndex = header.logicalIndexAt(pos)
        if logicalIndex == 3:  # Current column
            menu = QMenu(self)

            # Sort options
            alphabetic_action = QAction(c_('Sort - Alphabetic'), self)
            alphabetic_action.triggered.connect(lambda: self.sort_current_column('alphabetic'))
            menu.addAction(alphabetic_action)

            modifier_key_action = QAction(c_('Sort - Modifier.Key'), self)
            modifier_key_action.triggered.connect(lambda: self.sort_current_column('modifier_key'))
            menu.addAction(modifier_key_action)

            key_modifier_action = QAction(c_('Sort - Key.Modifier'), self)
            key_modifier_action.triggered.connect(lambda: self.sort_current_column('key_modifier'))
            menu.addAction(key_modifier_action)

            menu.exec(header.mapToGlobal(pos))

    def sort_current_column(self, sort_type):
        # Clear filter first
        self.filter_edit.setText('')

        # Get all rows data
        self.table.setSortingEnabled(False)
        rows_data = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            group = self.table.item(row, 1).text()
            default = self.table.item(row, 2).text()
            current = self.table.item(row, 3).text()
            is_custom = bool(self.table.item(row, 3).data(Qt.ItemDataRole.UserRole))
            rows_data.append((name, group, default, current, is_custom))

        # Sort based on type
        if sort_type == 'alphabetic':
            rows_data.sort(key=lambda x: x[3].lower())  # Sort by current text
        elif sort_type == 'modifier_key':
            rows_data.sort(key=lambda x: self._get_sort_key_modifier_key(x[3]))
        elif sort_type == 'key_modifier':
            rows_data.sort(key=lambda x: self._get_sort_key_key_modifier(x[3]))

        # Re-populate table with sorted data
        self.table.setRowCount(len(rows_data))
        for row, (name, group, default_text, assigned_text, is_custom) in enumerate(rows_data):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(group))
            self.table.setItem(row, 2, QTableWidgetItem(c_(default_text)))
            current_item = QTableWidgetItem(assigned_text)
            current_item.setData(Qt.ItemDataRole.UserRole, is_custom)
            if self.color_custom_checkbox.isChecked() and is_custom:
                # Use theme-appropriate color for custom shortcuts
                if _is_dark_theme():
                    # In dark theme, use a subtle blue highlight
                    current_item.setBackground(QColor(100, 150, 255, 80))  # Semi-transparent blue
                else:
                    # In light theme, use yellow
                    current_item.setBackground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 3, current_item)

    def _get_sort_key_modifier_key(self, text):
        """Sort by Modifier.Key - groups modifiers together (Alt+something, Ctrl+something, etc.)"""
        if text == 'None':
            return ('', '')
        # Split by comma and take first shortcut
        first_shortcut = text.split(',')[0].strip()
        # Parse modifier and key
        parts = first_shortcut.replace('+', ' ').split()
        if len(parts) >= 2:
            modifier = ' '.join(parts[:-1])  # All but last part
            key = parts[-1]
            return (modifier.lower(), key.lower())
        else:
            return ('', first_shortcut.lower())

    def _get_sort_key_key_modifier(self, text):
        """Sort by Key.Modifier - groups keys together (A+Alt, A+Ctrl, etc.)"""
        if text == 'None':
            return ('', '')
        # Split by comma and take first shortcut
        first_shortcut = text.split(',')[0].strip()
        # Parse modifier and key
        parts = first_shortcut.replace('+', ' ').split()
        if len(parts) >= 2:
            modifier = ' '.join(parts[:-1])  # All but last part
            key = parts[-1]
            return (key.lower(), modifier.lower())
        else:
            return (first_shortcut.lower(), '')

    def apply_filter(self, text):
        text = text.lower().strip()
        for row in range(self.table.rowCount()):
            show = False
            if not text:  # Show all if no filter
                show = True
            else:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and text in item.text().lower():
                        show = True
                        break
            self.table.setRowHidden(row, not show)


class ShortcutsButtonAction(InterfaceAction):
    name = 'Shortcuts Helper'
    action_spec = (c_('Shortcuts Helper'), None, c_('Quick access to Calibre\'s Keyboard Shortcuts preferences and current shortcuts list'), None)
    try:
        popup_type = QToolButton.ToolButtonPopupMode.MenuButtonPopup
    except Exception:
        popup_type = QToolButton.MenuButtonPopup

    def genesis(self):
        self.rebuild_icon()
        self._setup_split_button()
        self._cleanup_shortcut_registrations()
        self._register_shortcut_actions()
        # Connect palette change listener
        try:
            app = QApplication.instance()
            if app and hasattr(app, 'palette_changed'):
                app.palette_changed.connect(self.rebuild_icon)
        except Exception:
            pass

    def rebuild_icon(self):
        icon_name = 'images/iconplugin_light.png' if not _is_dark_theme() else 'images/iconplugin_dark.png'
        icon = _get_plugin_icon(icon_name, plugin_name=self.name)
        if icon is None or icon.isNull():
            # Fallback to default
            icon = QIcon()
        self.qaction.setIcon(icon)

    def _setup_split_button(self):
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)
        self.qaction.triggered.connect(self._main_button_clicked)
        self.refresh_action_state()

    def refresh_action_state(self):
        self._rebuild_menu()
        self._apply_popup_mode()
        self._update_tooltip()

    def _apply_popup_mode(self):
        try:
            for bar in self.gui.bars_manager.bars:
                widget = bar.widgetForAction(self.qaction)
                if widget is not None:
                    widget.setPopupMode(self.popup_type)
                    widget.update()
        except Exception:
            pass

    def _rebuild_menu(self):
        self.menu.clear()
        plugin_icon = self.qaction.icon()
        configured_action = self.menu.addAction(plugin_icon, c_('Shortcuts Helper - Run configured action'))
        configured_action.triggered.connect(self._main_button_clicked)
        self.menu.addSeparator()
        prefs_action = self.menu.addAction(plugin_icon, c_('Open Shortcuts Preferences'))
        prefs_action.triggered.connect(self._show_shortcuts_prefs)
        dialog_action = self.menu.addAction(plugin_icon, c_('Show Current Shortcuts'))
        dialog_action.triggered.connect(self._show_current_shortcuts)
        self.menu.addSeparator()
        config_action = self.menu.addAction(QIcon.ic('config.png'), c_('Configure plugin...'))
        config_action.triggered.connect(self.show_configuration)

    def _label_for_action(self, action_key):
        for key, label in ACTION_CHOICES:
            if key == action_key:
                return label
        return c_('Open Shortcuts Preferences')

    def _update_tooltip(self):
        label = self._label_for_action(get_main_action_key())
        self.qaction.setToolTip(c_('Direct click: {}\nUse the arrow for menu actions').format(label))

    def show_configuration(self):
        base_plugin = self.interface_action_base_plugin
        if base_plugin is not None:
            base_plugin.do_user_config(parent=self.gui)

    def _cleanup_shortcut_registrations(self):
        keyboard = getattr(self.gui, 'keyboard', None)
        if keyboard is None:
            return

        for unique_name in (
            'shortcuts_helper_prefs',
            'shortcuts_helper_dialog',
            'shortcuts_helper_open_preferences',
            'shortcuts_helper_show_current',
        ):
            try:
                keyboard.unregister_shortcut(unique_name)
            except Exception:
                pass

        for attr_name in ('_prefs_action', '_dialog_action'):
            action = getattr(self, attr_name, None)
            if action is not None:
                try:
                    self.gui.removeAction(action)
                except Exception:
                    pass
                setattr(self, attr_name, None)

        try:
            keyboard.finalize()
        except Exception:
            pass

    def _register_shortcut_actions(self):
        keyboard = getattr(self.gui, 'keyboard', None)
        if keyboard is None:
            return

        self._prefs_action = QAction(c_('Open Shortcuts Preferences'), self.gui)
        self._prefs_action.triggered.connect(self._show_shortcuts_prefs)
        self.gui.addAction(self._prefs_action)

        self._dialog_action = QAction(c_('Show Current Shortcuts'), self.gui)
        self._dialog_action.triggered.connect(self._show_current_shortcuts)
        self.gui.addAction(self._dialog_action)

        try:
            keyboard.register_shortcut(
                'shortcuts_helper_open_preferences',
                c_('Shortcuts Helper: Open Shortcuts Preferences'),
                default_keys=(),
                action=self._prefs_action,
                description=c_('Open Shortcuts Preferences'),
                group=self.name
            )
            keyboard.register_shortcut(
                'shortcuts_helper_show_current',
                c_('Shortcuts Helper: Show Current Shortcuts'),
                default_keys=(),
                action=self._dialog_action,
                description=c_('Show Current Shortcuts'),
                group=self.name
            )
        except Exception:
            pass

        try:
            keyboard.finalize()
        except Exception:
            pass

    def _main_button_clicked(self):
        main_action = get_main_action_key()
        if main_action == 'current':
            self._show_current_shortcuts()
        else:
            self._show_shortcuts_prefs()

    def _show_shortcuts_prefs(self):
        self.gui.iactions['Preferences'].do_config(
            initial_plugin=('Advanced', 'Keyboard'),
            close_after_initial=True
        )

    def _show_current_shortcuts(self):
        # Show the non-modal dialog
        if hasattr(self, '_current_shortcuts_dialog') and self._current_shortcuts_dialog is not None:
            try:
                self._current_shortcuts_dialog.raise_()
                self._current_shortcuts_dialog.activateWindow()
                return
            except Exception:
                pass
        self._current_shortcuts_dialog = CurrentShortcutsDialog(self.gui, parent=self.gui)
        self._current_shortcuts_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._current_shortcuts_dialog.show()
