__license__   = 'GPL v3'
__copyright__ = '2026, Comfy.n'
__docformat__ = 'restructuredtext en'

import shlex
import os
import json
import re
import time

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import gprefs, show_restart_warning, open_url, error_dialog
from calibre.gui2.preferences import AbortCommit, get_plugin
from .column_packs import (
    build_general_help_links,
    build_helper_group_definitions,
    build_quick_create_presets,
)

try:
    from calibre.constants import numeric_version, ismacos
except Exception:
    numeric_version = (0, 0, 0)
    ismacos = False

try:
    from calibre.gui2.preferences.main import must_restart_message as _CALIBRE_MUST_RESTART_MESSAGE
except Exception:
    _CALIBRE_MUST_RESTART_MESSAGE = None

COLUMNS_HELPER_DEBUG_ENABLED = os.environ.get('COLUMNS_HELPER_DEBUG_ENABLED', '0').lower() in ('1', 'true', 'yes')
if not COLUMNS_HELPER_DEBUG_ENABLED:
    def debug_print(*args, **kwargs):
        return None
else:
    try:
        from calibre.utils.logging import prints as debug_print
    except Exception:
        def debug_print(*args, **kwargs):
            __builtins__.print(*args, **kwargs)

load_translations()

try:
    from qt.core import (
        QAction,
        QDialog,
        QDialogButtonBox,
        QEvent,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QPushButton,
        QToolButton,
        QHBoxLayout,
        QVBoxLayout,
        QWidget,
        QApplication,
        QIcon,
        QPixmap,
        QMenu,
        QShortcut,
        QKeySequence,
        QSize,
        QTreeWidget,
        QTreeWidgetItem,
        QTableWidgetItem,
        QTextBrowser,
        QTimer,
        Qt,
        QBrush,
        QColor,
        QCheckBox,
        QComboBox,
        QCompleter,
        QStringListModel,
        QSyntaxHighlighter,
        QTextCharFormat,
        QFont,
        QFontDatabase,
        QFontInfo,
        QFontMetrics,
        QPalette,
        QSplitter,
        QUrl,
        QTabWidget,
        QTabBar,
        QScrollArea,
        QFrame,
        QSizePolicy,
    )
except ImportError:
    from PyQt5.Qt import (  # type: ignore
        QAction,
        QDialog,
        QDialogButtonBox,
        QEvent,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QPushButton,
        QToolButton,
        QHBoxLayout,
        QVBoxLayout,
        QWidget,
        QApplication,
        QIcon,
        QPixmap,
        QMenu,
        QShortcut,
        QKeySequence,
        QSize,
        QTreeWidget,
        QTreeWidgetItem,
        QTableWidgetItem,
        QTextBrowser,
        QTimer,
        Qt,
        QBrush,
        QColor,
        QCheckBox,
        QComboBox,
        QCompleter,
        QStringListModel,
        QSyntaxHighlighter,
        QTextCharFormat,
        QFont,
        QFontDatabase,
        QFontInfo,
        QFontMetrics,
        QPalette,
        QSplitter,
        QUrl,
        QTabWidget,
        QTabBar,
        QScrollArea,
        QFrame,
        QSizePolicy,
    )


def _is_dark_theme():
    try:
        app = QApplication.instance()
        if not app:
            return False
        palette = app.palette()
        window_color = palette.color(palette.Window)
        text_color = palette.color(palette.WindowText)
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
    # Normalize and prefer the 'images/' path when asking calibre's get_icons
    # to avoid zipfile KeyError traces for root-level names that actually
    # live under images/ inside the plugin zip.
    icon_name = icon_name.replace('\\', '/')
    icon_name_backslash = icon_name.replace('/', '\\')
    icon_base = icon_name.replace('images/', '') if icon_name.startswith('images/') else icon_name
    icon_base_backslash = icon_base.replace('/', '\\')
    images_name = icon_name if icon_name.startswith('images/') else ('images/' + icon_name)
    images_name_backslash = images_name.replace('/', '\\')

    candidates = []
    if plugin_name:
        candidates.append((images_name, plugin_name))
        if images_name_backslash != images_name:
            candidates.append((images_name_backslash, plugin_name))
        candidates.append((icon_name, plugin_name))
        if icon_name_backslash != icon_name:
            candidates.append((icon_name_backslash, plugin_name))
        candidates.append((icon_base, plugin_name))
        if icon_base_backslash != icon_base:
            candidates.append((icon_base_backslash, plugin_name))

    candidates.append((images_name,))
    if images_name_backslash != images_name:
        candidates.append((images_name_backslash,))
    candidates.append((icon_name,))
    if icon_name_backslash != icon_name:
        candidates.append((icon_name_backslash,))
    candidates.append((icon_base,))
    if icon_base_backslash != icon_base:
        candidates.append((icon_base_backslash,))

    if plugin_path:
        candidates.append((plugin_path, images_name))
        if images_name_backslash != images_name:
            candidates.append((plugin_path, images_name_backslash))
        candidates.append((plugin_path, icon_name))
        if icon_name_backslash != icon_name:
            candidates.append((plugin_path, icon_name_backslash))
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


def _html_escape(text):
    return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def copy_to_clipboard(text):
    if not text:
        return False
    app = QApplication.instance()
    if app is None:
        return False
    cb = app.clipboard()
    if cb is None:
        return False
    cb.setText(text)
    return True


def _qt_object_is_alive(obj):
    if obj is None:
        return False
    try:
        import sip  # type: ignore
        if sip.isdeleted(obj):
            return False
    except Exception:
        pass
    try:
        if hasattr(obj, 'objectName'):
            obj.objectName()
    except RuntimeError:
        return False
    except Exception:
        pass
    return True


SHOWROOM_GEOMETRY_KEY = 'columns_helper_showroom_geometry'
SHOWROOM_BODY_SPLITTER_KEY = 'columns_helper_showroom_body_splitter_sizes'
SHOWROOM_DETAIL_SPLITTER_KEY = 'columns_helper_showroom_splitter_sizes'
SHOWROOM_ZOOM_STEPS_KEY = 'columns_helper_showroom_zoom_steps'
SHOWROOM_TREE_SORT_KEY = 'columns_helper_showroom_tree_sort'
SHOWROOM_ZOOM_STEPS_MIN = -6
SHOWROOM_ZOOM_STEPS_MAX = 8
SHOWROOM_ZOOM_BASE_UNITS = 10
SHOWROOM_ZOOM_MIN_UNITS = 4
SHOWROOM_ZOOM_MAX_UNITS = 18
_HELPER_SHOWROOM_DIALOG = None


def showroom_zoom_steps_value():
    try:
        val = int(gprefs.get(SHOWROOM_ZOOM_STEPS_KEY, 0) or 0)
    except Exception:
        val = 0
    return max(SHOWROOM_ZOOM_STEPS_MIN, min(SHOWROOM_ZOOM_STEPS_MAX, val))


def showroom_zoom_scale_units(steps=None):
    if steps is None:
        steps = showroom_zoom_steps_value()
    return max(SHOWROOM_ZOOM_MIN_UNITS, min(SHOWROOM_ZOOM_MAX_UNITS, SHOWROOM_ZOOM_BASE_UNITS + int(steps)))


def showroom_zoom_scale_factor(steps=None):
    return float(showroom_zoom_scale_units(steps)) / float(SHOWROOM_ZOOM_BASE_UNITS)


def showroom_zoom_percent_value():
    try:
        return int(round(showroom_zoom_scale_factor() * 100.0))
    except Exception:
        return 100


def _clear_helper_showroom_dialog(*args):
    global _HELPER_SHOWROOM_DIALOG
    _HELPER_SHOWROOM_DIALOG = None


def _plugin_version_text():
    try:
        from calibre_plugins.columns_helper import ColumnsHelperPlugin
        return '.'.join(str(x) for x in ColumnsHelperPlugin.version)
    except Exception:
        return '?.?.?'


def _calibre_version_text():
    try:
        return '.'.join(str(x) for x in tuple(numeric_version[:3]))
    except Exception:
        return '?.?.?'


def _restart_message_text():
    if _CALIBRE_MUST_RESTART_MESSAGE:
        return _CALIBRE_MUST_RESTART_MESSAGE
    return _(
        'Some of the changes you made require a restart. Please restart calibre as soon as possible.'
    )


def _supports_column_tooltip_templates():
    try:
        return tuple(numeric_version[:3]) >= (8, 10, 0)
    except Exception:
        return False


def _column_tooltip_placeholder_text():
    return _(
        'Tooltip template preview only.\n\n'
        'If this preset defines a tooltip template, or your library already has one for the same lookup name, it will appear here.\n\n'
        'Template globals include "{0}" for the column lookup name and "{1}" for the original tooltip text. Tooltip templates are available in calibre 8.10+.'
    ).format('column_lookup_name', 'original_text')


def _get_close_action_icon():
    try:
        icon = QIcon.ic('window-close.png')
        if icon is not None and not icon.isNull():
            return icon
    except Exception:
        pass
    try:
        icon = QIcon.ic('close.png')
        if icon is not None and not icon.isNull():
            return icon
    except Exception:
        pass
    return None


def _qt_menu_text(text):
    return str(text or '').replace('&', '&&')


def _ccr_scrollbar_stylesheet():
    return """
    QScrollBar::handle {
       border: 1px solid #5B6985;
    }
    QScrollBar:vertical {
        background: transparent;
        width: 12px;
        margin: 0px 0px 0px 0px;
        padding: 6px 0px 6px 0px;
    }
    QScrollBar::handle:vertical {
        background: rgba(140, 172, 204, 0.25);
        min-height: 22px;
        border-radius: 4px;
        margin: 4px 0px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(140, 172, 204, 0.45);
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 12px;
        margin: 0px 0px 0px 0px;
        padding: 0px 6px 0px 6px;
    }
    QScrollBar::handle:horizontal {
        background: rgba(140, 172, 204, 0.25);
        min-width: 22px;
        border-radius: 4px;
        margin: 0px 4px;
    }
    QScrollBar::handle:horizontal:hover {
        background: rgba(140, 172, 204, 0.45);
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
    """


def _ccr_combo_stylesheet():
    return '''
QComboBox {
    border: 1px solid #6B6C6B;
    min-height: 20px;
}
QComboBox:focus {
    border: 1px solid #1976D2;
}

'''


def _ccr_lineedit_stylesheet():
    return '''
QLineEdit {
    border: 1px solid #6B6C6B;
    min-height: 20px;
}
QLineEdit:focus {
    border: 1px solid #1976D2;
}

'''


def _ccr_tabs_stylesheet():
    try:
        app = QApplication.instance()
        palette = app.palette() if app is not None else None
        if palette is not None:
            text_color = palette.color(QPalette.ColorRole.WindowText)
            tab_text_color = text_color.name() if text_color.isValid() else '#777777'
        else:
            tab_text_color = '#777777'
    except Exception:
        tab_text_color = '#777777'

    return """
    QTabWidget::pane {
        border-top: none;
        margin-left: 2px;
        margin-right: 2px;
    }
    QTabBar::tab {
        padding-top: 6px;
        padding-bottom: 6px;
        padding-left: 12px;
        padding-right: 12px;
        font-size: 10pt;
        background: transparent;
        border-top: 1px solid palette(mid);
        border-left: 1px solid palette(mid);
        border-right: 1px solid palette(mid);
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        min-width: 100px;
        margin-left: 1px;
        margin-right: 1px;
        font-style: normal;
    }
    QTabBar::tab:selected {
        font-weight: bold;
        font-style: normal;
        border-top: 2px solid palette(link);
        border-left: 2px solid palette(link);
        border-right: 2px solid palette(link);
        color: palette(link);
    }
    QTabBar::tab:!selected {
        color: palette(text);
        margin-top: 2px;
        border-top: 1px solid """ + tab_text_color + """;
        border-left: 1px solid """ + tab_text_color + """;
        border-right: 1px solid """ + tab_text_color + """;
        font-style: normal;
    }
    """


def _external_link_pixmap(size=14):
    try:
        if hasattr(QIcon, 'ic'):
            ic = QIcon.ic('external-link.png')
            if ic and not ic.isNull():
                pm = ic.pixmap(size, size)
                if pm and not pm.isNull():
                    return pm
    except Exception:
        pass
    try:
        from calibre.utils.resources import get_image_path
        p = get_image_path('external-link.png')
        if p:
            pm = QPixmap(p)
            if not pm.isNull():
                aspect = getattr(Qt.AspectRatioMode, 'KeepAspectRatio', getattr(Qt, 'KeepAspectRatio', 1))
                smooth = getattr(Qt.TransformationMode, 'SmoothTransformation', getattr(Qt, 'SmoothTransformation', 1))
                return pm.scaled(size, size, aspect, smooth)
    except Exception:
        pass
    return None


class NoUnderlineLinkLabel(QLabel):
    def __init__(self, text, url, parent=None):
        QLabel.__init__(self, text, parent)
        self._url = url
        try:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        except Exception:
            self.setCursor(Qt.PointingHandCursor)
        try:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        except Exception:
            self.setTextInteractionFlags(Qt.TextBrowserInteraction)

    def mousePressEvent(self, event):
        button = event.button() if hasattr(event, 'button') else None
        left = getattr(Qt.MouseButton, 'LeftButton', getattr(Qt, 'LeftButton', 1))
        if button == left:
            open_url(self._url)
        QLabel.mousePressEvent(self, event)


class ElidedDescriptionLabel(QLabel):
    def __init__(self, text, parent=None):
        QLabel.__init__(self, parent)
        self._full_text = text
        self.setToolTip(text)
        try:
            self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        except Exception:
            self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumWidth(0)

    def resizeEvent(self, event):
        QLabel.resizeEvent(self, event)
        elide_mode = getattr(Qt.TextElideMode, 'ElideRight', getattr(Qt, 'ElideRight', 1))
        self.setText(self.fontMetrics().elidedText(
            self._full_text, elide_mode, max(0, self.width())))


MORE_PLUGINS_DATA = (
    ('AI Config', _('Quick access to AI settings'), 'https://www.mobileread.com/forums/showthread.php?t=371037'),
    ('BERTRAND Livreiros', _('Metadata and covers from BERTRAND'), 'https://www.mobileread.com/forums/showthread.php?t=374669'),
    ('Best Sellers', _('Book Catalogs, Blurb & Review Finders'), 'https://www.mobileread.com/forums/showthread.php?t=374278'),
    ('Book List Plus', _('Book list view with covers'), 'https://www.mobileread.com/forums/showthread.php?t=373100'),
    ('Calibre Config Reports', _('Configuration reporting tool'), 'https://www.mobileread.com/forums/showthread.php?t=369555'),
    ('Chapter Summarizer', _('Powerful document summarizer'), 'https://www.mobileread.com/forums/showthread.php?t=374061'),
    ('Columns Helper', _('Columns management tools'), 'https://www.mobileread.com/forums/showthread.php?t=372614'),
    ('Comfy Reminders', _('Create and manage reminders'), 'https://www.mobileread.com/forums/showthread.php?t=367258'),
    ('Current Paths', _('Show config/library paths'), 'https://www.mobileread.com/forums/showthread.php?t=371623'),
    ('Custom Action Button', _('Configurable toolbar button'), 'https://www.mobileread.com/forums/showthread.php?t=374301'),
    ('DELFI knjižare', _('Downloads metadata and covers from DELFI'), 'https://www.mobileread.com/forums/showthread.php?t=374478'),
    ('Extended Book Details', _('Book Details on left panel'), 'https://www.mobileread.com/forums/showthread.php?t=372675'),
    ('FTS+', _('FTS with additional features'), 'https://www.mobileread.com/forums/showthread.php?t=372481'),
    ('Goldendict Bridge', _('Multiple dictionary local lookup'), 'https://www.mobileread.com/forums/showthread.php?t=372546'),
    ('Input Order Swap', _('Swap top two input formats'), 'https://www.mobileread.com/forums/showthread.php?t=371116'),
    ('KoboTouch Config Button', _('Quick access to Kobo config'), 'https://www.mobileread.com/forums/showthread.php?t=367728'),
    ('Language Switcher', _('Quick-switch Calibre language'), 'https://www.mobileread.com/forums/showthread.php?t=372153'),
    ('Look & Feel Button', _('Quick access to Look & Feel'), 'https://www.mobileread.com/forums/showthread.php?t=372670'),
    ('Metadata Sources Preview', _('Preview metadata providers'), 'https://www.mobileread.com/forums/showthread.php?t=373625'),
    ('Open Config Folder', _('Open config folder'), 'https://www.mobileread.com/forums/showthread.php?t=372023'),
    ('OPF Helper', _('Toolkit for all things OPF'), 'https://www.mobileread.com/forums/showthread.php?t=371086'),
    ('Output Format Cycler', _('Cycle output format'), 'https://www.mobileread.com/forums/showthread.php?t=371117'),
    ('Quick Palette Customize', _('Quick access to palette config'), 'https://www.mobileread.com/forums/showthread.php?t=372047'),
    ('Review Nook', _('Keep your own book reviews in calibre'), 'https://www.mobileread.com/forums/showthread.php?t=375545'),
    ('RSS Reader', _('Read RSS/Atom feeds inside calibre'), 'https://www.mobileread.com/forums/showthread.php?t=371755'),
    ('Shortcuts Helper', _('Quick access to Shortcuts'), 'https://www.mobileread.com/forums/showthread.php?t=372349'),
    ('Template Catalog', _('Manage and organise templates'), 'https://www.mobileread.com/forums/showthread.php?t=366843'),
    ('Toggle Light & Dark', _('Toggle light/dark theme'), 'https://www.mobileread.com/forums/showthread.php?t=371676'),
    ('Toolbars Button', _('Quick access to Toolbars and Menus'), 'https://www.mobileread.com/forums/showthread.php?t=372229'),
    ('VL from selection', _('Create VLs from selection'), 'https://www.mobileread.com/forums/showthread.php?t=371238'),
)


def open_helper_showroom_dialog(parent, group_definitions, get_presets, create_one, create_many):
    global _HELPER_SHOWROOM_DIALOG
    try:
        if _HELPER_SHOWROOM_DIALOG is not None and _HELPER_SHOWROOM_DIALOG.isVisible():
            _HELPER_SHOWROOM_DIALOG.rebind_context(parent, group_definitions, get_presets, create_one, create_many)
            _HELPER_SHOWROOM_DIALOG.showNormal()
            _HELPER_SHOWROOM_DIALOG.raise_()
            _HELPER_SHOWROOM_DIALOG.activateWindow()
            return _HELPER_SHOWROOM_DIALOG
    except Exception:
        _HELPER_SHOWROOM_DIALOG = None

    dialog = HelperShowroomDialog(parent, group_definitions, get_presets, create_one, create_many)
    dialog.destroyed.connect(_clear_helper_showroom_dialog)
    _HELPER_SHOWROOM_DIALOG = dialog
    dialog.show()
    try:
        dialog.raise_()
        dialog.activateWindow()
    except Exception:
        pass
    return dialog


class HelperShowroomDialog(QDialog):

    def __init__(self, parent, group_definitions, get_presets, create_one, create_many):
        try:
            QDialog.__init__(self, None, flags=Qt.WindowType.Window)
        except Exception:
            try:
                QDialog.__init__(self, None, flags=Qt.Window)
            except Exception:
                QDialog.__init__(self, parent)
        self.setWindowTitle(_('Column Pack Browser'))
        themed_icon = _get_plugin_icon('images/pack_light.png', plugin_name=PLUGIN_NAME)
        if themed_icon is None or themed_icon.isNull():
            themed_icon = _get_themed_plugin_icon('iconplugin_light.png')
        if themed_icon is None or themed_icon.isNull():
            themed_icon = _get_themed_plugin_icon('iconplugin_dark.png')
        if themed_icon is None or themed_icon.isNull():
            themed_icon = _get_plugin_icon('images/iconplugin_light.png', plugin_name=PLUGIN_NAME)
        if themed_icon is None or themed_icon.isNull():
            themed_icon = _get_plugin_icon('images/iconplugin_dark.png', plugin_name=PLUGIN_NAME)
        if themed_icon is not None and not themed_icon.isNull():
            try:
                self.setWindowIcon(themed_icon)
            except Exception:
                pass
        try:
            self.setModal(False)
        except Exception:
            pass
        try:
            self.setWindowModality(Qt.WindowModality.NonModal)
        except Exception:
            pass
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        except Exception:
            pass
        try:
            self.setStyleSheet(_ccr_scrollbar_stylesheet())
        except Exception:
            pass
        self.resize(980, 640)
        self.parent_dialog = None
        self.gui = None
        self.group_definitions = []
        self.get_presets = lambda _group: {}
        self.create_one = None
        self.create_many = None
        self._host_destroyed = False
        self._general_help_links = list(build_general_help_links(_))
        self._splitter_sizes_key = SHOWROOM_DETAIL_SPLITTER_KEY
        self._body_splitter_sizes_key = SHOWROOM_BODY_SPLITTER_KEY
        self._geometry_key = SHOWROOM_GEOMETRY_KEY
        self._zoom_steps = showroom_zoom_steps_value()
        self._zoom_base_points = {}
        self._tooltip_panel_source = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(6)

        zoom_bar = QWidget(self)
        zoom_layout = QHBoxLayout(zoom_bar)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(4)

        self.intro_label = QLabel(
            _('Preview column packs and inspect lookup names, types, descriptions, templates, and display settings before creating anything.'),
            zoom_bar,
        )
        self.intro_label.setWordWrap(True)
        zoom_layout.addWidget(self.intro_label, 1)

        self.zoom_out_button = QToolButton(zoom_bar)
        self.zoom_out_button.setToolTip(_('Zoom out (Ctrl+-)'))
        self.zoom_out_button.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(self.zoom_out_button)

        self.zoom_label = QLabel('', zoom_bar)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setFixedWidth(42)
        self.zoom_label.setToolTip(_('Current zoom percent'))
        zoom_layout.addWidget(self.zoom_label)

        self.zoom_in_button = QToolButton(zoom_bar)
        self.zoom_in_button.setToolTip(_('Zoom in (Ctrl++)'))
        self.zoom_in_button.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(self.zoom_in_button)

        self.zoom_reset_button = QToolButton(zoom_bar)
        self.zoom_reset_button.setToolTip(_('Reset zoom (Ctrl+0)'))
        self.zoom_reset_button.clicked.connect(self.zoom_reset)
        zoom_layout.addWidget(self.zoom_reset_button)

        layout.addWidget(zoom_bar)

        self.legend_label = QLabel(self._build_tree_legend_html(), self)
        self.legend_label.setWordWrap(True)
        try:
            self.legend_label.setTextFormat(Qt.TextFormat.RichText)
        except Exception:
            pass
        layout.addWidget(self.legend_label)

        self.guidance_label = QLabel(
            _('\nPacks provide suggestions and known defaults. Choose the final lookup names and column headings that best fit your library and interface language.'),
            self,
        )
        self.guidance_label.setWordWrap(True)
        layout.addWidget(self.guidance_label)

        self.body_splitter = QSplitter(self)
        try:
            self.body_splitter.setOrientation(Qt.Orientation.Horizontal)
        except Exception:
            self.body_splitter.setOrientation(Qt.Horizontal)
        try:
            self.body_splitter.setChildrenCollapsible(False)
        except Exception:
            pass
        layout.addWidget(self.body_splitter, 1)

        left_container = QWidget(self)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        self.tree_actions = QWidget(left_container)
        tree_actions_layout = QHBoxLayout(self.tree_actions)
        tree_actions_layout.setContentsMargins(0, 0, 0, 0)
        tree_actions_layout.setSpacing(4)

        self.expand_all_button = QToolButton(self.tree_actions)
        try:
            self.expand_all_button.setText('▾')
        except Exception:
            self.expand_all_button.setText(_('Expand'))
        self.expand_all_button.setToolTip(_('Expand all packs'))
        self.expand_all_button.clicked.connect(self._expand_all_tree)
        self.expand_all_button.setAutoRaise(True)
        tree_actions_layout.addWidget(self.expand_all_button)

        self.collapse_all_button = QToolButton(self.tree_actions)
        try:
            self.collapse_all_button.setText('▸')
        except Exception:
            self.collapse_all_button.setText(_('Collapse'))
        self.collapse_all_button.setToolTip(_('Collapse all packs'))
        self.collapse_all_button.clicked.connect(self._collapse_all_tree)
        self.collapse_all_button.setAutoRaise(True)
        tree_actions_layout.addWidget(self.collapse_all_button)

        self.tree_filter_edit = QLineEdit(self.tree_actions)
        self.tree_filter_edit.setPlaceholderText(_('Filter packs and presets'))
        self.tree_filter_edit.setStyleSheet(_ccr_lineedit_stylesheet())
        try:
            self.tree_filter_edit.setClearButtonEnabled(True)
        except Exception:
            pass
        self.tree_filter_edit.textChanged.connect(self._apply_tree_filter)
        tree_actions_layout.addWidget(self.tree_filter_edit, 1)
        tree_actions_layout.addStretch(1)
        left_layout.addWidget(self.tree_actions)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabels([_('Section / pack / column')])
        self.tree.setSortingEnabled(True)
        try:
            self.tree.header().sortIndicatorChanged.connect(lambda *_args: self._save_tree_sort())
        except Exception:
            pass
        self.tree.setMinimumWidth(320)
        try:
            self.tree.setUniformRowHeights(True)
        except Exception:
            pass
        left_layout.addWidget(self.tree, 1)
        self.version_info_widget = self._create_version_info_widget(left_container)
        left_layout.addWidget(self.version_info_widget)
        self.body_splitter.addWidget(left_container)

        right_container = QWidget(self)
        right = QVBoxLayout(right_container)
        right.setContentsMargins(0, 0, 0, 0)
        self.body_splitter.addWidget(right_container)
        try:
            self.body_splitter.splitterMoved.connect(lambda *_args: self._save_body_sizes())
        except Exception:
            pass

        self.summary_label = QLabel('')
        self.summary_label.setWordWrap(True)
        right.addWidget(self.summary_label)

        self.meta_edit = QPlainTextEdit(self)
        self.meta_edit.setReadOnly(True)
        self.column_data_label = QLabel(_('Column data'))

        self.composite_edit = QPlainTextEdit(self)
        self.composite_edit.setReadOnly(True)
        self.composite_edit.setPlaceholderText(_('No composite template for this preset.'))
        self.composite_highlighter = TemplateHighlighter(self.composite_edit.document())
        self.composite_label = QLabel(_('Template'))

        self.web_search_edit = QPlainTextEdit(self)
        self.web_search_edit.setReadOnly(True)
        self.web_search_edit.setPlaceholderText(_('No web search template for this preset.'))
        self.web_search_highlighter = TemplateHighlighter(self.web_search_edit.document())
        self.web_search_label = QLabel(_('Search template'))

        self.tooltip_edit = QPlainTextEdit(self)
        self.tooltip_edit.setReadOnly(True)
        self.tooltip_edit.setPlaceholderText(_column_tooltip_placeholder_text())
        self.tooltip_highlighter = TemplateHighlighter(self.tooltip_edit.document())
        self.tooltip_label = QLabel(_('Tooltip template'))

        self.details_splitter = QSplitter(self)
        try:
            self.details_splitter.setOrientation(Qt.Orientation.Vertical)
        except Exception:
            self.details_splitter.setOrientation(Qt.Vertical)
        try:
            self.details_splitter.setChildrenCollapsible(False)
        except Exception:
            pass
        self.details_splitter.addWidget(self._build_detail_section(self.column_data_label, self.meta_edit))
        self.details_splitter.addWidget(self._build_detail_section(self.composite_label, self.composite_edit))
        self.details_splitter.addWidget(self._build_detail_section(self.web_search_label, self.web_search_edit))
        self.details_splitter.addWidget(self._build_detail_section(self.tooltip_label, self.tooltip_edit))
        try:
            self.details_splitter.splitterMoved.connect(lambda *_args: self._save_section_sizes())
        except Exception:
            pass
        right.addWidget(self.details_splitter, 1)

        self.feedback_label = QLabel('')
        self.feedback_label.setWordWrap(True)
        right.addWidget(self.feedback_label)

        self.help_section = QWidget(self)
        help_layout = QVBoxLayout(self.help_section)
        help_layout.setContentsMargins(0, 10, 0, 8)
        help_layout.setSpacing(0)
        self.help_label = QLabel('')
        self.help_label.setWordWrap(True)
        try:
            self.help_label.setTextFormat(Qt.TextFormat.RichText)
            self.help_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        except Exception:
            pass
        self.help_label.linkActivated.connect(self._open_help_link)
        help_layout.addWidget(self.help_label)
        right.addWidget(self.help_section)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(8)
        footer.addStretch(1)

        self.test_button = QPushButton(_('Test'))
        self.test_web_button = QPushButton(_('Test web'))
        self.copy_data_button = QPushButton(_('Copy column data'))
        self.create_selected_button = QPushButton(_('Create selected'))
        self.create_group_button = QPushButton(_('Apply pack'))
        self.close_button = QPushButton(_('Close'))
        footer.addWidget(self.test_button)
        footer.addWidget(self.test_web_button)
        footer.addWidget(self.copy_data_button)
        footer.addWidget(self.create_selected_button)
        footer.addWidget(self.create_group_button)
        footer.addWidget(self.close_button)
        right.addLayout(footer)

        self.close_button.clicked.connect(self.accept)
        self.test_button.clicked.connect(self._test_current_template)
        self.test_web_button.clicked.connect(self._test_web_search_template)
        self.copy_data_button.clicked.connect(self._copy_current_column_data)
        self.create_selected_button.clicked.connect(self._create_selected)
        self.create_group_button.clicked.connect(self._create_group)
        self.tree.currentItemChanged.connect(self._refresh_details)
        self.tree.itemDoubleClicked.connect(lambda item, _col: self._create_selected())

        test_icon = _get_themed_plugin_icon('test.png')
        if test_icon is not None:
            self.test_button.setIcon(test_icon)
            self.test_web_button.setIcon(test_icon)
        copy_icon = _get_themed_plugin_icon('edit-copy.png')
        if copy_icon is not None:
            self.copy_data_button.setIcon(copy_icon)
        try:
            column_icon = QIcon.ic('column.png')
        except Exception:
            column_icon = None
        if column_icon is not None and not column_icon.isNull():
            self.create_selected_button.setIcon(column_icon)
        try:
            pack_icon = QIcon.ic('unpack-book.png')
        except Exception:
            pack_icon = None
        themed_pack_icon = _get_plugin_icon('images/pack_light.png', plugin_name=PLUGIN_NAME)
        if themed_pack_icon is not None and not themed_pack_icon.isNull():
            pack_icon = themed_pack_icon
        if pack_icon is not None and not pack_icon.isNull():
            self.create_group_button.setIcon(pack_icon)
        close_icon = _get_close_action_icon()
        if close_icon is not None:
            self.close_button.setIcon(close_icon)

        self._init_zoom_controls()
        self._install_zoom_support()
        self.rebind_context(parent, group_definitions, get_presets, create_one, create_many)

        self._restore_geometry()
        self._restore_body_sizes()
        self._restore_section_sizes()
        self._restore_tree_sort()
        self._refresh_details()
        self._apply_zoom()

    def _create_version_info_widget(self, parent):
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(0)
        self.calibre_version_label = QLabel('calibre {}'.format(_calibre_version_text()), widget)
        self.plugin_version_label = QLabel(_('Columns Helper v.{}').format(_plugin_version_text()), widget)
        layout.addWidget(self.calibre_version_label)
        layout.addWidget(self.plugin_version_label)
        self._refresh_version_info_styles()
        return widget

    def _refresh_version_info_styles(self):
        try:
            palette = self.palette()
            title_color = palette.color(QPalette.ColorRole.WindowText).name()
            meta_color = palette.color(QPalette.ColorRole.Mid).name()
        except Exception:
            title_color = '#444444'
            meta_color = '#777777'
        if hasattr(self, 'calibre_version_label'):
            self.calibre_version_label.setStyleSheet(
                'QLabel { color: %s; font-size: 8pt; font-weight: 600; padding: 0px; }' % title_color
            )
        if hasattr(self, 'plugin_version_label'):
            self.plugin_version_label.setStyleSheet(
                'QLabel { color: %s; font-size: 8pt; padding: 0px; }' % meta_color
            )

    def _expand_all_tree(self):
        try:
            self.tree.expandAll()
        except Exception:
            pass

    def _collapse_all_tree(self):
        try:
            self.tree.collapseAll()
        except Exception:
            pass
        try:
            if self.tree.topLevelItemCount() > 0:
                self.tree.topLevelItem(0).setExpanded(True)
        except Exception:
            pass

    def _save_tree_sort(self):
        try:
            header = self.tree.header()
        except Exception:
            return
        try:
            section = int(header.sortIndicatorSection())
        except Exception:
            section = 0
        try:
            order = int(header.sortIndicatorOrder())
        except Exception:
            try:
                order = int(Qt.SortOrder.AscendingOrder)
            except Exception:
                order = 0
        try:
            gprefs.set(SHOWROOM_TREE_SORT_KEY, (section, order))
        except Exception:
            pass

    def _restore_tree_sort(self):
        try:
            header = self.tree.header()
        except Exception:
            return
        try:
            stored = gprefs.get(SHOWROOM_TREE_SORT_KEY, None)
        except Exception:
            stored = None
        section = 0
        order = None
        if isinstance(stored, (list, tuple)) and len(stored) >= 2:
            try:
                section = int(stored[0])
            except Exception:
                section = 0
            try:
                order = int(stored[1])
            except Exception:
                order = None
        if order is None:
            try:
                order = int(Qt.SortOrder.AscendingOrder)
            except Exception:
                order = 0
        try:
            self.tree.sortItems(section, Qt.SortOrder(order))
        except Exception:
            try:
                self.tree.sortItems(section, order)
            except Exception:
                pass
        try:
            header.setSortIndicator(section, Qt.SortOrder(order))
        except Exception:
            try:
                header.setSortIndicator(section, order)
            except Exception:
                pass

    def rebind_context(self, parent, group_definitions, get_presets, create_one, create_many):
        self.parent_dialog = parent if _qt_object_is_alive(parent) else None
        self.gui = self._resolve_gui(parent)
        self.group_definitions = list(group_definitions or [])
        self.get_presets = get_presets
        self.create_one = create_one
        self.create_many = create_many
        self._host_destroyed = False
        if self.parent_dialog is not None:
            try:
                self.parent_dialog.destroyed.connect(self._on_host_destroyed)
            except Exception:
                pass
        self._reload_tree()

    def _reload_tree(self):
        current_payload = self._current_payload() or {}
        wanted_group = current_payload.get('group')
        wanted_key = current_payload.get('key')
        try:
            self.tree.clear()
        except Exception:
            pass
        self._populate_tree()
        self._restore_tree_sort()
        if wanted_group:
            self._select_payload(wanted_group, wanted_key)
        self._refresh_details()

    def _select_payload(self, group, key=None):
        def visit(item):
            payload = item.data(0, Qt.ItemDataRole.UserRole) or {}
            if payload.get('group') == group and (key is None or payload.get('key') == key):
                self.tree.setCurrentItem(item)
                return True
            for idx in range(item.childCount()):
                if visit(item.child(idx)):
                    return True
            return False

        for top_index in range(self.tree.topLevelItemCount()):
            if visit(self.tree.topLevelItem(top_index)):
                return True
        return False

    def _on_host_destroyed(self, *args):
        self.parent_dialog = None
        self._host_destroyed = True
        self._set_feedback(_('The columns window was closed. Reopen Columns Helper to create presets again.'))
        self._refresh_details()

    def _resolve_gui(self, parent):
        if parent is not None and hasattr(parent, 'library_view') and hasattr(parent, 'current_db'):
            return parent
        gui = getattr(parent, 'gui', None)
        probe = parent
        while gui is None and probe is not None:
            try:
                probe = probe.parent()
            except Exception:
                probe = None
            gui = getattr(probe, 'gui', None) if probe is not None else None
        return gui

    def _init_zoom_controls(self):
        zoom_out_icon = _get_plugin_icon('images/zoom_out.png', plugin_name=PLUGIN_NAME)
        if zoom_out_icon is None or zoom_out_icon.isNull():
            try:
                zoom_out_icon = QIcon.ic('zoom-out.png')
            except Exception:
                zoom_out_icon = None
        if zoom_out_icon is not None and not zoom_out_icon.isNull():
            self.zoom_out_button.setIcon(zoom_out_icon)
        self.zoom_out_button.setAutoRaise(True)

        zoom_in_icon = _get_plugin_icon('images/zoom_in.png', plugin_name=PLUGIN_NAME)
        if zoom_in_icon is None or zoom_in_icon.isNull():
            try:
                zoom_in_icon = QIcon.ic('zoom-in.png')
            except Exception:
                zoom_in_icon = None
        if zoom_in_icon is not None and not zoom_in_icon.isNull():
            self.zoom_in_button.setIcon(zoom_in_icon)
        self.zoom_in_button.setAutoRaise(True)

        zoom_reset_icon = _get_plugin_icon('images/zoom-reset.png', plugin_name=PLUGIN_NAME)
        if zoom_reset_icon is None or zoom_reset_icon.isNull():
            try:
                zoom_reset_icon = QIcon.ic('restart.png')
            except Exception:
                zoom_reset_icon = None
        if zoom_reset_icon is not None and not zoom_reset_icon.isNull():
            self.zoom_reset_button.setIcon(zoom_reset_icon)
        self.zoom_reset_button.setAutoRaise(True)

    def _install_zoom_support(self):
        self._zoom_in_shortcut_1 = QShortcut(QKeySequence('Ctrl++'), self)
        self._zoom_in_shortcut_1.activated.connect(self.zoom_in)
        self._zoom_in_shortcut_2 = QShortcut(QKeySequence('Ctrl+='), self)
        self._zoom_in_shortcut_2.activated.connect(self.zoom_in)
        self._zoom_out_shortcut = QShortcut(QKeySequence('Ctrl+-'), self)
        self._zoom_out_shortcut.activated.connect(self.zoom_out)
        self._zoom_reset_shortcut = QShortcut(QKeySequence('Ctrl+0'), self)
        self._zoom_reset_shortcut.activated.connect(self.zoom_reset)
        watched = [self, self.tree, self.tree.viewport(), self.meta_edit, self.composite_edit, self.web_search_edit]
        watched.append(self.tooltip_edit)
        for obj in watched:
            try:
                obj.installEventFilter(self)
            except Exception:
                pass

    def _save_geometry(self):
        try:
            gprefs[self._geometry_key] = bytearray(self.saveGeometry())
        except Exception:
            pass

    def _restore_geometry(self):
        geom = gprefs.get(self._geometry_key, None)
        if geom:
            try:
                self.restoreGeometry(geom)
                return
            except Exception:
                pass
        self.resize(980, 640)

    def _save_body_sizes(self):
        try:
            gprefs[self._body_splitter_sizes_key] = [int(v) for v in self.body_splitter.sizes()]
        except Exception:
            pass

    def _restore_body_sizes(self):
        sizes = gprefs.get(self._body_splitter_sizes_key, None)
        if not isinstance(sizes, (list, tuple)) or len(sizes) != 2:
            sizes = [340, 640]
        try:
            self.body_splitter.setSizes([max(140, int(v)) for v in sizes])
        except Exception:
            pass

    # The following methods previously handled persistence of the tree sort order.
    # They have been removed to avoid interfering with column ordering.

    def _remember_font(self, key, widget):
        if widget is None or key in self._zoom_base_points:
            return
        try:
            point_size = float(widget.font().pointSizeF())
            if point_size <= 0:
                point_size = float(widget.font().pointSize())
        except Exception:
            point_size = 0.0
        if point_size <= 0:
            point_size = 10.0
        self._zoom_base_points[key] = point_size

    def _set_widget_font_scale(self, widget, key, factor):
        if widget is None:
            return
        self._remember_font(key, widget)
        base = self._zoom_base_points.get(key, 10.0)
        try:
            font = widget.font()
            font.setPointSizeF(max(6.0, round(base * factor, 1)))
            widget.setFont(font)
        except Exception:
            pass

    def _apply_zoom(self):
        factor = showroom_zoom_scale_factor(self._zoom_steps)
        widget_map = {
            'intro': getattr(self, 'intro_label', None),
            'legend': getattr(self, 'legend_label', None),
            'guidance': getattr(self, 'guidance_label', None),
            'summary': self.summary_label,
            'feedback': self.feedback_label,
            'help': self.help_label,
            'tree': self.tree,
            'meta': self.meta_edit,
            'composite': self.composite_edit,
            'search': self.web_search_edit,
            'tooltip': self.tooltip_edit,
            'col_label': self.column_data_label,
            'tpl_label': self.composite_label,
            'web_label': self.web_search_label,
            'tooltip_label': self.tooltip_label,
            'filter': getattr(self, 'tree_filter_edit', None),
            'zoom_label': self.zoom_label,
            'calibre_version': getattr(self, 'calibre_version_label', None),
            'plugin_version': getattr(self, 'plugin_version_label', None),
            'test_button': self.test_button,
            'test_web_button': self.test_web_button,
            'copy_button': self.copy_data_button,
            'create_button': self.create_selected_button,
            'pack_button': self.create_group_button,
            'close_button': self.close_button,
        }
        for key, widget in widget_map.items():
            self._set_widget_font_scale(widget, key, factor)
        try:
            header = self.tree.header()
            if header is not None:
                self._set_widget_font_scale(header, 'tree_header', factor)
        except Exception:
            pass
        icon_px = max(14, min(28, int(round(16 * factor))))
        for button in (self.zoom_out_button, self.zoom_in_button, self.zoom_reset_button,
                       self.expand_all_button, self.collapse_all_button,
                       self.test_button, self.test_web_button, self.copy_data_button,
                       self.create_selected_button, self.create_group_button, self.close_button):
            try:
                button.setIconSize(QSize(icon_px, icon_px))
            except Exception:
                pass
        self._update_zoom_label()
        self._refresh_version_info_styles()

    def _change_zoom(self, delta_steps):
        new_val = max(SHOWROOM_ZOOM_STEPS_MIN, min(SHOWROOM_ZOOM_STEPS_MAX, int(self._zoom_steps) + int(delta_steps)))
        if new_val == self._zoom_steps:
            self._update_zoom_label()
            return
        self._zoom_steps = new_val
        gprefs[SHOWROOM_ZOOM_STEPS_KEY] = int(new_val)
        self._apply_zoom()

    def _update_zoom_label(self):
        try:
            self.zoom_label.setText('{0}%'.format(int(round(showroom_zoom_scale_factor(self._zoom_steps) * 100.0))))
        except Exception:
            self.zoom_label.setText('{0}%'.format(showroom_zoom_percent_value()))

    def zoom_in(self):
        self._change_zoom(1)

    def zoom_out(self):
        self._change_zoom(-1)

    def zoom_reset(self):
        if self._zoom_steps == 0:
            self._update_zoom_label()
            return
        self._zoom_steps = 0
        gprefs[SHOWROOM_ZOOM_STEPS_KEY] = 0
        self._apply_zoom()

    def _build_detail_section(self, label, editor):
        container = QWidget(self)
        section_layout = QVBoxLayout(container)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(4)
        try:
            font = label.font()
            font.setBold(True)
            label.setFont(font)
        except Exception:
            pass
        section_layout.addWidget(label)
        section_layout.addWidget(editor, 1)
        return container

    def _tree_colors(self):
        if _is_dark_theme():
            return {
                'section_fg': '#93c5fd',
                'section_bg': '#1f2937',
                'group_fg': '#86efac',
                'preset_fg': '#d1d5db',
            }
        return {
            'section_fg': '#1d4ed8',
            'section_bg': '#e8f0fe',
            'group_fg': '#166534',
            'preset_fg': '#1f2937',
        }

    def _build_tree_legend_html(self):
        colors = self._tree_colors()
        return (
            '{legend} '
            '<span style="color:{section_fg};"><b>{section}</b></span> · '
            '<span style="color:{group_fg};"><b>{pack}</b></span> = {pack_desc} · '
            '<span style="color:{preset_fg};"><b>{column}</b></span> = {column_desc}'
        ).format(
            legend=_html_escape(_('Legend:')),
            section_fg=colors['section_fg'],
            group_fg=colors['group_fg'],
            preset_fg=colors['preset_fg'],
            section=_html_escape(_('Section')),
            pack=_html_escape(_('Pack')),
            pack_desc=_html_escape(_('reusable set of related column presets')),
            column=_html_escape(_('Column')),
            column_desc=_html_escape(_('single preset you can create individually')),
        )

    def _style_tree_item(self, item, kind):
        colors = self._tree_colors()
        try:
            font = item.font(0)
            font.setBold(kind in ('section', 'group'))
            item.setFont(0, font)
        except Exception:
            pass
        try:
            if kind == 'section':
                item.setForeground(0, QBrush(QColor(colors['section_fg'])))
                item.setBackground(0, QBrush(QColor(colors['section_bg'])))
                item.setToolTip(0, _('Section'))
            elif kind == 'group':
                item.setForeground(0, QBrush(QColor(colors['group_fg'])))
                item.setToolTip(0, _('Pack: reusable set of related column presets'))
            else:
                item.setForeground(0, QBrush(QColor(colors['preset_fg'])))
                item.setToolTip(0, _('Column preset: create this column only'))
        except Exception:
            pass

    def _save_section_sizes(self):
        try:
            sizes = [int(v) for v in self.details_splitter.sizes()]
        except Exception:
            sizes = []
        if len(sizes) == 4:
            gprefs[self._splitter_sizes_key] = sizes

    def _restore_section_sizes(self):
        sizes = gprefs.get(self._splitter_sizes_key, None)
        if not isinstance(sizes, (list, tuple)) or len(sizes) != 4:
            sizes = [200, 180, 140, 180]
        try:
            self.details_splitter.setSizes([max(80, int(v)) for v in sizes])
        except Exception:
            pass

    def accept(self):
        self._save_section_sizes()
        QDialog.accept(self)

    def reject(self):
        self._save_section_sizes()
        QDialog.reject(self)

    def _populate_tree(self):
        sections = []
        section_map = {}
        for group_def in self.group_definitions:
            section_key = group_def.get('section') or 'other'
            section_title = group_def.get('section_title') or section_key
            bucket = section_map.get(section_key)
            if bucket is None:
                bucket = {'title': section_title, 'groups': []}
                section_map[section_key] = bucket
                sections.append(bucket)
            bucket['groups'].append(group_def)

        first = None
        try:
            self.tree.setUpdatesEnabled(False)
        except Exception:
            pass
        try:
            self.tree.blockSignals(True)
        except Exception:
            pass
        try:
            for section in sections:
                section_item = QTreeWidgetItem([section['title']])
                section_item.setData(0, Qt.ItemDataRole.UserRole, {'kind': 'section'})
                self._style_tree_item(section_item, 'section')
                self.tree.addTopLevelItem(section_item)
                for group_def in section['groups']:
                    group_key = group_def.get('key')
                    presets = self.get_presets(group_key) if group_key else {}
                    group_item = QTreeWidgetItem([group_def.get('title') or group_key or ''])
                    group_item.setData(0, Qt.ItemDataRole.UserRole, {
                        'kind': 'group',
                        'group': group_key,
                        'group_title': group_def.get('title') or group_key or '',
                        'summary': group_def.get('summary') or '',
                        'group_definition': dict(group_def),
                    })
                    self._style_tree_item(group_item, 'group')
                    section_item.addChild(group_item)
                    for preset_key, preset in presets.items():
                        if preset_key == '__all__':
                            continue
                        label = preset.get('menu_text') or preset.get('heading') or preset_key
                        child = QTreeWidgetItem([label])
                        child.setData(0, Qt.ItemDataRole.UserRole, {
                            'kind': 'preset',
                            'group': group_key,
                            'key': preset_key,
                            'preset': dict(preset),
                            'group_definition': dict(group_def),
                        })
                        self._style_tree_item(child, 'preset')
                        group_item.addChild(child)
                        if first is None:
                            first = child
                section_item.setExpanded(True)
            if first is not None:
                self.tree.setCurrentItem(first)
        finally:
            try:
                self.tree.blockSignals(False)
            except Exception:
                pass
            try:
                self.tree.setUpdatesEnabled(True)
            except Exception:
                pass
        self._apply_tree_filter(self.tree_filter_edit.text() if hasattr(self, 'tree_filter_edit') else '')

    def _item_matches_filter(self, item, needle):
        if not needle:
            return True
        payload = item.data(0, Qt.ItemDataRole.UserRole) or {}
        haystacks = [item.text(0) or '']
        for key in ('group', 'key', 'group_title', 'summary'):
            value = payload.get(key)
            if value:
                haystacks.append(str(value))
        preset = payload.get('preset') or {}
        display = preset.get('display') or {}
        for key in ('lookup_name', 'heading', 'datatype', 'description', 'menu_text', 'tooltip_template'):
            value = preset.get(key)
            if value:
                haystacks.append(str(value))
        for key in ('description', 'composite_template', 'web_search_template', 'tooltip_template'):
            value = display.get(key)
            if value:
                haystacks.append(str(value))
        combined = '\n'.join(haystacks).lower()
        return needle in combined

    def _apply_tree_filter(self, text=''):
        needle = (text or '').strip().lower()

        def visit(item):
            child_visible = False
            for idx in range(item.childCount()):
                child_visible = visit(item.child(idx)) or child_visible
            visible = self._item_matches_filter(item, needle) or child_visible or not needle
            try:
                item.setHidden(not visible)
            except Exception:
                pass
            if needle and visible and child_visible:
                try:
                    item.setExpanded(True)
                except Exception:
                    pass
            return visible

        first_visible = None
        current = self.tree.currentItem()
        for top_index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(top_index)
            if visit(item) and first_visible is None:
                first_visible = item
        if current is not None:
            try:
                if current.isHidden():
                    current = None
            except Exception:
                current = None
        if current is None and first_visible is not None:
            target = self._first_visible_descendant(first_visible)
            if target is not None:
                self.tree.setCurrentItem(target)

    def _first_visible_descendant(self, item):
        try:
            if not item.isHidden() and (item.childCount() == 0 or (item.data(0, Qt.ItemDataRole.UserRole) or {}).get('kind') != 'section'):
                return item
        except Exception:
            pass
        for idx in range(item.childCount()):
            target = self._first_visible_descendant(item.child(idx))
            if target is not None:
                return target
        return item if not item.isHidden() else None

    def _open_help_link(self, url):
        if not url:
            return
        try:
            open_url(QUrl(url))
        except Exception:
            pass

    def _set_feedback(self, text):
        self.feedback_label.setText(text or '')

    def _host_can_accept_actions(self):
        if not _qt_object_is_alive(self.parent_dialog):
            return False
        for callback in (self.create_one, self.create_many):
            owner = getattr(callback, '__self__', None)
            if owner is not None and not _qt_object_is_alive(owner):
                return False
            widget = getattr(owner, 'widget', None) if owner is not None else None
            if widget is not None and not _qt_object_is_alive(widget):
                return False
            table = getattr(widget, 'opt_columns', None) if widget is not None else None
            if table is not None and not _qt_object_is_alive(table):
                return False
        return True

    def _current_preset(self):
        payload = self._current_payload() or {}
        if payload.get('kind') != 'preset':
            return None
        return payload.get('preset') or {}

    def _render_help_links(self, payload, preset=None):
        entries = []
        seen = set()
        info_entries = []

        def add_links(candidates):
            for candidate in candidates or ():
                try:
                    label, url = candidate
                except Exception:
                    continue
                if not label or not url or url in seen:
                    continue
                seen.add(url)
                entries.append((label, url))

        def add_info(candidate):
            if not candidate:
                return
            text = str(candidate).strip()
            if not text:
                return
            if text not in info_entries:
                info_entries.append(text)

        add_links(self._general_help_links)
        add_links((payload.get('group_definition') or {}).get('help_links'))
        add_links((preset or {}).get('help_links'))
        add_info((payload.get('group_definition') or {}).get('info_text'))
        add_info((preset or {}).get('info_text'))

        if not entries and not info_entries:
            self.help_label.setText('')
            return

        chunks = []
        if info_entries:
            info_html = '<br/>'.join(_html_escape(text) for text in info_entries)
            chunks.append('<b>{0}</b> {1}'.format(_html_escape(_('Info:')), info_html))
        if entries:
            links_html = ' · '.join(
                '<a href="{0}">{1}</a>'.format(_html_escape(url), _html_escape(label))
                for label, url in entries
            )
            chunks.append(_html_escape(_('Learn: ')) + links_html)
        self.help_label.setText('<br/>'.join(chunks))

    def _current_tooltip_template(self):
        return (self.tooltip_edit.toPlainText() or '').strip()

    def _current_lookup_name(self):
        preset = self._current_preset() or {}
        return str(preset.get('lookup_name') or '').strip()

    def _tooltip_templates_pref(self):
        gui = self._get_calibre_gui()
        db = getattr(gui, 'current_db', None) if gui is not None else None
        api = getattr(db, 'new_api', None) if db is not None else None
        if api is None:
            return ({}, None)
        try:
            data = dict(api.pref('column_tooltip_templates', {}) or {})
        except Exception:
            data = {}
        return (data, api)

    def _tooltip_template_from_sources(self, preset):
        display = dict(preset.get('display') or {})
        preset_template = str(preset.get('tooltip_template') or display.get('tooltip_template') or '').strip()
        if preset_template:
            return (preset_template, 'preset')
        lookup_name = self._current_lookup_name()
        templates, _api = self._tooltip_templates_pref()
        stored = str(templates.get(lookup_name, '') or '').strip() if lookup_name else ''
        if stored:
            return (stored, 'library')
        return ('', None)

    def _tooltip_label_text(self, source):
        base = _('Tooltip template')
        if source == 'preset':
            return _('Tooltip template (pack preset)')
        if source == 'library':
            return _('Tooltip template (current library setting)')
        return base

    def _current_template_for_actions(self):
        composite_template = (self.composite_edit.toPlainText() or '').strip()
        web_search_template = (self.web_search_edit.toPlainText() or '').strip()
        focus = QApplication.focusWidget()
        if focus is self.web_search_edit and web_search_template:
            return ('web_search_template', web_search_template)
        if focus is self.composite_edit and composite_template:
            return ('composite_template', composite_template)
        if composite_template:
            return ('composite_template', composite_template)
        if web_search_template:
            return ('web_search_template', web_search_template)
        return (None, '')

    def _template_for_kind(self, template_kind=None):
        composite_template = (self.composite_edit.toPlainText() or '').strip()
        web_search_template = (self.web_search_edit.toPlainText() or '').strip()
        if template_kind == 'web_search_template':
            return ('web_search_template', web_search_template)
        if template_kind == 'composite_template':
            return ('composite_template', composite_template)
        return self._current_template_for_actions()

    def _get_calibre_gui(self):
        gui = getattr(self, 'gui', None)
        if gui is not None:
            return gui
        gui = getattr(self.parent(), 'gui', None)
        parent = self.parent()
        while gui is None and parent is not None:
            gui = getattr(parent, 'gui', None)
            try:
                parent = parent.parent()
            except Exception:
                parent = None
        return gui

    def _test_current_template(self):
        self._test_template_kind(None)

    def _test_web_search_template(self):
        self._test_template_kind('web_search_template')

    def _test_template_kind(self, template_kind=None):
        payload = self._current_payload() or {}
        preset = self._current_preset()
        if payload.get('kind') != 'preset' or preset is None:
            return

        template_kind, template_content = self._template_for_kind(template_kind)
        if not template_content:
            self._set_feedback(_('No template is available to test for this preset.'))
            return

        gui = self._get_calibre_gui()
        if gui is None or not hasattr(gui, 'library_view'):
            error_dialog(self, _('Error'), _('Cannot access library view. Please ensure calibre is running properly.'), show=True)
            return

        rows = gui.library_view.selectionModel().selectedRows()
        if not rows:
            error_dialog(self, _('No book selected'), _('Please select a book in calibre first to test the template against.'), show=True)
            return

        try:
            from calibre.gui2.dialogs.template_dialog import TemplateDialog
        except Exception:
            error_dialog(self, _('Unavailable'), _('This calibre version does not expose the template tester dialog.'), show=True)
            return

        book_id = gui.library_view.model().id(rows[0])
        db = gui.current_db
        mi = db.new_api.get_metadata(book_id, get_cover=True, cover_as_data=True)
        dialog = TemplateDialog(self, template_content, mi=mi)
        title = preset.get('heading') or payload.get('key') or _('Template')
        kind_label = _('Composite') if template_kind == 'composite_template' else _('Web search')
        dialog.setWindowTitle(_('Test Template: {0} ({1})').format(title, kind_label))
        dialog.exec()

    def _copy_current_column_data(self):
        payload = self._current_payload() or {}
        preset = self._current_preset()
        if payload.get('kind') != 'preset' or preset is None:
            return
        display = dict(preset.get('display') or {})
        composite_template = str(display.get('composite_template') or '').strip()
        web_search_template = str(display.get('web_search_template') or '').strip()
        lines = [
            '{0}: {1}'.format(_('Column header'), preset.get('heading') or ''),
            '{0}: {1}'.format(_('Lookup name'), preset.get('lookup_name') or ''),
            '{0}: {1}'.format(_('Type'), preset.get('datatype') or ''),
            '{0}: {1}'.format(_('Description'), preset.get('description') or display.get('description') or ''),
            '{0}: {1}'.format(_('Is multiple'), _('Yes') if preset.get('is_multiple') else _('No')),
            '{0}: {1}'.format(_('Is Composite'), _('Yes') if preset.get('datatype') == 'composite' else _('No')),
            '',
            _('Template') + ':',
            composite_template,
            '',
            _('Web search template') + ':',
            web_search_template,
            '',
            _('Tooltip template') + ':',
            self._current_tooltip_template(),
            '',
            _('Display settings') + ':',
            json.dumps(display, indent=2, ensure_ascii=False, sort_keys=True),
        ]
        if copy_to_clipboard('\n'.join(lines)):
            self._set_feedback(_('Column data copied to the clipboard.'))

    def _current_payload(self):
        item = self.tree.currentItem()
        if item is None:
            return None
        try:
            return item.data(0, Qt.ItemDataRole.UserRole)
        except Exception:
            return None

    def _refresh_details(self, *args):
        payload = self._current_payload() or {}
        kind = payload.get('kind')
        preset = payload.get('preset') or {}
        display = dict(preset.get('display') or {}) if kind == 'preset' else {}
        composite_template = str(display.get('composite_template') or '').strip()
        web_search_template = str(display.get('web_search_template') or '').strip()
        tooltip_template, tooltip_source = self._tooltip_template_from_sources(preset) if kind == 'preset' else ('', None)
        host_ready = self._host_can_accept_actions()
        self.create_selected_button.setEnabled(kind == 'preset' and host_ready)
        self.create_group_button.setEnabled(kind in ('group', 'preset') and host_ready)
        self.test_button.setEnabled(kind == 'preset' and bool(composite_template or web_search_template))
        self.test_web_button.setEnabled(kind == 'preset' and bool(web_search_template))
        self.copy_data_button.setEnabled(kind == 'preset')
        if not host_ready:
            self._set_feedback(_('The columns window is not available. Reopen Columns Helper to create presets.'))
        else:
            self._set_feedback('')

        if kind == 'preset':
            self.summary_label.setText((preset.get('description') or display.get('description') or '').strip())
            self._render_help_links(payload, preset=preset)
            meta_lines = [
                '{0}: {1}'.format(_('Column heading'), preset.get('heading') or ''),
                '{0}: {1}'.format(_('Lookup name'), preset.get('lookup_name') or ''),
                '{0}: {1}'.format(_('Data type'), preset.get('datatype') or ''),
                '{0}: {1}'.format(_('Is multiple'), _('Yes') if preset.get('is_multiple') else _('No')),
                '{0}: {1}'.format(_('Is Composite'), _('Yes') if preset.get('datatype') == 'composite' else _('No')),
                '',
                _('Display settings') + ':',
                json.dumps(display, indent=2, ensure_ascii=False, sort_keys=True),
            ]
            self.meta_edit.setPlainText('\n'.join(meta_lines))
            self.composite_edit.setPlainText(composite_template)
            self.web_search_edit.setPlainText(web_search_template)
            self.tooltip_label.setText(self._tooltip_label_text(tooltip_source))
            self.tooltip_edit.setPlainText(tooltip_template or '')
            self._tooltip_panel_source = tooltip_source
            self.tooltip_edit.setPlaceholderText(_column_tooltip_placeholder_text())
            return

        if kind == 'group':
            group = payload.get('group')
            presets = self.get_presets(group) if group else {}
            count = len([k for k in presets if k != '__all__'])
            self.summary_label.setText(payload.get('summary') or _('This pack (reusable set) contains {0} helper presets.').format(count))
            self._render_help_links(payload)
            self.meta_edit.setPlainText(json.dumps({
                'group': group,
                'title': payload.get('group_title'),
                'preset_count': count,
            }, indent=2, ensure_ascii=False, sort_keys=True))
            self.composite_edit.setPlainText('')
            self.web_search_edit.setPlainText('')
            self.tooltip_label.setText(self._tooltip_label_text(None))
            self.tooltip_edit.setPlainText('')
            return

        self.summary_label.setText(_('Browse sections, then packs (reusable sets), then preview a preset before creating it.'))
        self._render_help_links(payload)
        self.meta_edit.setPlainText('')
        self.composite_edit.setPlainText('')
        self.web_search_edit.setPlainText('')
        self.tooltip_label.setText(self._tooltip_label_text(None))
        self.tooltip_edit.setPlainText('')

    def _create_selected(self):
        payload = self._current_payload() or {}
        if payload.get('kind') != 'preset':
            return
        if not self._host_can_accept_actions():
            self._set_feedback(_('The columns window is not available. Reopen Columns Helper to create presets.'))
            return
        try:
            host = self.create_one(payload.get('group'), payload.get('key'))
        except RuntimeError:
            self._set_feedback(_('The columns window was closed. Reopen Columns Helper and try again.'))
            self._refresh_details()
            return
        self._focus_host_after_action(host)

    def _create_group(self):
        payload = self._current_payload() or {}
        group = payload.get('group')
        if not group:
            return
        presets = self.get_presets(group)
        keys = [key for key in presets if key != '__all__']
        if keys:
            if not self._host_can_accept_actions():
                self._set_feedback(_('The columns window is not available. Reopen Columns Helper to apply packs.'))
                return
            try:
                host = self.create_many(group, keys)
            except RuntimeError:
                self._set_feedback(_('The columns window was closed. Reopen Columns Helper and try again.'))
                self._refresh_details()
                return
            self._focus_host_after_action(host)

    def _focus_host_after_action(self, preferred_host=None):
        host = preferred_host
        if not _qt_object_is_alive(host):
            host = globals().get('_MODELESS_COLUMNS_DIALOG', None)
        if not _qt_object_is_alive(host):
            host = self.parent_dialog
        if host is None:
            return
        try:
            if host.isMinimized():
                host.showNormal()
        except Exception:
            pass
        try:
            host.raise_()
            host.activateWindow()
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            if event.type() == QEvent.Type.Wheel:
                mods = event.modifiers() if hasattr(event, 'modifiers') else None
                ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier) if mods is not None else False
                if ctrl:
                    dy = 0
                    try:
                        dy = int(event.angleDelta().y())
                    except Exception:
                        try:
                            dy = int(event.delta())
                        except Exception:
                            dy = 0
                    if dy:
                        self._change_zoom(1 if dy > 0 else -1)
                        try:
                            event.accept()
                        except Exception:
                            pass
                        return True
        except Exception:
            pass
        return QDialog.eventFilter(self, obj, event)

    def closeEvent(self, event):
        self._save_geometry()
        self._save_body_sizes()
        self._save_section_sizes()
        try:
            host = getattr(self, 'parent_dialog', None)
            if host is not None and getattr(host, '_cdf_hidden_for_pack_browser', False):
                if not host.isVisible():
                    host.close()
        except Exception:
            pass
        QDialog.closeEvent(self, event)


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
    return None


def _get_themed_plugin_icon(icon_name, plugin_path=None, plugin_name=None):
    if not icon_name:
        return None
    if '/' not in icon_name:
        icon_name = 'images/' + icon_name
    base, ext = os.path.splitext(icon_name)
    theme_suffix = 'dark' if _is_dark_theme() else 'light'
    opposite_suffix = 'light' if theme_suffix == 'dark' else 'dark'
    themed_match = re.search(r'_(light|dark)$', base)
    if themed_match:
        explicit_suffix = themed_match.group(1)
        stem = base[:-len(explicit_suffix)]
        candidates = []
        preferred = stem + theme_suffix + ext
        sibling = stem + opposite_suffix + ext
        if preferred != icon_name:
            candidates.append(preferred)
        candidates.append(icon_name)
        if sibling not in candidates:
            candidates.append(sibling)
    else:
        candidates = [
            '{0}_{1}{2}'.format(base, theme_suffix, ext),
            icon_name,
        ]
    for candidate in candidates:
        icon = _get_plugin_icon(candidate, plugin_path=plugin_path, plugin_name=plugin_name)
        if icon is not None and not icon.isNull():
            return icon
    return None


class TemplateHighlighter(QSyntaxHighlighter):

    KEYWORDS_GPM = ['if', 'then', 'else', 'elif', 'fi', 'for', 'rof',
                    'separator', 'break', 'continue', 'return', 'in', 'inlist',
                    'inlist_field', 'def', 'fed', 'limit', 'with', 'htiw']

    KEYWORDS_PYTHON = ['and', 'as', 'assert', 'break', 'class', 'continue', 'def',
                       'del', 'elif', 'else', 'except', 'exec', 'finally', 'for', 'from',
                       'global', 'if', 'import', 'in', 'is', 'lambda', 'not', 'or',
                       'pass', 'print', 'raise', 'return', 'try', 'while', 'with',
                       'yield']

    BUILTINS_PYTHON = ['abs', 'all', 'any', 'bool', 'callable', 'chr', 'classmethod',
                       'dict', 'dir', 'divmod', 'enumerate', 'eval', 'filter', 'float',
                       'getattr', 'globals', 'hasattr', 'hex', 'id', 'int', 'isinstance',
                       'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max', 'min',
                       'object', 'open', 'ord', 'pow', 'property', 'range', 'repr',
                       'reversed', 'round', 'set', 'setattr', 'slice', 'sorted',
                       'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip']

    CONSTANTS_PYTHON = ['False', 'True', 'None', 'NotImplemented', 'Ellipsis']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initialize_formats()
        self.initialize_rules()

    def initialize_rules(self):
        try:
            from calibre.utils.formatter_functions import formatter_functions
            builtin_functions = sorted(formatter_functions().get_builtins())
        except Exception:
            builtin_functions = []

        self.gpm_rules = []
        self.python_rules = []

        def a(a, b):
            return re.compile(a), b

        gpm_rules = []
        gpm_rules.append(a(r'\b[a-zA-Z]\w*\b(?!\(|\s+\()|\$+#?[a-zA-Z]\w*', 'identifier'))
        gpm_rules.append(a(r'^program:', 'keymode'))
        gpm_rules.append(a('|'.join([rf'\b{keyword}\b' for keyword in self.KEYWORDS_GPM]), 'keyword'))
        builtin_patterns = [rf'\b{re.escape(name)}\b' for name in builtin_functions if name]
        builtin_patterns.append(r'\b[a-zA-Z_]\w*(?=\()')
        gpm_rules.append(a('|'.join(builtin_patterns), 'builtin'))
        gpm_rules.append(a(r'''(?<!:)'[^']*'|"(?:[^"\\]|\\.)*"''', 'string'))

        python_rules = []
        python_rules.append(a(r'^python:', 'keymode'))
        python_rules.append(a('|'.join([rf'\b{keyword}\b' for keyword in self.KEYWORDS_PYTHON]), 'keyword'))
        python_rules.append(a('|'.join([rf'\b{builtin}\b' for builtin in self.BUILTINS_PYTHON]), 'builtin'))
        python_rules.append(a('|'.join([rf'\b{constant}\b' for constant in self.CONSTANTS_PYTHON]), 'constant'))
        python_rules.append(a(r'\bPyQt6\b|\bqt.core\b|\bQt?[A-Z][a-z]\w+\b', 'pyqt'))
        python_rules.append(a(r'@\w+(\.\w+)?\b', 'decorator'))
        string_re = r'''(["'])(?:(?!\1)[^\\]|\\.)*\1'''
        python_rules.append(a(string_re, 'string'))
        self.stringRe = re.compile(string_re)

        number_rule = a(r'\b[+-]?[0-9]+[lL]?\b|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 'number')
        paren_rule = a(r'\(|\)', 'paren')
        gpm_rules.extend([number_rule, paren_rule])
        python_rules.extend([number_rule, paren_rule])

        self.gpm_rules = tuple(gpm_rules)
        self.python_rules = tuple(python_rules)

    def initialize_formats(self):
        font_name = gprefs.get('gpm_template_editor_font', None)
        size = gprefs.get('gpm_template_editor_font_size', 10)
        if font_name is None:
            font = QFont()
            font.setFixedPitch(True)
            font.setPointSize(size)
            font_name = font.family()

        app_palette = QApplication.instance().palette()
        is_dark = _is_dark_theme()

        all_formats = (
            ('normal', None, False, False),
            ('keyword', app_palette.color(QPalette.ColorRole.Link).name(), True, False),
            ('builtin', app_palette.color(QPalette.ColorRole.Link).name(), False, False),
            ('constant', app_palette.color(QPalette.ColorRole.Link).name(), False, False),
            ('identifier', None, False, True),
            ('comment', '#00c700' if is_dark else '#007F00', False, True),
            ('string', '#b6b600' if is_dark else '#808000', False, False),
            ('number', '#d96d00' if is_dark else '#924900', False, False),
            ('decorator', '#FF8000', False, True),
            ('pyqt', None, False, False),
            ('paren', None, True, True),
        )

        base_format = QTextCharFormat()
        base_format.setFontFamilies([font_name, 'Courier New', 'Monospace'])
        base_format.setFontPointSize(size)

        self.Formats = {}
        for name, color, bold, italic in all_formats:
            format_ = QTextCharFormat(base_format)
            if color:
                format_.setForeground(QColor(color))
            if bold:
                format_.setFontWeight(QFont.Weight.Bold)
            format_.setFontItalic(italic)
            self.Formats[name] = format_

    def _current_mode(self):
        try:
            block = self.document().firstBlock()
            first_line = str(block.text() or '').lstrip()
        except Exception:
            first_line = ''
        return 'python' if first_line.startswith('python:') else 'gpm'

    def replace_strings_with_dash(self, mo):
        found = mo.group(0)
        return '-' * len(found)

    def highlightBlock(self, text):
        text = str(text)
        self.setFormat(0, len(text), self.Formats['normal'])
        if not text:
            return
        if re.match(r'[ \t]*#', text):
            self.setFormat(0, len(text), self.Formats['comment'])
            return

        mode = self._current_mode()
        rules = self.python_rules if mode == 'python' else self.gpm_rules
        bn = self.currentBlock().blockNumber()
        for regex, format_ in rules:
            for m in regex.finditer(text):
                if format_ == 'keymode':
                    if bn > 0 and m.start() == 0:
                        continue
                    format_name = 'keyword'
                else:
                    format_name = format_
                self.setFormat(m.start(), m.end() - m.start(), self.Formats[format_name])

        if mode == 'python' and '#' in text:
            t = re.sub(self.stringRe, self.replace_strings_with_dash, text)
            sharp_pos = t.find('#')
            if sharp_pos >= 0:
                self.setFormat(sharp_pos, len(text) - sharp_pos, self.Formats['comment'])


PLUGIN_NAME = 'Columns Helper'
_MODELESS_COLUMNS_DIALOG = None
MODELLESS_COLUMNS_SPLITTER_KEY = 'columns_helper_modeless_splitter_sizes'
MODELLESS_COLUMNS_DETAIL_SPLITTER_KEY = 'columns_helper_modeless_detail_splitter_sizes'


def _clear_modeless_dialog(*args):
    global _MODELESS_COLUMNS_DIALOG
    _MODELESS_COLUMNS_DIALOG = None


class ModelessColumnsDialog(QDialog):

    def __init__(self, gui, parent=None):
        try:
            QDialog.__init__(self, None, flags=Qt.WindowType.Window)
        except Exception:
            try:
                QDialog.__init__(self, None, flags=Qt.Window)
            except Exception:
                QDialog.__init__(self, None)
        self.gui = gui
        self.plugin = get_plugin('Interface', 'Custom Columns')
        self.restart_required = False
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        try:
            self.setModal(False)
        except Exception:
            pass
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowTitle(_(PLUGIN_NAME))
        icon_path = 'images/iconplugin_dark.png' if _is_dark_theme() else 'images/iconplugin_light.png'
        icon = _get_plugin_icon(icon_path)
        if icon is not None:
            self.setWindowIcon(icon)
        else:
            self.setWindowIcon(QIcon.ic('column.png'))
        self.setMinimumSize(QSize(920, 680))
        self.resize(1120, 760)
        try:
            flags = self.windowFlags()
            flags |= Qt.WindowType.Window
            flags |= Qt.WindowType.WindowMinimizeButtonHint
            flags |= Qt.WindowType.WindowMaximizeButtonHint
            flags |= Qt.WindowType.WindowSystemMenuHint
            self.setWindowFlags(flags)
        except Exception:
            try:
                flags = self.windowFlags()
                flags |= Qt.Window
                flags |= Qt.WindowMinimizeButtonHint
                flags |= Qt.WindowMaximizeButtonHint
                flags |= Qt.WindowSystemMenuHint
                self.setWindowFlags(flags)
            except Exception:
                pass

        self.layout = QVBoxLayout(self)
        self._main_splitter_sizes_key = MODELLESS_COLUMNS_SPLITTER_KEY
        self._detail_splitter_sizes_key = MODELLESS_COLUMNS_DETAIL_SPLITTER_KEY
        self._cached_detail_width = 320

        self.main_splitter = QSplitter(self)
        try:
            self.main_splitter.setOrientation(Qt.Orientation.Horizontal)
        except Exception:
            self.main_splitter.setOrientation(Qt.Horizontal)
        try:
            self.main_splitter.setChildrenCollapsible(True)
            # Guard against invalid indices during early construction.
            try:
                count = int(self.main_splitter.count() or 0)
            except Exception:
                count = 0
            if count > 0:
                self.main_splitter.setCollapsible(0, False)
            if count > 1:
                self.main_splitter.setCollapsible(1, True)
        except Exception:
            pass

        try:
            from calibre.gui2.preferences import columns as cols
        except Exception:
            cols = None
        if cols is not None:
            cols.ConfigWidget._creating_from_plugin = True
        try:
            self.widget = self.plugin.create_widget(self.main_splitter)
        finally:
            if cols is not None:
                cols.ConfigWidget._creating_from_plugin = False
        self.widget._from_plugin_action = True
        self.widget._cdf_in_modeless_host = True
        self.widget._cdf_host_dialog = self
        self.widget._cdf_restrict_search_template_to_modeless = True
        self._cdf_hidden_for_pack_browser = False

        # Patch widget's save_geometry and restore_geometry to use separate gprefs keys
        self._original_save_geometry = getattr(self.widget, 'save_geometry', None)
        self._original_restore_geometry = getattr(self.widget, 'restore_geometry', None)
        self.widget.save_geometry = self._patched_save_geometry
        self.widget.restore_geometry = self._patched_restore_geometry

        self.main_splitter.addWidget(self.widget)
        self.selected_column_panel = self._create_selected_column_panel(self.main_splitter)
        self.main_splitter.addWidget(self.selected_column_panel)
        try:
            self.main_splitter.splitterMoved.connect(self._on_main_splitter_moved)
        except Exception:
            pass

        self.layout.addWidget(self.main_splitter, 1)

        # Status label in the middle for feedback messages with background
        self.status_label = QLabel('', self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(52)
        self.status_label.setMargin(10)
        self.layout.addWidget(self.status_label)
        self._set_status_message()

        self.quick_create_bar = QWidget(self)
        self.quick_create_layout = QHBoxLayout(self.quick_create_bar)
        self.quick_create_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_create_layout.setSpacing(8)
        self.quick_create_label = QLabel(self.quick_create_bar)
        self.quick_create_label.setWordWrap(True)
        try:
            self.quick_create_label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        except Exception:
            pass
        self.quick_create_label.linkActivated.connect(self.on_quick_create_link)
        self.quick_create_layout.addWidget(self.quick_create_label, 1)

        self.plugin_helpers_button = QToolButton(self.quick_create_bar)
        self.plugin_helpers_button.setText(_('\u2009Quick Create'))
        self.plugin_helpers_button.setToolTip(_('Quickly create columns from curated packs.'))
        self._configure_helper_button(self.plugin_helpers_button)
        # Removed bogus spacing style; using thin space in label instead
        plus_icon = _get_plugin_icon('images/plus_light.png', plugin_name=PLUGIN_NAME)
        if plus_icon is not None and not plus_icon.isNull():
            self.plugin_helpers_button.setIcon(plus_icon)
        self.quick_create_layout.addWidget(self.plugin_helpers_button)

        self.preview_helpers_button = QToolButton(self.quick_create_bar)
        self.preview_helpers_button.setText(_('\u2009Browse packs…'))
        self.preview_helpers_button.setToolTip(_('Browse column packs, preview templates, and create selected items.'))
        self._configure_helper_button(self.preview_helpers_button)
        # Removed bogus spacing style; using thin space in label instead
        pack_icon = _get_plugin_icon('images/pack_light.png', plugin_name=PLUGIN_NAME)
        if pack_icon is not None and not pack_icon.isNull():
            self.preview_helpers_button.setIcon(pack_icon)
        self.preview_helpers_button.clicked.connect(self.show_helper_showroom)
        self.quick_create_layout.addWidget(self.preview_helpers_button)

        self.quick_create_layout.addSpacing(20)

        self.template_color_checkbox = QCheckBox()
        self.template_color_checkbox.setText(_('Highlight templates'))
        self.template_color_checkbox.setChecked(gprefs.get('columns_helper_template_coloring', False))
        self.template_color_checkbox.setToolTip(_('Enable color coding for columns containing templates (composite or web search templates)'))
        self.template_color_checkbox.stateChanged.connect(self.on_template_color_changed)
        self.quick_create_layout.addWidget(self.template_color_checkbox)

        self.quick_create_layout.addSpacing(8)

        self.details_toggle_button = QToolButton(self.quick_create_bar)
        self.details_toggle_button.setText(_('\u2009Details'))
        self.details_toggle_button.setToolTip(_('Show or hide the column details panel on the right'))
        self.details_toggle_button.setCheckable(True)
        self.details_toggle_button.setChecked(False)
        self._configure_helper_button(self.details_toggle_button)
        details_icon = QIcon.ic('dialog_information.png')
        if details_icon is not None and not details_icon.isNull():
            self.details_toggle_button.setIcon(details_icon)
        self.details_toggle_button.clicked.connect(self._toggle_details_panel)
        self.quick_create_layout.addWidget(self.details_toggle_button)

        self.layout.addWidget(self.quick_create_bar)
        self.layout.addSpacing(15)

        self.footer_widget = QWidget(self)
        self.footer_layout = QHBoxLayout(self.footer_widget)
        self.footer_layout.setContentsMargins(0, 0, 0, 0)
        self.footer_layout.setSpacing(8)
        self.version_info_widget = self._create_version_info_widget(self.footer_widget)
        self.footer_layout.addWidget(self.version_info_widget)
        self.footer_layout.addStretch(1)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Close |
            QDialogButtonBox.StandardButton.RestoreDefaults,
            self,
        )
        self.apply_button = self.button_box.button(QDialogButtonBox.StandardButton.Apply)
        self.close_button = self.button_box.button(QDialogButtonBox.StandardButton.Close)
        self.defaults_button = self.button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults)
        self.apply_button.setEnabled(False)
        self.defaults_button.setEnabled(self.widget.supports_restoring_to_defaults)
        defaults_tooltip = _(
            'Restore calibre\'s default main-library column layout for this screen.\n\n'
            'Specifically, this reloads the default column visibility and the default left-to-right column order used by the library view.\n\n'
            'It does not delete custom columns or reset their definitions, names, types, templates, or descriptions.\n\n'
            'Click Apply to actually save the restored layout.'
        )
        try:
            self.defaults_button.setToolTip(defaults_tooltip)
            self.defaults_button.setStatusTip(defaults_tooltip)
            self.defaults_button.setWhatsThis(defaults_tooltip)
        except Exception:
            pass
        close_icon = _get_close_action_icon()
        if close_icon is not None:
            try:
                self.close_button.setIcon(close_icon)
            except Exception:
                pass

        self.footer_layout.addWidget(self.button_box)
        self.layout.addWidget(self.footer_widget)

        self.button_box.rejected.connect(self.reject)
        self.apply_button.clicked.connect(self.apply_changes)
        self.defaults_button.clicked.connect(self.restore_defaults)
        self.escape_shortcut = QShortcut(QKeySequence('Esc'), self)
        try:
            self.escape_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        except Exception:
            try:
                self.escape_shortcut.setContext(Qt.WidgetShortcut)
            except Exception:
                pass
        self.escape_shortcut.activated.connect(self.reject)

        self.widget.changed_signal.connect(self.on_changed)
        self._do_on_child_tabs('set_changed_signal', self.on_changed)

        self.widget.genesis(self.gui)
        self._do_on_child_tabs('genesis', self.gui)
        self.widget.initialize()
        self._do_on_child_tabs('initialize')
        QTimer.singleShot(0, self._restore_widget_column_layout)
        QTimer.singleShot(75, self._restore_widget_column_layout)
        self._inject_id_column()
        self._attach_selected_column_panel_hooks()
        self._refresh_quick_create_ui()
        self._install_escape_filters()

        # Apply CCR-style scrollbar styling
        try:
            self.setStyleSheet(self._get_scrollbar_stylesheet())
        except Exception:
            pass

        # Connect to palette changes for dynamic color updates
        try:
            app = QApplication.instance()
            if app is not None:
                app.paletteChanged.connect(self._refresh_template_coloring)
                app.paletteChanged.connect(self._refresh_status_label_style)
                app.paletteChanged.connect(self._refresh_version_info_styles)
        except Exception:
            pass

        geom = gprefs.get('columns_dialog_filter_modeless_geometry', None)
        if geom:
            try:
                self.restoreGeometry(geom)
            except Exception:
                pass
        QTimer.singleShot(0, self._restore_main_splitter_sizes)
        QTimer.singleShot(0, self._restore_selected_detail_sizes)
        QTimer.singleShot(0, self._refresh_selected_column_panel)

    def _restore_column_widths(self, table):
        """Restore column widths from gprefs for modeless dialog"""
        try:
            widths = gprefs.get('columns_helper_modeless_column_widths', None)
            if widths and len(widths) == table.columnCount():
                for i, width in enumerate(widths):
                    try:
                        table.setColumnWidth(i, int(width))
                    except Exception:
                        pass
        except Exception:
            pass

    def _create_version_info_widget(self, parent):
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(0)
        self.main_calibre_version_label = QLabel('calibre {}'.format(_calibre_version_text()), widget)
        self.main_plugin_version_label = QLabel(_('Columns Helper v.{}').format(_plugin_version_text()), widget)
        layout.addWidget(self.main_calibre_version_label)
        layout.addWidget(self.main_plugin_version_label)
        self._refresh_version_info_styles()
        return widget

    def _refresh_version_info_styles(self, *args):
        try:
            palette = self.palette()
            title_color = palette.color(QPalette.ColorRole.WindowText).name()
            meta_color = palette.color(QPalette.ColorRole.Mid).name()
        except Exception:
            title_color = '#444444'
            meta_color = '#777777'
        if hasattr(self, 'main_calibre_version_label'):
            self.main_calibre_version_label.setStyleSheet(
                'QLabel { color: %s; font-size: 8pt; font-weight: 600; padding: 0px; }' % title_color
            )
        if hasattr(self, 'main_plugin_version_label'):
            self.main_plugin_version_label.setStyleSheet(
                'QLabel { color: %s; font-size: 8pt; padding: 0px; }' % meta_color
            )

    def _build_detail_section(self, label, editor):
        container = QWidget(self)
        section_layout = QVBoxLayout(container)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(4)
        try:
            font = label.font()
            font.setBold(True)
            label.setFont(font)
        except Exception:
            pass
        section_layout.addWidget(label)
        section_layout.addWidget(editor, 1)
        return container

    def _create_selected_column_panel(self, parent):
        panel = QWidget(parent)
        panel.setMinimumWidth(0)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(6)

        self.selected_column_summary = QLabel(
            _('Select a column to inspect its data, templates, and current library tooltip.'),
            panel,
        )
        self.selected_column_summary.setWordWrap(True)
        panel_layout.addWidget(self.selected_column_summary)

        self.selected_meta_label = QLabel(_('Column data'), panel)
        self.selected_meta_edit = QPlainTextEdit(panel)
        self.selected_meta_edit.setReadOnly(True)

        self.selected_template_label = QLabel(_('Template'), panel)
        self.selected_template_edit = QPlainTextEdit(panel)
        self.selected_template_edit.setReadOnly(True)
        self.selected_template_edit.setPlaceholderText(_('No composite template for this column.'))
        self.selected_template_highlighter = TemplateHighlighter(self.selected_template_edit.document())

        self.selected_search_label = QLabel(_('Search template'), panel)
        self.selected_search_edit = QPlainTextEdit(panel)
        self.selected_search_edit.setReadOnly(True)
        self.selected_search_edit.setPlaceholderText(_('No web search template for this column.'))
        self.selected_search_highlighter = TemplateHighlighter(self.selected_search_edit.document())

        self.selected_tooltip_label = QLabel(_('Tooltip template'), panel)
        self.selected_tooltip_edit = QPlainTextEdit(panel)
        self.selected_tooltip_edit.setReadOnly(True)
        self.selected_tooltip_edit.setPlaceholderText(_column_tooltip_placeholder_text())
        self.selected_tooltip_highlighter = TemplateHighlighter(self.selected_tooltip_edit.document())

        self.selected_detail_splitter = QSplitter(panel)
        try:
            self.selected_detail_splitter.setOrientation(Qt.Orientation.Vertical)
        except Exception:
            self.selected_detail_splitter.setOrientation(Qt.Vertical)
        try:
            self.selected_detail_splitter.setChildrenCollapsible(False)
        except Exception:
            pass
        self.selected_detail_splitter.addWidget(self._build_detail_section(self.selected_meta_label, self.selected_meta_edit))
        self.selected_detail_splitter.addWidget(self._build_detail_section(self.selected_template_label, self.selected_template_edit))
        self.selected_detail_splitter.addWidget(self._build_detail_section(self.selected_search_label, self.selected_search_edit))
        self.selected_detail_splitter.addWidget(self._build_detail_section(self.selected_tooltip_label, self.selected_tooltip_edit))
        try:
            self.selected_detail_splitter.splitterMoved.connect(lambda *_args: self._save_selected_detail_sizes())
        except Exception:
            pass
        panel_layout.addWidget(self.selected_detail_splitter, 1)
        return panel

    def _selected_columns_table(self):
        return getattr(getattr(self, 'widget', None), 'opt_columns', None)

    def _selected_column_indexes(self):
        widget = getattr(self, 'widget', None)
        return {
            'order': int(getattr(widget, 'ORDER_COLUMN', 0)),
            'header': int(getattr(widget, 'HEADER_COLUMN', 1)),
            'key': int(getattr(widget, 'KEY_COLUMN', 2)),
            'type': int(getattr(widget, 'TYPE_COLUMN', 3)),
            'description': int(getattr(widget, 'DESCRIPTION_COLUMN', 4)),
            'status': int(getattr(widget, 'STATUS_COLUMN', 5)),
            'id': 3,
        }

    def _selected_row(self):
        table = self._selected_columns_table()
        if table is None:
            return -1
        try:
            row = int(table.currentRow())
        except Exception:
            row = -1
        if row >= 0:
            return row
        try:
            index = table.currentIndex()
            if index is not None and index.isValid():
                return int(index.row())
        except Exception:
            pass
        return -1

    def _table_text(self, row, col):
        table = self._selected_columns_table()
        if table is None or row < 0 or col < 0 or col >= table.columnCount():
            return ''
        item = table.item(row, col)
        return str(item.text() if item is not None else '').strip()

    def _current_library_tooltip_template(self, lookup_name):
        lookup_name = str(lookup_name or '').strip()
        if not lookup_name:
            return ''
        db = getattr(self.gui, 'current_db', None)
        api = getattr(db, 'new_api', None) if db is not None else None
        if api is None:
            return ''
        try:
            templates = dict(api.pref('column_tooltip_templates', {}) or {})
        except Exception:
            templates = {}
        return str(templates.get(lookup_name, '') or '').strip()

    def _selected_column_payload(self):
        table = self._selected_columns_table()
        row = self._selected_row()
        if table is None or row < 0 or row >= table.rowCount():
            return None

        columns = self._selected_column_indexes()

        lookup_name = self._table_text(row, columns['key'])
        heading = self._table_text(row, columns['header'])
        id_text = self._table_text(row, columns['id'])
        type_text = self._table_text(row, columns['type'])
        description_text = self._table_text(row, columns['description'])
        status_text = self._table_text(row, columns['status'])
        order_text = self._table_text(row, columns['order'])
        order_item = table.item(row, columns['order'])
        hidden = False
        try:
            hidden = order_item.checkState() == Qt.CheckState.Unchecked
        except Exception:
            try:
                hidden = order_item.checkState() == Qt.Unchecked
            except Exception:
                hidden = False

        cc = dict((getattr(self.widget, 'custcols', None) or {}).get(lookup_name) or {})
        display = dict(cc.get('display') or {})
        if not description_text:
            description_text = str(display.get('description') or '').strip()

        meta = {
            'lookup_name': lookup_name,
            'heading': heading,
            'id': id_text,
            'datatype': type_text,
            'description': description_text,
            'status': status_text,
            'visible': not hidden,
            'custom': lookup_name.startswith('#'),
            'order': order_text,
            'display': display,
        }
        if 'is_multiple' in cc:
            meta['is_multiple'] = bool(cc.get('is_multiple'))

        return {
            'heading': heading,
            'lookup_name': lookup_name,
            'hidden': hidden,
            'meta': meta,
            'template': str(display.get('composite_template') or '').strip(),
            'search_template': str(display.get('web_search_template') or '').strip(),
            'tooltip_template': self._current_library_tooltip_template(lookup_name),
        }

    def _toggle_details_panel(self):
        sizes = list(self.main_splitter.sizes())
        if len(sizes) < 2:
            return
        if sizes[1] > 10:
            self._cached_detail_width = sizes[1]
            self.main_splitter.setSizes([sizes[0] + sizes[1], 0])
            self.details_toggle_button.setChecked(False)
        else:
            restore = getattr(self, '_cached_detail_width', 320)
            self.main_splitter.setSizes([max(480, sizes[0] - restore), max(restore, 200)])
            self.details_toggle_button.setChecked(True)

    def _on_main_splitter_moved(self, *_args):
        self._save_main_splitter_sizes()
        sizes = list(self.main_splitter.sizes())
        if len(sizes) >= 2:
            if sizes[1] > 10:
                self._cached_detail_width = sizes[1]
                self.details_toggle_button.setChecked(True)
            else:
                self.details_toggle_button.setChecked(False)

    def _save_main_splitter_sizes(self):
        try:
            gprefs[self._main_splitter_sizes_key] = [int(v) for v in self.main_splitter.sizes()]
        except Exception:
            pass

    def _restore_main_splitter_sizes(self):
        sizes = gprefs.get(self._main_splitter_sizes_key, None)
        try:
            if isinstance(sizes, (list, tuple)) and len(sizes) >= 2:
                self.main_splitter.setSizes([max(480, int(sizes[0])), max(0, int(sizes[1]))])
                if sizes[1] > 10:
                    self._cached_detail_width = sizes[1]
                    self.details_toggle_button.setChecked(True)
                else:
                    self.details_toggle_button.setChecked(False)
            else:
                self.main_splitter.setSizes([max(820, int(self.width() or 1120)), 0])
                self.details_toggle_button.setChecked(False)
        except Exception:
            pass

    def _save_selected_detail_sizes(self):
        try:
            gprefs[self._detail_splitter_sizes_key] = [int(v) for v in self.selected_detail_splitter.sizes()]
        except Exception:
            pass

    def _restore_selected_detail_sizes(self):
        sizes = gprefs.get(self._detail_splitter_sizes_key, None)
        try:
            if isinstance(sizes, (list, tuple)) and len(sizes) >= 4:
                self.selected_detail_splitter.setSizes([max(80, int(v)) for v in sizes[:4]])
            else:
                self.selected_detail_splitter.setSizes([230, 130, 120, 120])
        except Exception:
            pass

    def _attach_selected_column_panel_hooks(self):
        table = self._selected_columns_table()
        if table is None or table is getattr(self, '_selected_panel_hooked_table', None):
            return
        self._selected_panel_hooked_table = table
        try:
            table.currentCellChanged.connect(self._refresh_selected_column_panel)
        except Exception:
            pass
        try:
            table.itemSelectionChanged.connect(self._refresh_selected_column_panel)
        except Exception:
            pass
        try:
            table.itemChanged.connect(lambda *_args: QTimer.singleShot(0, self._refresh_selected_column_panel))
        except Exception:
            pass

    def _refresh_selected_column_panel(self, *args):
        self._attach_selected_column_panel_hooks()
        payload = self._selected_column_payload()
        if not payload:
            self.selected_column_summary.setText(
                _('Select a column to inspect its data, templates, and current library tooltip.')
            )
            self.selected_meta_edit.setPlainText('')
            self.selected_template_edit.setPlainText('')
            self.selected_search_edit.setPlainText('')
            self.selected_tooltip_label.setText(_('Tooltip template'))
            self.selected_tooltip_edit.setPlainText('')
            return

        heading = payload.get('heading') or payload.get('lookup_name') or _('Selected column')
        lookup_name = payload.get('lookup_name') or ''
        state_text = _('hidden') if payload.get('hidden') else _('visible')
        if lookup_name and lookup_name != heading:
            summary = _('{0} — {1} — {2}').format(heading, lookup_name, state_text)
        else:
            summary = _('{0} — {1}').format(heading, state_text)
        self.selected_column_summary.setText(summary)
        meta = payload.get('meta') or {}
        display = dict(meta.get('display') or {})
        custom = meta.get('custom', False)
        datatype = meta.get('datatype')
        if custom:
            # For custom columns, prefer actual datatype from definition over table text
            cc = dict((getattr(self.widget, 'custcols', None) or {}).get(meta.get('lookup_name') or '', {}))
            datatype = cc.get('datatype', datatype)

        edit_states = {'New', 'Modified', 'Deleted', 'Restored', 'Edited'}
        status_text = meta.get('status') or ''
        description_text = meta.get('description') or display.get('description') or ''

        if status_text in edit_states:
            status = status_text
        else:
            status = ''
            if custom and status_text and status_text != description_text:
                description_text = status_text

        meta_lines = [
            '{0}: {1}'.format(_('Column heading'), meta.get('heading') or ''),
            '{0}: {1}'.format(_('Lookup name'), meta.get('lookup_name') or ''),
            '{0}: {1}'.format(_('ID'), meta.get('id') or ''),
            '{0}: {1}'.format(_('Data type'), datatype or ''),
            '{0}: {1}'.format(_('Is multiple'), _('Yes') if meta.get('is_multiple') else _('No')),
            '{0}: {1}'.format(_('Description'), description_text),
            '{0}: {1}'.format(_('Status'), status) if status else '',
            '{0}: {1}'.format(_('Visible'), _('Yes') if meta.get('visible') else _('No')),
            '{0}: {1}'.format(_('Custom column'), _('Yes') if custom else _('No')),
            '{0}: {1}'.format(_('Order'), meta.get('order') or ''),
            '',
            _('Display settings') + ':',
            json.dumps(display, indent=2, ensure_ascii=False, sort_keys=True),
        ]
        meta_lines = [line for line in meta_lines if line]  # Remove empty status line
        self.selected_meta_edit.setPlainText('\n'.join(meta_lines))
        self.selected_template_edit.setPlainText(payload.get('template') or '')
        self.selected_search_edit.setPlainText(payload.get('search_template') or '')
        tooltip_text = payload.get('tooltip_template') or ''
        self.selected_tooltip_label.setText(
            _('Tooltip template (current library setting)') if tooltip_text else _('Tooltip template')
        )
        self.selected_tooltip_edit.setPlainText(tooltip_text)

    def _do_on_child_tabs(self, method_name, *args):
        callback = getattr(self.widget, 'do_on_child_tabs', None)
        if callable(callback):
            try:
                return callback(method_name, *args)
            except Exception as err:
                if COLUMNS_HELPER_DEBUG_ENABLED:
                    debug_print('[ColumnsHelper][DEBUG] do_on_child_tabs failed:', method_name, repr(err))
                return None
        if COLUMNS_HELPER_DEBUG_ENABLED:
            debug_print('[ColumnsHelper][DEBUG] do_on_child_tabs unavailable:', method_name)
        return None

    def _save_widget_column_layout(self):
        try:
            saver = getattr(self.widget, '_cc_filter_save_layout', None)
            if callable(saver):
                saver()
        except Exception:
            pass

    def _restore_widget_column_layout(self):
        try:
            restorer = getattr(self.widget, '_cc_filter_restore_layout', None)
            if callable(restorer):
                restorer()
        except Exception:
            pass

    def _get_scrollbar_stylesheet(self):
        """Return CCR-style scrollbar stylesheet with theme-aware colors"""
        return _ccr_scrollbar_stylesheet()

    def on_changed(self, *args):
        self.apply_button.setEnabled(True)
        self.apply_button.setDefault(True)
        self.apply_button.setAutoDefault(True)

    def restore_defaults(self):
        try:
            self._do_on_child_tabs('restore_defaults')
            self.widget.restore_defaults()
            self.on_changed()
        except Exception:
            pass

    def apply_changes(self):
        self._save_widget_column_layout()
        try:
            must_restart = bool(self._do_on_child_tabs('commit')) | bool(self.widget.commit())
        except AbortCommit:
            return False

        self.restart_required = must_restart
        if must_restart:
            self.gui.must_restart_before_config = True
            rc = self.widget.restart_critical
            msg = _restart_message_text() if rc else _(
                'Some of the changes you made require a restart. Please restart calibre as soon as possible.'
            )
            if show_restart_warning(msg, parent=self):
                try:
                    self.close()
                finally:
                    self.gui.quit(restart=True)
                return True

        self._do_on_child_tabs('refresh_gui', self.gui)
        self.widget.refresh_gui(self.gui)
        self.apply_button.setEnabled(False)
        self.close_button.setDefault(True)
        return True

    def reject(self):
        QDialog.reject(self)

    def keyPressEvent(self, event):
        try:
            if event.key() == Qt.Key.Key_Escape or event.key() == Qt.Key_Escape:
                self.reject()
                return
        except Exception:
            pass
        QDialog.keyPressEvent(self, event)

    def _configure_helper_button(self, button):
        try:
            button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        except Exception:
            try:
                button.setPopupMode(QToolButton.InstantPopup)
            except Exception:
                pass
        try:
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        except Exception:
            try:
                button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            except Exception:
                pass
        try:
            button.setMinimumHeight(26)
        except Exception:
            pass

    def _refresh_quick_create_ui(self):
        self.quick_create_label.setText(self._builtins_quick_create_markup())
        self.plugin_helpers_button.setMenu(self._build_plugin_helpers_menu())

    def _default_status_message(self):
        return _(
            'Ready. Use the quick-create links or open the packs dialog to add curated columns.\nPacks provide suggestions and known defaults; choose the final lookup names and column headings that best fit your library and interface language.'
        )

    def _status_stylesheet(self, tone='info'):
        if _is_dark_theme():
            background = '#2b2b2b'
            border = '#555555'
            foreground = '#90EE90' if tone == 'success' else '#c8ccd2'
        else:
            background = '#f0f0f0'
            border = '#cccccc'
            foreground = '#006400' if tone == 'success' else '#5a5a5a'
        return (
            'background-color: {0}; border: 1px solid {1}; border-radius: 4px; '
            'padding: 8px; color: {2}; font-weight: {3}; font-size: 12pt;'
        ).format(background, border, foreground, 'bold' if tone == 'success' else 'normal')

    def _set_status_message(self, text=None, tone='info'):
        self._status_tone = tone
        self._status_text = text or self._default_status_message()
        try:
            self.status_label.setText(self._status_text)
            self.status_label.setStyleSheet(self._status_stylesheet(tone))
        except Exception:
            pass

    def _refresh_status_label_style(self, *args):
        self._set_status_message(getattr(self, '_status_text', None), getattr(self, '_status_tone', 'info'))

    def _load_local_pixmap(self, relative_path):
        try:
            local_path = os.path.join(os.path.dirname(__file__), relative_path.replace('/', os.sep))
            if os.path.exists(local_path):
                pixmap = QPixmap()
                if pixmap.load(local_path):
                    return pixmap
        except Exception:
            pass
        return None

    def _prebuild_about_dialog(self):
        if hasattr(self, '_about_dialog') and _qt_object_is_alive(self._about_dialog):
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(_('About Columns Helper'))
        themed_icon = _get_plugin_icon('images/iconplugin_light.png', plugin_name=PLUGIN_NAME)
        if themed_icon is None or themed_icon.isNull():
            themed_icon = _get_themed_plugin_icon('iconplugin_light.png')
        if themed_icon is not None and not themed_icon.isNull():
            dialog.setWindowIcon(themed_icon)
        dialog.resize(540, 510)
        dialog.setMinimumSize(480, 420)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(8)

        tabs = QTabWidget(dialog)
        tabs.setStyleSheet(_ccr_tabs_stylesheet())

        align_center = getattr(Qt.AlignmentFlag, 'AlignCenter', getattr(Qt, 'AlignCenter', 0x0084))
        align_hcenter = getattr(Qt.AlignmentFlag, 'AlignHCenter', getattr(Qt, 'AlignHCenter', 0x0004))
        align_top = getattr(Qt.AlignmentFlag, 'AlignTop', getattr(Qt, 'AlignTop', 0x0020))

        # Tab 1: About
        about_page = QWidget(tabs)
        about_layout = QVBoxLayout(about_page)
        about_layout.setContentsMargins(12, 14, 12, 12)
        about_layout.setSpacing(10)
        about_layout.setAlignment(align_top)

        try:
            from calibre_plugins.columns_helper import ColumnsHelperPlugin
            ver = '.'.join(str(x) for x in ColumnsHelperPlugin.version)
        except Exception:
            ver = '1.0.0'

        tip_text = _('Show appreciation')

        html = (
            '<style>a {{ text-decoration: none; }}</style>'
            '<div align="center">'
            '<h2>{0}</h2>'
            '<p>' + _('Create custom columns with ease, find the best presets for your needs, and manage them on a user-friendly interface.') + '</p>'
            '<p style="font-size:9pt; color:gray;">' + _('Version: {0}').format(ver) + '</p>'
            '<p style="font-size:11pt;"><a href="https://www.mobileread.com/forums/showthread.php?t=372614">' + _('MR help thread') + '</a></p>'
            '<p style="font-size:12pt;">' + '<a href="https://ko-fi.com/comfy_n">' + tip_text + '</a></p>'
            '</div>'
        ).format(PLUGIN_NAME)
        text_label = QLabel(html, about_page)
        text_label.setAlignment(align_center)
        text_label.setWordWrap(True)
        try:
            text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        except Exception:
            text_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        text_label.setOpenExternalLinks(False)
        try:
            text_label.linkActivated.connect(open_url)
        except Exception:
            pass
        about_layout.addWidget(text_label)

        qr_label = QLabel(about_page)
        qr_label.setAlignment(align_center)
        self._qr_label = qr_label
        self._qr_showing_qr = True
        about_layout.addWidget(self._qr_label)

        qr_data = getattr(self, '_cached_qr_data', None)
        if qr_data:
            qp = QPixmap()
            if qp.loadFromData(qr_data):
                smooth_trans = getattr(Qt.TransformationMode, 'SmoothTransformation', getattr(Qt, 'SmoothTransformation', 1))
                pointing_hand = getattr(Qt.CursorShape, 'PointingHandCursor', getattr(Qt, 'PointingHandCursor', 13))
                self._qr_label.setPixmap(qp.scaledToWidth(150, smooth_trans))
                self._qr_label.setCursor(pointing_hand)
                self._qr_label.mousePressEvent = self._flip_qr_image
        else:
            self._qr_label.setVisible(False)

        about_layout.addStretch(1)
        tabs.addTab(about_page, _('About'))

        # Tab 2: More plugins
        more_page = QWidget(tabs)
        more_layout = QVBoxLayout(more_page)
        more_layout.setContentsMargins(4, 6, 4, 4)
        more_layout.setSpacing(6)

        scroll = QScrollArea(more_page)
        scroll.setWidgetResizable(True)
        try:
            scroll.setFrameShape(QFrame.Shape.NoFrame)
        except Exception:
            scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(_ccr_scrollbar_stylesheet())

        content = QWidget(scroll)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 8, 10, 8)
        content_layout.setSpacing(4)
        content_layout.setAlignment(align_top)

        more_title = QLabel('<b>' + _('More plugins') + '</b>', content)
        more_title.setStyleSheet('font-size: 13.5pt;' if ismacos else 'font-size: 12pt;')
        more_title.setAlignment(align_hcenter)
        content_layout.addWidget(more_title)
        content_layout.addSpacing(4)

        ext_pm = _external_link_pixmap(14)
        for p_name, p_desc, p_url in MORE_PLUGINS_DATA:
            row = QWidget(content)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            if ext_pm is not None and not ext_pm.isNull():
                icon_lbl = QLabel(row)
                icon_lbl.setPixmap(ext_pm)
                icon_lbl.setFixedWidth(18)
                icon_lbl.setAlignment(align_center)
            else:
                icon_lbl = QLabel('🔗', row)
                icon_lbl.setFixedWidth(18)
                icon_lbl.setAlignment(align_center)
            row_layout.addWidget(icon_lbl)

            link = NoUnderlineLinkLabel(p_name, p_url, row)
            link.setStyleSheet(
                'font-size: 10.5pt; color: palette(link);' if ismacos else 'font-size: 9.5pt; color: palette(link);')
            row_layout.addWidget(link)

            desc = ElidedDescriptionLabel(' — ' + p_desc, row)
            desc.setStyleSheet(
                'font-size: 10.5pt; color: palette(mid);' if ismacos else 'font-size: 9.5pt; color: palette(mid);')
            row_layout.addWidget(desc, 1)

            content_layout.addWidget(row)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        more_layout.addWidget(scroll, 1)
        tabs.addTab(more_page, _('More plugins'))

        layout.addWidget(tabs, 1)

        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(4, 2, 4, 2)
        version_label = QLabel(_('{0} v.{1} | calibre {2}').format(PLUGIN_NAME, _plugin_version_text(), _calibre_version_text()), dialog)
        version_label.setStyleSheet('color: palette(mid); font-size: 8pt;')
        footer.addWidget(version_label)
        footer.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, dialog)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        close_icon = _get_close_action_icon()
        if close_icon is not None and close_btn is not None:
            close_btn.setIcon(close_icon)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        footer.addWidget(buttons)

        layout.addLayout(footer)

        self._about_dialog = dialog

    def show_about_dialog(self):
        if not hasattr(self, '_about_dialog'):
            self._prebuild_about_dialog()
        try:
            self._about_dialog.show()
            self._about_dialog.raise_()
            self._about_dialog.activateWindow()
        except Exception:
            pass

    def _flip_qr_image(self, event):
        """Open Ko-fi link when QR code is clicked"""
        try:
            QTimer.singleShot(0, lambda: open_url('https://ko-fi.com/comfy_n'))
        except Exception:
            pass

    def show_helper_showroom(self):
        get_presets = getattr(self.widget, '_cdf_get_quick_create_presets', None)
        get_definitions = getattr(self.widget, '_cdf_get_helper_group_definitions', None)
        if get_presets is None or get_definitions is None:
            return
        dialog = open_helper_showroom_dialog(
            self,
            group_definitions=get_definitions(),
            get_presets=get_presets,
            create_one=self.run_quick_create,
            create_many=self.run_quick_create_batch,
        )
        return dialog

    def _patched_save_geometry(self):
        """Save geometry using separate gprefs keys for modeless dialog"""
        try:
            table = getattr(self.widget, 'opt_columns', None)
            if table is not None:
                widths = []
                for i in range(table.columnCount()):
                    widths.append(table.columnWidth(i))
                gprefs.set('columns_helper_modeless_table_geometry', widths)

                # Save column order using separate key
                column_positions = []
                header = table.horizontalHeader()
                for vi in range(table.columnCount()):
                    column_positions.append(header.logicalIndex(vi))
                gprefs.set('columns_helper_modeless_column_order', column_positions)
        except Exception:
            pass

    def _patched_restore_geometry(self):
        """Restore geometry using separate gprefs keys for modeless dialog"""
        try:
            table = getattr(self.widget, 'opt_columns', None)
            if table is not None:
                geom = gprefs.get('columns_helper_modeless_table_geometry', None)
                if geom is not None and len(geom) == table.columnCount():
                    try:
                        for i in range(table.columnCount()):
                            table.setColumnWidth(i, geom[i])
                    except Exception:
                        pass

                # Restore column order from separate key
                column_positions = gprefs.get('columns_helper_modeless_column_order', None)
                if column_positions is not None and len(column_positions) == table.columnCount():
                    try:
                        header = table.horizontalHeader()
                        for dvi, li in enumerate(column_positions):
                            cvi = header.visualIndex(li)
                            if cvi != dvi:
                                header.moveSection(cvi, dvi)
                    except Exception:
                        pass
        except Exception:
            pass

    def _inject_id_column(self):
        try:
            table = getattr(self.widget, 'opt_columns', None)
            if table is None:
                return

            # Guard: if ID column already exists in the expected slot, do not insert again.
            try:
                existing_header = table.horizontalHeaderItem(3)
                if existing_header is not None and str(existing_header.text() or '').strip().casefold() == 'id':
                    return
            except Exception:
                pass

            # Insert ID column after KEY_COLUMN (index 2)
            table.insertColumn(3)

            # Keep search-template column index in sync after insertion.
            try:
                idx = getattr(self.widget, '_cc_filter_search_template_column', None)
                if idx is not None and int(idx) >= 3:
                    self.widget._cc_filter_search_template_column = int(idx) + 1
                    if COLUMNS_HELPER_DEBUG_ENABLED:
                        debug_print('[ColumnsHelper][DEBUG] _inject_id_column: shifted _cc_filter_search_template_column from', idx, 'to', int(idx) + 1)
            except Exception as err:
                if COLUMNS_HELPER_DEBUG_ENABLED:
                    debug_print('[ColumnsHelper][DEBUG] _inject_id_column: could not shift search-template column index', repr(err))

            # Set header with bold font
            header_item = QTableWidgetItem('ID')
            header_item.setToolTip('Column creation ID (chronological order)')
            try:
                font = header_item.font()
                font.setBold(True)
                header_item.setFont(font)
            except Exception:
                pass
            table.setHorizontalHeaderItem(3, header_item)

            # Populate ID values and apply color coding
            for row in range(table.rowCount()):
                try:
                    key_item = table.item(row, 2)
                    if key_item is None:
                        continue
                    key = key_item.text()

                    # Get colnum from custcols
                    custcols = getattr(self.widget, 'custcols', None)
                    if custcols and key in custcols:
                        colnum = custcols[key].get('colnum', '')
                        id_item = QTableWidgetItem()
                        try:
                            id_item.setData(Qt.ItemDataRole.DisplayRole, int(colnum))
                        except Exception:
                            id_item.setText(str(colnum))
                        id_item.setToolTip(str(colnum))
                        id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        table.setItem(row, 3, id_item)

                        # Apply color coding to template/web-search-template columns
                        self._apply_template_color_coding(row, key, custcols[key])
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_template_color_coding(self, row, key, col_meta):
        """Apply theme-responsive color coding to columns with templates"""
        try:
            if not self.template_color_checkbox.isChecked():
                return

            table = getattr(self.widget, 'opt_columns', None)
            if table is None:
                return

            is_template = False
            template_type = None

            # Check for composite template
            display = col_meta.get('display', {})
            if display.get('composite_template'):
                is_template = True
                template_type = 'composite'

            # Check for web search template
            if display.get('web_search_template'):
                is_template = True
                template_type = 'web_search'

            if not is_template:
                return

            # Theme-responsive color coding: green and #fced62
            if _is_dark_theme():
                bg_color = '#1a4d2e'  # Dark green
                fg_color = '#fcedc2'  # Yellow
            else:
                bg_color = '#e8f5e9'  # Light green
                fg_color = '#1b5e20'  # Dark green

            # Apply to all columns except STATUS (which stays unchanged)
            for col in range(table.columnCount()):
                if col == 5:  # STATUS_COLUMN
                    continue
                item = table.item(row, col)
                if item is not None:
                    try:
                        item.setBackground(QBrush(QColor(bg_color)))
                        item.setForeground(QBrush(QColor(fg_color)))
                    except Exception:
                        pass
        except Exception:
            pass

    def on_template_color_changed(self, state):
        """Handle checkbox toggle for template coloring"""
        try:
            gprefs['columns_helper_template_coloring'] = bool(state)
            self._refresh_template_coloring()
        except Exception:
            pass

    def _refresh_template_coloring(self):
        """Refresh template coloring after checkbox toggle or palette change"""
        try:
            table = getattr(self.widget, 'opt_columns', None)
            if table is None:
                return

            custcols = getattr(self.widget, 'custcols', None)
            if custcols is None:
                return

            for row in range(table.rowCount()):
                try:
                    key_item = table.item(row, 2)
                    if key_item is None:
                        continue
                    key = key_item.text()
                    if key in custcols:
                        # Clear existing colors if coloring is disabled
                        if not self.template_color_checkbox.isChecked():
                            for col in range(table.columnCount()):
                                if col == 5:
                                    continue
                                item = table.item(row, col)
                                if item is not None:
                                    item.setBackground(QBrush())
                                    item.setForeground(QBrush())
                        else:
                            self._apply_template_color_coding(row, key, custcols[key])
                except Exception:
                    pass
        except Exception:
            pass

    def _builtins_quick_create_markup(self):
        get_presets = getattr(self.widget, '_cdf_get_quick_create_presets', None)
        if get_presets is None:
            return ''
        presets = get_presets('builtin')
        links = []
        for key in ('isbn', 'formats', 'yesno', 'tags', 'series', 'rating', 'people', 'text', 'read_progress'):
            preset = presets.get(key)
            if preset is None:
                continue
            links.append('<a href="builtin:{0}">{1}</a>'.format(key, preset['link_text']))
        if not links:
            return ''
        return '<p>{0} {1}</p>'.format(_('Quick create:'), ', '.join(links))

    def _build_helper_menu(self, group):
        menu = QMenu(self)
        get_presets = getattr(self.widget, '_cdf_get_quick_create_presets', None)
        if get_presets is None:
            return menu
        presets = get_presets(group)
        ordered_keys = [key for key in presets if key != '__all__']
        all_action = menu.addAction(_('Create all'))
        all_action.setEnabled(bool(ordered_keys))
        all_action.triggered.connect(lambda _checked=False, g=group, keys=ordered_keys: self.run_quick_create_batch(g, keys))
        menu.addSeparator()
        for key in ordered_keys:
            preset = presets[key]
            action = menu.addAction(_qt_menu_text(preset['menu_text']))
            action.triggered.connect(lambda _checked=False, g=group, k=key: self.run_quick_create(g, k))
        return menu

    def _build_plugin_helpers_menu(self):
        menu = QMenu(self)
        get_definitions = getattr(self.widget, '_cdf_get_helper_group_definitions', None)
        if get_definitions is None:
            return menu
        group_definitions = list(get_definitions() or [])
        sections = []
        section_map = {}
        for group_def in group_definitions:
            section_key = group_def.get('section') or 'other'
            section_title = group_def.get('section_title') or section_key
            bucket = section_map.get(section_key)
            if bucket is None:
                bucket = {'title': section_title, 'groups': []}
                section_map[section_key] = bucket
                sections.append(bucket)
            bucket['groups'].append(group_def)

        for section in sections:
            section_menu = QMenu(menu)
            try:
                section_menu.setTitle(_qt_menu_text(section['title']))
            except Exception:
                pass
            for group_def in section['groups']:
                group_key = group_def.get('key')
                title = group_def.get('title') or group_key or ''
                if not group_key:
                    continue
                submenu = self._build_helper_menu(group_key)
                try:
                    submenu.setTitle(_qt_menu_text(title))
                except Exception:
                    pass
                section_menu.addMenu(submenu)
            if not section_menu.isEmpty():
                menu.addMenu(section_menu)
        return menu

    def _show_quick_create_status(self, text):
        display_text = (text or '').replace('Created', 'Added').replace('created', 'added already')
        if display_text:
            self._set_status_message(display_text, tone='success')
            QTimer.singleShot(8500, self._clear_status_label)

    def _clear_status_label(self):
        self._set_status_message()

    def on_quick_create_link(self, url):
        parts = str(url or '').split(':', 1)
        if len(parts) != 2:
            return
        self.run_quick_create(parts[0], parts[1])

    def run_quick_create(self, group, key):
        if not _qt_object_is_alive(self) or not _qt_object_is_alive(getattr(self, 'widget', None)) or not _qt_object_is_alive(getattr(getattr(self, 'widget', None), 'opt_columns', None)):
            self._set_status_message(_('The columns window was closed. Reopen Columns Helper and try again.'))
            return None
        create = getattr(self.widget, '_cdf_quick_create_columns', None)
        if create is None:
            return None
        messages = create(group, [key])
        if messages:
            self._show_quick_create_status(messages[-1])
            self.on_changed()
        return self

    def run_quick_create_batch(self, group, keys):
        if not _qt_object_is_alive(self) or not _qt_object_is_alive(getattr(self, 'widget', None)) or not _qt_object_is_alive(getattr(getattr(self, 'widget', None), 'opt_columns', None)):
            self._set_status_message(_('The columns window was closed. Reopen Columns Helper and try again.'))
            return None
        create = getattr(self.widget, '_cdf_quick_create_columns', None)
        if create is None:
            return None
        messages = create(group, list(keys))
        if messages:
            self._show_quick_create_status('; '.join(messages[:3]) if len(messages) > 1 else messages[0])
            self.on_changed()
        return self

    def open_to_lookup(self, lookup_name):
        lookup_name = str(lookup_name or '').strip()
        widget = getattr(self, 'widget', None)
        if not lookup_name or not _qt_object_is_alive(self) or not _qt_object_is_alive(widget):
            return False

        try:
            self.showNormal()
        except Exception:
            pass
        try:
            self.raise_()
        except Exception:
            pass
        try:
            self.activateWindow()
        except Exception:
            pass

        def apply_lookup():
            if not _qt_object_is_alive(widget):
                return False
            try:
                refresh_filter = getattr(widget, 'refresh_filter', None)
                if callable(refresh_filter):
                    refresh_filter()
            except Exception:
                pass

            query = 'lookup:{0}'.format(lookup_name)
            combo = getattr(widget, '_cc_filter_edit', None)
            try:
                if isinstance(combo, QComboBox):
                    combo.setEditText(query)
                    line_edit = combo.lineEdit()
                    if line_edit is not None:
                        line_edit.setText(query)
                        line_edit.selectAll()
                elif isinstance(combo, QLineEdit):
                    combo.setText(query)
                    combo.selectAll()
            except Exception:
                pass

            try:
                apply_filter_fn = getattr(widget, 'apply_filter', None)
                if callable(apply_filter_fn):
                    apply_filter_fn()
            except Exception:
                pass

            try:
                select_row = getattr(widget, 'select_row_for_lookup', None)
                if callable(select_row) and select_row(lookup_name):
                    self._set_status_message(_('Showing column: {0}').format(lookup_name), tone='success')
                    return True
            except Exception:
                pass
            return False

        try:
            if apply_lookup():
                return True
        except Exception:
            pass
        try:
            QTimer.singleShot(0, apply_lookup)
            QTimer.singleShot(75, apply_lookup)
        except Exception:
            pass
        return True

    def _install_escape_filters(self):
        # For modeless dialogs, don't install app-wide event filter as it can interfere
        # Only install on the dialog and its children
        watched = [self, self.widget, self.button_box, self.apply_button, self.close_button, self.defaults_button]
        for obj in watched:
            if obj is None:
                continue
            try:
                obj.installEventFilter(self)
            except Exception:
                pass
        try:
            for child in self.findChildren(QWidget):
                try:
                    child.installEventFilter(self)
                except Exception:
                    pass
        except Exception:
            pass

    def _event_targets_this_dialog(self, obj):
        widget = obj if isinstance(obj, QWidget) else QApplication.focusWidget()
        while widget is not None:
            if widget is self:
                return True
            try:
                widget = widget.parentWidget()
            except Exception:
                break
        return False

    def eventFilter(self, obj, event):
        try:
            event_type = event.type()
        except Exception:
            event_type = None
        if event_type == QEvent.Type.KeyPress or event_type == QEvent.KeyPress:
            try:
                modal_widget = QApplication.activeModalWidget()
                owns_event = self._event_targets_this_dialog(obj)
                if (event.key() == Qt.Key.Key_Escape or event.key() == Qt.Key_Escape) and owns_event and (modal_widget is None or modal_widget is self):
                    self.reject()
                    return True
            except Exception:
                pass
        return QDialog.eventFilter(self, obj, event)

    def closeEvent(self, event):
        if getattr(self, '_cdf_app_event_filter_installed', False):
            app = QApplication.instance()
            if app is not None:
                try:
                    app.removeEventFilter(self)
                except Exception:
                    pass
        self._save_widget_column_layout()
        self._save_main_splitter_sizes()
        self._save_selected_detail_sizes()
        try:
            gprefs['columns_dialog_filter_modeless_geometry'] = bytearray(self.saveGeometry())
        except Exception:
            pass
        QDialog.closeEvent(self, event)

    def showEvent(self, event):
        QDialog.showEvent(self, event)
        QTimer.singleShot(0, self._restore_widget_column_layout)
        QTimer.singleShot(75, self._restore_widget_column_layout)
        QTimer.singleShot(0, self._restore_main_splitter_sizes)
        QTimer.singleShot(0, self._restore_selected_detail_sizes)
        QTimer.singleShot(0, self._refresh_selected_column_panel)


def open_modeless_columns_dialog(gui, parent=None, show_window=True):
    global _MODELESS_COLUMNS_DIALOG
    if gui is None:
        return None
    if COLUMNS_HELPER_DEBUG_ENABLED:
        debug_print('[ColumnsHelper][DEBUG] open_modeless_columns_dialog show_window={}'.format(bool(show_window)))
    try:
        if _MODELESS_COLUMNS_DIALOG is not None:
            if show_window:
                try:
                    if _MODELESS_COLUMNS_DIALOG.isMinimized():
                        _MODELESS_COLUMNS_DIALOG.showNormal()
                except Exception:
                    pass
                try:
                    _MODELESS_COLUMNS_DIALOG.show()
                except Exception:
                    pass
                _MODELESS_COLUMNS_DIALOG.raise_()
                _MODELESS_COLUMNS_DIALOG.activateWindow()
            return _MODELESS_COLUMNS_DIALOG
    except Exception:
        _MODELESS_COLUMNS_DIALOG = None

    dialog = ModelessColumnsDialog(gui, parent=None)
    dialog.destroyed.connect(_clear_modeless_dialog)
    _MODELESS_COLUMNS_DIALOG = dialog
    if show_window:
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
    else:
        try:
            dialog.show()
            dialog.hide()
        except Exception:
            pass
    return dialog


def _split_filter_text(text):
    text = (text or '').strip()
    if not text:
        return []
    try:
        return shlex.split(text)
    except Exception:
        return text.split()


def _install_columns_preferences_filter_patch():
    try:
        from calibre.gui2.preferences import columns as cols
    except Exception:
        return False

    if getattr(cols, '_columns_dialog_filter_patch_installed', False):
        return True

    original_init = cols.ConfigWidget.__init__
    original_genesis = cols.ConfigWidget.genesis
    original_init_columns = cols.ConfigWidget.init_columns
    original_add_custcol = cols.ConfigWidget.add_custcol
    original_edit_custcol = cols.ConfigWidget.edit_custcol
    original_del_custcol = cols.ConfigWidget.del_custcol
    original_show_all = getattr(cols.ConfigWidget, 'show_all', None)
    original_hide_all = getattr(cols.ConfigWidget, 'hide_all', None)
    original_restore_defaults = cols.ConfigWidget.restore_defaults
    original_table_sorted = cols.ConfigWidget.table_sorted
    original_up_column = cols.ConfigWidget.up_column
    original_down_column = cols.ConfigWidget.down_column
    original_header_moved = getattr(cols.ConfigWidget, 'header_moved', None)
    original_save_geometry = getattr(cols.ConfigWidget, 'save_geometry', None)
    original_restore_geometry = getattr(cols.ConfigWidget, 'restore_geometry', None)
    original_create_custom_column = cols.CreateCustomColumn
    original_set_up_down_enabled = cols.ConfigWidget.set_up_down_enabled

    def _is_plugin_context(widget):
        return bool(
            getattr(widget, '_from_plugin_action', False)
            or getattr(widget, '_cdf_in_modeless_host', False)
        )

    def patched_init(self, *args, **kwargs):
        if getattr(cols.ConfigWidget, '_creating_from_plugin', False):
            self._from_plugin_action = True
        return original_init(self, *args, **kwargs)

    def _swap_table_rows(widget, a, b):
        t = getattr(widget, 'opt_columns', None)
        if t is None:
            return False
        try:
            cols_count = int(t.columnCount() or 0)
        except Exception:
            cols_count = 0
        if cols_count <= 0:
            return False
        try:
            for c in range(cols_count):
                ia = t.takeItem(a, c)
                ib = t.takeItem(b, c)
                t.setItem(a, c, ib)
                t.setItem(b, c, ia)
        except Exception:
            return False
        return True

    def _move_row_to_index(widget, source_row, target_row):
        t = getattr(widget, 'opt_columns', None)
        if t is None:
            return
        try:
            row_count = int(t.rowCount() or 0)
        except Exception:
            row_count = 0
        try:
            cols_count = int(t.columnCount() or 0)
        except Exception:
            cols_count = 0
        if row_count <= 0 or cols_count <= 0:
            return
        if source_row < 0 or source_row >= row_count or target_row < 0 or target_row >= row_count or source_row == target_row:
            return
        try:
            t.setSortingEnabled(False)
        except Exception:
            pass
        row_data = []
        try:
            for col in range(cols_count):
                row_data.append(t.takeItem(source_row, col))
            t.removeRow(source_row)
            t.insertRow(target_row)
            for col, item in enumerate(row_data):
                if item is not None:
                    t.setItem(target_row, col, item)
            try:
                recreate_row = getattr(widget, 'recreate_row', None)
                if callable(recreate_row):
                    for row in range(row_count):
                        recreate_row(row)
            except Exception:
                pass
            try:
                widget.changed_signal.emit()
            except Exception:
                pass
        except Exception:
            try:
                t.setSortingEnabled(True)
            except Exception:
                pass
            return
        try:
            t.setCurrentCell(target_row, header_column)
        except Exception:
            try:
                t.setCurrentCell(target_row, 0)
            except Exception:
                pass
        try:
            t.setSortingEnabled(True)
        except Exception:
            pass
        # Do not call set_up_down_enabled() directly — calibre versions differ in signature.
        try:
            _update_move_top_bottom_enabled(widget)
        except Exception:
            pass

    def _update_move_top_bottom_enabled(widget):
        t = getattr(widget, 'opt_columns', None)
        if t is None:
            return
        try:
            row = int(t.currentRow())
        except Exception:
            row = -1
        try:
            last = int(t.rowCount() or 0) - 1
        except Exception:
            last = -1
        top_button = getattr(widget, '_cdf_move_top_button', None)
        bottom_button = getattr(widget, '_cdf_move_bottom_button', None)
        if top_button is not None:
            top_button.setEnabled(row > 0)
        if bottom_button is not None:
            bottom_button.setEnabled(row >= 0 and row < last)

    def _move_selected_column_to_top(widget):
        t = getattr(widget, 'opt_columns', None)
        if t is None:
            return
        try:
            row = int(t.currentRow())
        except Exception:
            row = -1
        if row <= 0:
            return
        _move_row_to_index(widget, row, 0)

    def _move_selected_column_to_bottom(widget):
        t = getattr(widget, 'opt_columns', None)
        if t is None:
            return
        try:
            row = int(t.currentRow())
        except Exception:
            row = -1
        try:
            last = int(t.rowCount() or 0) - 1
        except Exception:
            last = -1
        if row < 0 or row >= last:
            return
        _move_row_to_index(widget, row, last)

    def _find_button_layout_in_tree(layout, up_button, down_button):
        if layout is None or up_button is None or down_button is None:
            return None, -1, -1

        up_index = -1
        down_index = -1
        try:
            item_count = layout.count()
        except Exception:
            item_count = 0
        for i in range(item_count):
            try:
                item = layout.itemAt(i)
            except Exception:
                item = None
            if item is None:
                continue
            try:
                item_widget = item.widget()
            except Exception:
                item_widget = None
            if item_widget is up_button:
                up_index = i
            elif item_widget is down_button:
                down_index = i
        if up_index >= 0 and down_index >= 0 and up_index != down_index:
            return layout, up_index, down_index

        for i in range(item_count):
            try:
                item = layout.itemAt(i)
            except Exception:
                item = None
            if item is None:
                continue
            try:
                child_layout = item.layout()
            except Exception:
                child_layout = None
            found_layout, found_up, found_down = _find_button_layout_in_tree(child_layout, up_button, down_button)
            if found_layout is not None:
                return found_layout, found_up, found_down
            try:
                item_widget = item.widget()
            except Exception:
                item_widget = None
            if item_widget is not None:
                try:
                    nested_layout = item_widget.layout()
                except Exception:
                    nested_layout = None
                found_layout, found_up, found_down = _find_button_layout_in_tree(nested_layout, up_button, down_button)
                if found_layout is not None:
                    return found_layout, found_up, found_down
        return None, -1, -1

    def _find_common_button_layout(widget, up_button, down_button):
        root_layout = None
        try:
            root_layout = widget.layout()
        except Exception:
            root_layout = None
        layout, up_index, down_index = _find_button_layout_in_tree(root_layout, up_button, down_button)
        if layout is not None:
            return layout, up_index, down_index
        return None, -1, -1

    def _ensure_move_top_bottom_buttons(widget):
        if not _is_plugin_context(widget):
            return
        if getattr(widget, '_cdf_move_top_bottom_installed', False):
            return

        # Find the existing up/down buttons created by calibre.
        up_button = getattr(widget, 'up_button', None) or getattr(widget, 'column_up', None)
        down_button = getattr(widget, 'down_button', None) or getattr(widget, 'column_down', None)
        if up_button is None or down_button is None:
            return

        # In calibre's built-in columns dialog the arrows live in a nested sublayout.
        # Search the full layout tree rooted at the ConfigWidget.
        layout, up_index, down_index = _find_common_button_layout(widget, up_button, down_button)
        if layout is None:
            return

        try:
            parent = widget
        except Exception:
            parent = None
        if parent is None:
            return

        # Create buttons and insert them between Up and Down.
        move_top = QToolButton(parent)
        move_bottom = QToolButton(parent)
        try:
            move_top.setAutoRaise(True)
            move_bottom.setAutoRaise(True)
        except Exception:
            pass
        try:
            move_top.setIconSize(up_button.iconSize())
            move_bottom.setIconSize(down_button.iconSize())
        except Exception:
            pass
        try:
            move_top.setSizePolicy(up_button.sizePolicy())
            move_bottom.setSizePolicy(down_button.sizePolicy())
        except Exception:
            pass
        try:
            move_top.setMinimumSize(up_button.minimumSize())
            move_bottom.setMinimumSize(down_button.minimumSize())
        except Exception:
            pass
        try:
            move_top.setMaximumSize(up_button.maximumSize())
            move_bottom.setMaximumSize(down_button.maximumSize())
        except Exception:
            pass

        top_icon = _get_plugin_icon('images/top_move.png', plugin_name=PLUGIN_NAME)
        if top_icon is None or top_icon.isNull():
            top_icon = QIcon.ic('arrow-up.png')
        bottom_icon = _get_plugin_icon('images/bottom_move.png', plugin_name=PLUGIN_NAME)
        if bottom_icon is None or bottom_icon.isNull():
            bottom_icon = QIcon.ic('arrow-down.png')
        try:
            move_top.setIcon(top_icon)
        except Exception:
            pass
        try:
            move_bottom.setIcon(bottom_icon)
        except Exception:
            pass

        move_top.setToolTip(_('Move selected column to top'))
        move_bottom.setToolTip(_('Move selected column to bottom'))
        move_top.clicked.connect(lambda _checked=False, w=widget: _move_selected_column_to_top(w))
        move_bottom.clicked.connect(lambda _checked=False, w=widget: _move_selected_column_to_bottom(w))

        # Placement requirement:
        # - Move-to-top goes *below* the Up arrow
        # - Move-to-bottom goes *above* the Down arrow
        layout.insertWidget(up_index + 1, move_top)

        layout, _up_index, down_index = _find_common_button_layout(widget, up_button, down_button)
        if layout is None or down_index < 0:
            try:
                move_top.setParent(None)
                move_top.deleteLater()
            except Exception:
                pass
            try:
                move_bottom.setParent(None)
                move_bottom.deleteLater()
            except Exception:
                pass
            return
        layout.insertWidget(down_index, move_bottom)

        widget._cdf_move_top_button = move_top
        widget._cdf_move_bottom_button = move_bottom
        widget._cdf_move_top_bottom_installed = True

        try:
            _update_move_top_bottom_enabled(widget)
        except Exception:
            pass

    try:
        from calibre.constants import numeric_version
    except Exception:
        numeric_version = (0, 0, 0)

    supports_search_templates = tuple(numeric_version[:3]) >= (7, 26, 0)
    filter_column_order_key = 'columns_dialog_filter_column_order'
    filter_table_geometry_key = 'columns_dialog_filter_table_geometry'
    helper_group_definitions = build_helper_group_definitions(_)
    quick_create_presets = build_quick_create_presets(_)

    order_column = int(getattr(cols.ConfigWidget, 'ORDER_COLUMN', 0))
    header_column = int(getattr(cols.ConfigWidget, 'HEADER_COLUMN', 1))
    key_column = int(getattr(cols.ConfigWidget, 'KEY_COLUMN', 2))
    type_column = int(getattr(cols.ConfigWidget, 'TYPE_COLUMN', 3))
    description_column = int(getattr(cols.ConfigWidget, 'DESCRIPTION_COLUMN', 4))
    status_column = int(getattr(cols.ConfigWidget, 'STATUS_COLUMN', 5))
    base_column_count = len(getattr(cols.ConfigWidget, 'column_headings', ()) or ()) or (status_column + 1)

    field_aliases = {
        'name': header_column,
        'header': header_column,
        'lookup': key_column,
        'key': key_column,
        'type': type_column,
        'desc': description_column,
        'description': description_column,
        'status': status_column,
    }
    search_fields = {'search', 'search_template', 'websearch', 'web_search', 'web_search_template'}
    template_fields = {'template'}

    def focus_host_window(window):
        if window is None:
            return
        try:
            if window.isMinimized():
                window.showNormal()
        except Exception:
            pass
        try:
            window.raise_()
        except Exception:
            pass
        try:
            window.activateWindow()
        except Exception:
            pass

    def position_over_host(dialog, host):
        if dialog is None or host is None:
            return
        try:
            host_geom = host.frameGeometry()
            dialog_geom = dialog.frameGeometry()
            center = host_geom.center()
            dialog_geom.moveCenter(center)
            dialog.move(dialog_geom.topLeft())
        except Exception:
            pass

    def get_helper_group_definitions(*args, **kwargs):
        return list(helper_group_definitions)

    class PatchedCreateCustomColumn(original_create_custom_column):

        def exec(self, *args, **kwargs):
            caller = getattr(self, 'caller', None)
            host = getattr(caller, '_cdf_host_dialog', None) if _is_plugin_context(caller) else None
            if host is not None:
                try:
                    self.setParent(host, self.windowFlags())
                except Exception:
                    pass
                try:
                    self.setWindowModality(Qt.WindowModality.WindowModal)
                except Exception:
                    pass
                try:
                    self.finished.connect(lambda _result, host=host: QTimer.singleShot(0, lambda: focus_host_window(host)))
                except Exception:
                    pass
                QTimer.singleShot(0, lambda dialog=self: install_dialog_template_highlighters(dialog))
                QTimer.singleShot(125, lambda dialog=self: install_dialog_template_highlighters(dialog))
                QTimer.singleShot(0, lambda dialog=self, host=host: position_over_host(dialog, host))
                QTimer.singleShot(0, lambda host=host: focus_host_window(host))
            return original_create_custom_column.exec(self, *args, **kwargs)

    def copy_to_clipboard(text):
        if not text:
            return False
        app = QApplication.instance()
        if app is None:
            return False
        cb = app.clipboard()
        if cb is None:
            return False
        cb.setText(text)
        return True

    def _normalize_hint_text(text):
        return re.sub(r'\s+', ' ', str(text or '').replace('&', '')).strip().casefold()

    def _nearest_template_label(editor):
        try:
            parent = editor.parentWidget()
        except Exception:
            parent = None
        candidates = []
        if parent is not None:
            try:
                candidates.extend(parent.findChildren(QLabel))
            except Exception:
                pass

        best_label = ''
        best_score = None
        try:
            editor_geom = editor.geometry()
        except Exception:
            editor_geom = None
        for label in candidates:
            text = _normalize_hint_text(getattr(label, 'text', lambda: '')())
            if 'template' not in text and 'search' not in text and 'web' not in text:
                continue
            if editor_geom is None:
                return text
            try:
                label_geom = label.geometry()
            except Exception:
                return text
            if label_geom.bottom() > editor_geom.bottom():
                continue
            distance_y = abs(editor_geom.top() - label_geom.bottom())
            distance_x = abs(editor_geom.left() - label_geom.left())
            score = (distance_y * 4) + distance_x
            if best_score is None or score < best_score:
                best_score = score
                best_label = text
        return best_label

    def detect_template_editor_section(editor):
        hints = [
            _normalize_hint_text(getattr(editor, 'objectName', lambda: '')()),
            _normalize_hint_text(getattr(editor, 'toolTip', lambda: '')()),
            _normalize_hint_text(getattr(editor, 'placeholderText', lambda: '')()) if hasattr(editor, 'placeholderText') else '',
            _nearest_template_label(editor),
        ]
        combined = ' '.join(filter(None, hints))
        if 'web search' in combined or 'search template' in combined or 'web_search' in combined:
            return 'web_search_template'
        if 'composite' in combined or 'template' in combined:
            return 'composite_template'
        return None

    def install_dialog_template_highlighters(dialog):
        if dialog is None:
            return
        try:
            editors = dialog.findChildren(QPlainTextEdit)
        except Exception:
            editors = []
        for editor in editors:
            if getattr(editor, '_columns_helper_template_highlighter', None) is not None:
                continue
            section = detect_template_editor_section(editor)
            if section not in ('composite_template', 'web_search_template'):
                continue
            try:
                editor._columns_helper_template_section = section
                editor._columns_helper_template_highlighter = TemplateHighlighter(editor.document())
            except Exception:
                continue

    def row_template_values(self, row):
        table = getattr(self, 'opt_columns', None)
        if table is None or row < 0:
            return ('', '')
        key_item = table.item(row, key_column)
        key = str(key_item.text() if key_item is not None else '')
        cc = getattr(self, 'custcols', {}).get(key)
        if not cc:
            return ('', '')
        display = cc.get('display') or {}
        composite_template = str(display.get('composite_template') or '').strip()
        web_search_template = str(display.get('web_search_template') or '').strip()
        return (composite_template, web_search_template)

    def search_template_column_index(self):
        table = getattr(self, 'opt_columns', None)
        if table is None:
            return None

        def _is_search_header_text(text):
            normalized = str(text or '').strip().casefold()
            if not normalized:
                return False
            return normalized == str(_('Web search template') or '').strip().casefold() or normalized == 'web search template'

        def _find_search_columns():
            matches = []
            for col in range(table.columnCount()):
                header_item = table.horizontalHeaderItem(col)
                header_text = str(header_item.text() or '') if header_item is not None else ''
                if _is_search_header_text(header_text):
                    matches.append(col)
            return matches

        idx = getattr(self, '_cc_filter_search_template_column', None)
        idx_valid_range = idx is not None and idx >= base_column_count and idx < table.columnCount()
        if idx_valid_range:
            header_item = table.horizontalHeaderItem(idx)
            header_text = str(header_item.text() or '') if header_item is not None else ''
            if not _is_search_header_text(header_text):
                if COLUMNS_HELPER_DEBUG_ENABLED:
                    debug_print('[ColumnsHelper][DEBUG] search_template_column_index: cached index', idx, 'has non-search header=', repr(header_text), '; rescanning')
                idx_valid_range = False

        if not idx_valid_range:
            cols_found = _find_search_columns()
            if cols_found:
                idx = cols_found[-1]
                self._cc_filter_search_template_column = idx
                if COLUMNS_HELPER_DEBUG_ENABLED:
                    debug_print('[ColumnsHelper][DEBUG] search_template_column_index: recovered existing column(s)=', cols_found, 'using', idx)
            else:
                return None
        return idx

    def has_search_template_column(self):
        return search_template_column_index(self) is not None

    def default_filter_column_order(self):
        table = getattr(self, 'opt_columns', None)
        if table is None:
            return []
        order = list(range(table.columnCount()))
        search_col = search_template_column_index(self)
        if search_col is not None and search_col in order:
            order.remove(search_col)
            order.append(search_col)
        if order_column in order:
            order.remove(order_column)
            order.insert(0, order_column)
        return order

    def valid_visual_order(order, table):
        if not isinstance(order, (list, tuple)):
            return False
        count = table.columnCount()
        if len(order) != count:
            return False
        try:
            normalized = [int(x) for x in order]
        except Exception:
            return False
        return sorted(normalized) == list(range(count))

    def current_visual_order(table):
        header = table.horizontalHeader()
        order = []
        for visual_index in range(table.columnCount()):
            try:
                order.append(header.logicalIndex(visual_index))
            except Exception:
                return []
        return order

    def get_quick_create_presets(self, group):
        presets = quick_create_presets.get(group, {})
        return dict(presets)

    def select_row_for_lookup(self, lookup_name):
        table = getattr(self, 'opt_columns', None)
        if not _qt_object_is_alive(table):
            return False
        for row in range(table.rowCount()):
            item = table.item(row, order_column)
            key = '' if item is None else str(item.data(Qt.ItemDataRole.UserRole) or '')
            if key == lookup_name:
                target_col = header_column
                if target_col >= table.columnCount():
                    target_col = max(0, table.columnCount() - 1)
                try:
                    table.setCurrentCell(row, target_col)
                except Exception:
                    pass
                visible_item = table.item(row, target_col) or item
                if visible_item is not None:
                    try:
                        table.scrollToItem(visible_item)
                    except Exception:
                        pass
                return True
        return False

    def next_available_lookup_and_heading(self, lookup_name, heading):
        existing_keys = set(getattr(self, 'custcols', {}).keys())
        existing_headings = {str(cc.get('name') or '') for cc in getattr(self, 'custcols', {}).values()}
        model = getattr(self, 'model', None)
        if model is not None:
            try:
                existing_headings.update(str(v) for v in (model.orig_headers or {}).values())
            except Exception:
                pass

        key = lookup_name
        suffix = 1
        while key in existing_keys:
            key = '{0}_{1}'.format(lookup_name, suffix)
            suffix += 1

        heading_candidate = heading
        heading_suffix = 1
        while heading_candidate in existing_headings:
            heading_candidate = '{0} {1}'.format(heading, heading_suffix)
            heading_suffix += 1
        return key, heading_candidate

    def quick_create_pending_column(self, preset):
        table = getattr(self, 'opt_columns', None)
        if not _qt_object_is_alive(table):
            return None
        lookup_name = preset['lookup_name']
        if lookup_name in getattr(self, 'custcols', {}):
            select_row_for_lookup(self, lookup_name)
            return _('Already exists: {0}').format(lookup_name)

        lookup_name, heading = next_available_lookup_and_heading(self, lookup_name, preset['heading'])
        display = dict(preset.get('display') or {})
        cc = {
            'label': lookup_name[1:] if lookup_name.startswith('#') else lookup_name,
            'name': heading,
            'datatype': preset['datatype'],
            'display': display,
            'normalized': None,
            'colnum': None,
            'is_multiple': bool(preset.get('is_multiple', False)),
        }
        self.custcols[lookup_name] = cc
        self.set_new_custom_column(cc)
        cc['original_key'] = lookup_name

        row = table.rowCount()
        table.setRowCount(row + 1)
        self.setup_row(row, lookup_name, row)
        update_search_template_cell(self, row)
        refresh_filter(self)
        select_row_for_lookup(self, lookup_name)
        self.changed_signal.emit()
        return _('Created: {0}').format(lookup_name)

    def quick_create_columns(self, group, keys):
        if not _qt_object_is_alive(self) or not _qt_object_is_alive(getattr(self, 'opt_columns', None)):
            return [_('The columns window was closed. Reopen Columns Helper and try again.')]
        presets = get_quick_create_presets(self, group)
        messages = []
        for key in keys:
            preset = presets.get(key)
            if preset is None:
                continue
            msg = quick_create_pending_column(self, preset)
            if msg:
                messages.append(msg)
        refresh_filter(self)
        return messages

    def restore_filter_column_state(self):
        table = getattr(self, 'opt_columns', None)
        if table is None or not has_search_template_column(self):
            return
        if getattr(self, '_cc_filter_restoring_layout', False):
            return

        self._cc_filter_restoring_layout = True
        try:
            header = table.horizontalHeader()
            try:
                original_sorting = table.isSortingEnabled()
            except Exception:
                original_sorting = False
            try:
                table.setSortingEnabled(False)
            except Exception:
                pass
            try:
                table.blockSignals(True)
                if header is not None:
                    header.blockSignals(True)
            except Exception:
                pass
            desired_order = gprefs.get(filter_column_order_key, None)
            if not valid_visual_order(desired_order, table):
                desired_order = default_filter_column_order(self)

            for desired_visual_index, logical_index in enumerate(desired_order):
                current_visual_index = header.visualIndex(logical_index)
                if current_visual_index != desired_visual_index and current_visual_index >= 0:
                    header.moveSection(current_visual_index, desired_visual_index)

            widths = gprefs.get(filter_table_geometry_key, None)
            if isinstance(widths, (list, tuple)) and widths:
                for i, width in enumerate(widths):
                    if i >= table.columnCount():
                        break
                    try:
                        width_int = int(width)
                        if width_int > 0:
                            table.setColumnWidth(i, width_int)
                    except Exception:
                        pass
            else:
                search_col = search_template_column_index(self)
                if search_col is not None:
                    try:
                        table.setColumnWidth(search_col, max(table.columnWidth(search_col), 220))
                    except Exception:
                        pass

            self.column_positions = list(desired_order)
        finally:
            try:
                table.setSortingEnabled(original_sorting)
            except Exception:
                pass
            try:
                table.blockSignals(False)
                if header is not None:
                    header.blockSignals(False)
            except Exception:
                pass
            self._cc_filter_restoring_layout = False

    def save_filter_column_state(self):
        table = getattr(self, 'opt_columns', None)
        if table is None or not has_search_template_column(self):
            return
        order = current_visual_order(table)
        if valid_visual_order(order, table):
            gprefs.set(filter_column_order_key, list(order))
            self.column_positions = list(order)
        widths = []
        for i in range(table.columnCount()):
            try:
                widths.append(int(table.columnWidth(i)))
            except Exception:
                widths.append(0)
        gprefs.set(filter_table_geometry_key, widths)
        try:
            gprefs.save()
        except Exception:
            pass

    def ensure_search_template_column(self):
        if not supports_search_templates:
            return

        # Restrict search template column to modeless dialog only
        if not getattr(self, '_cdf_restrict_search_template_to_modeless', False):
            return

        table = getattr(self, 'opt_columns', None)
        if table is None:
            return
        if table.columnCount() < base_column_count:
            return

        def _is_search_header_text(text):
            normalized = str(text or '').strip().casefold()
            if not normalized:
                return False
            return normalized == str(_('Web search template') or '').strip().casefold() or normalized == 'web search template'

        def _find_search_columns():
            matches = []
            for col in range(table.columnCount()):
                header_item = table.horizontalHeaderItem(col)
                header_text = str(header_item.text() or '') if header_item is not None else ''
                if _is_search_header_text(header_text):
                    matches.append(col)
            return matches

        search_col = search_template_column_index(self)

        if search_col is None:
            cols_found = _find_search_columns()
            if cols_found:
                search_col = cols_found[-1]
                self._cc_filter_search_template_column = search_col
                if COLUMNS_HELPER_DEBUG_ENABLED:
                    debug_print('[ColumnsHelper][DEBUG] ensure_search_template_column: reusing existing search column(s)=', cols_found, 'selected', search_col)

        # If duplicates exist, keep the newest one and remove older duplicates.
        cols_found = _find_search_columns()
        if len(cols_found) > 1:
            keep_col = cols_found[-1]
            for dup_col in reversed(cols_found[:-1]):
                try:
                    table.removeColumn(dup_col)
                    if keep_col > dup_col:
                        keep_col -= 1
                except Exception as err:
                    if COLUMNS_HELPER_DEBUG_ENABLED:
                        debug_print('[ColumnsHelper][DEBUG] ensure_search_template_column: failed removing duplicate column', dup_col, repr(err))
            search_col = keep_col
            self._cc_filter_search_template_column = search_col
            if COLUMNS_HELPER_DEBUG_ENABLED:
                debug_print('[ColumnsHelper][DEBUG] ensure_search_template_column: removed duplicates, now using column', search_col)

        if search_col is None:
            search_col = table.columnCount()
            table.setColumnCount(search_col + 1)
            self._cc_filter_search_template_column = search_col
            if COLUMNS_HELPER_DEBUG_ENABLED:
                debug_print('[ColumnsHelper][DEBUG] ensure_search_template_column: inserted new column at', search_col)

        header_item = table.horizontalHeaderItem(search_col)
        if header_item is None or str(header_item.text() or '') != _('Web search template'):
            header_item = QTableWidgetItem(_('Web search template'))
            try:
                font = header_item.font()
                font.setBold(True)
                header_item.setFont(font)
            except Exception:
                pass
            table.setHorizontalHeaderItem(search_col, header_item)

        for row in range(table.rowCount()):
            update_search_template_cell(self, row)

        restore_filter_column_state(self)

    def update_search_template_cell(self, row):
        if not supports_search_templates:
            return
        table = getattr(self, 'opt_columns', None)
        search_col = search_template_column_index(self)
        if table is None or search_col is None or row < 0 or row >= table.rowCount():
            return

        _composite_template, search_template = row_template_values(self, row)
        item = table.item(row, search_col)
        if item is None:
            item = QTableWidgetItem()
            flags_source = table.item(row, status_column) or table.item(row, key_column)
            if flags_source is not None:
                item.setFlags(flags_source.flags())
            table.setItem(row, search_col, item)
        item.setText(search_template)
        item.setToolTip(search_template)

    def show_columns_context_menu(self, pos):
        table = getattr(self, 'opt_columns', None)
        if table is None:
            return
        item = table.itemAt(pos)
        index = table.indexAt(pos)
        if item is None and (index is None or not index.isValid()):
            return
        row = item.row() if item is not None else index.row()
        current_col = table.currentColumn()
        if current_col < 0:
            current_col = index.column() if index is not None and index.isValid() else header_column
        try:
            table.setCurrentCell(row, current_col)
        except Exception:
            pass
        composite_template, search_template = row_template_values(self, row)
        lookup_item = table.item(row, key_column)
        lookup_name = str(lookup_item.text() if lookup_item is not None else '').strip()
        is_custom_lookup = lookup_name.startswith('#')
        menu = QMenu(table)

        def add_copy_action(text, payload, copied_message):
            action = menu.addAction(text)
            action.setEnabled(bool(payload))

            def do_copy():
                if copy_to_clipboard(payload):
                    status = getattr(self, '_cc_filter_status', None)
                    if status is not None:
                        status.setText(copied_message)
                        QTimer.singleShot(1500, lambda: apply_filter(self))

            action.triggered.connect(do_copy)
            return action

        add_copy_action(_('Copy template to clipboard'), composite_template, _('Template copied'))
        add_copy_action(_('Copy web search template to clipboard'), search_template, _('Web search template copied'))

        if is_custom_lookup:
            ccr_iaction = None
            try:
                ccr_iaction = getattr(getattr(self, 'gui', None), 'iactions', {}).get('Calibre Config Reports')
            except Exception:
                ccr_iaction = None

            integration_icon = _get_plugin_icon('images/CCR_call.png', plugin_name=PLUGIN_NAME)
            if integration_icon is not None and not integration_icon.isNull():
                integration_action = menu.addAction(integration_icon, _('Open in Calibre Config Reports'))
            else:
                integration_action = menu.addAction(_('Open in Calibre Config Reports'))
            integration_action.setEnabled(bool(ccr_iaction and lookup_name))
            if ccr_iaction is None:
                integration_action.setToolTip(_('Calibre Config Reports is not installed.'))
            elif not lookup_name:
                integration_action.setToolTip(_('This row does not have a lookup name.'))
            else:
                def ccr_jump_and_force_filter(_checked=False, ia=ccr_iaction, name=lookup_name):
                    # Call CCR jump
                    if COLUMNS_HELPER_DEBUG_ENABLED:
                        try:
                            debug_print('[COLUMNS_HELPER][DEBUG] ccr_jump_and_force_filter: invoked at', time.time(), 'name=', name)
                        except Exception:
                            pass
                    if hasattr(ia, 'open_to_custom_column_lookup'):
                        try:
                            if COLUMNS_HELPER_DEBUG_ENABLED:
                                debug_print('[COLUMNS_HELPER][DEBUG] calling ia.open_to_custom_column_lookup', time.time(), name)
                        except Exception:
                            pass
                        ia.open_to_custom_column_lookup(name)

                    # Attempt to detect CCR dialog and, if open, emulate a short user edit
                    try:
                        from qt.core import QTimer, QKeyEvent, QEvent, Qt
                    except Exception:
                        try:
                            from PyQt5.QtCore import QTimer, QEvent, Qt
                            from PyQt5.QtGui import QKeyEvent
                        except Exception:
                            QTimer = None

                    def do_emulate():
                        ccr_dialog = None
                        try:
                            ccr_dialog = getattr(ia, 'dialog', None) or getattr(ia, 'parent', None)
                        except Exception:
                            ccr_dialog = None
                        if not ccr_dialog:
                            # Fallback: scan top-level widgets for CCR dialog
                            try:
                                app = QApplication.instance()
                                if app is not None:
                                    for w in app.topLevelWidgets():
                                        if w.__class__.__name__ == 'PluginCatalogDialog' or w.__class__.__name__ == 'PluginCatalogDialog':
                                            ccr_dialog = w
                                            break
                            except Exception:
                                pass

                        if not ccr_dialog:
                            return

                        # Try several likely attribute names used by CCR
                        filter_combo = getattr(ccr_dialog, 'columns_filter_combo', None) or getattr(ccr_dialog, '_columns_filter_combo', None)
                        # line edit could be combo.lineEdit()
                        filter_edit = None
                        try:
                            if filter_combo is not None:
                                try:
                                    filter_edit = filter_combo.lineEdit()
                                except Exception:
                                    filter_edit = getattr(ccr_dialog, 'columns_filter_edit', None) or getattr(ccr_dialog, '_columns_filter_edit', None)
                            else:
                                filter_edit = getattr(ccr_dialog, 'columns_filter_edit', None) or getattr(ccr_dialog, '_columns_filter_edit', None)
                        except Exception:
                            filter_edit = getattr(ccr_dialog, 'columns_filter_edit', None) or getattr(ccr_dialog, '_columns_filter_edit', None)

                        columns_table = getattr(ccr_dialog, 'columns_table', None) or getattr(ccr_dialog, '_columns_table', None)
                        filter_method = getattr(ccr_dialog, '_apply_columns_lookup_filter', None) or getattr(ccr_dialog, 'apply_columns_filter', None)

                        try:
                            text = ''
                            if filter_edit is not None:
                                text = filter_edit.text()
                            elif filter_combo is not None and hasattr(filter_combo, 'currentText'):
                                text = filter_combo.currentText()
                        except Exception:
                            text = ''

                        if filter_edit is None and filter_combo is None and not callable(filter_method):
                            return

                        # If there's no text, still attempt to call filter method
                        if not text and not callable(filter_method):
                            return

                        last_char = text[-1] if text else ''
                        try:
                            # Key press backspace
                            ev = QKeyEvent(QEvent.KeyPress, Qt.Key_Backspace, Qt.NoModifier)
                            filter_edit.keyPressEvent(ev)
                            ev = QKeyEvent(QEvent.KeyRelease, Qt.Key_Backspace, Qt.NoModifier)
                            filter_edit.keyReleaseEvent(ev)
                            # Retype last character (text-aware event)
                            kc = ord(last_char) if last_char else 0
                            ev = QKeyEvent(QEvent.KeyPress, kc, Qt.NoModifier, last_char)
                            filter_edit.keyPressEvent(ev)
                            ev = QKeyEvent(QEvent.KeyRelease, kc, Qt.NoModifier, last_char)
                            filter_edit.keyReleaseEvent(ev)
                        except Exception:
                            # Fallback: select all and reinsert text to trigger edit signals
                            try:
                                if filter_edit is not None:
                                    filter_edit.selectAll()
                                    filter_edit.insert(text)
                                elif filter_combo is not None and hasattr(filter_combo, 'setEditText'):
                                    filter_combo.setEditText(text)
                            except Exception:
                                pass

                        # Ensure CCR filter method is invoked (best effort)
                        if callable(filter_method):
                            try:
                                # If method expects the lookup, pass it, else call no-arg
                                try:
                                    filter_method()
                                except TypeError:
                                    try:
                                        filter_method(text)
                                    except Exception:
                                        filter_method()
                            except Exception:
                                pass

                        # Replace aggressive UI forcing with debug traces.
                        if COLUMNS_HELPER_DEBUG_ENABLED:
                            try:
                                debug_print('[COLUMNS_HELPER][DEBUG] do_emulate: called at', time.time(), 'lookup=', text)
                                if columns_table is not None:
                                    try:
                                        m = columns_table.model()
                                        rcount = m.rowCount() if hasattr(m, 'rowCount') else 'n/a'
                                        ccount = m.columnCount() if hasattr(m, 'columnCount') else 'n/a'
                                        debug_print('[COLUMNS_HELPER][DEBUG] columns_table model rows=', rcount, 'cols=', ccount)
                                    except Exception:
                                        debug_print('[COLUMNS_HELPER][DEBUG] columns_table model introspect failed')
                            except Exception:
                                pass

                    # Schedule the emulate to run immediately and as a short safety-net
                    try:
                        if COLUMNS_HELPER_DEBUG_ENABLED:
                            try:
                                debug_print('[COLUMNS_HELPER][DEBUG] scheduling do_emulate immediate at', time.time())
                            except Exception:
                                pass
                        if QTimer is not None:
                            # Immediate attempt (helps when CCR is already open)
                            QTimer.singleShot(0, do_emulate)
                            # Safety-net delayed attempt
                            QTimer.singleShot(80, do_emulate)
                        else:
                            do_emulate()
                    except Exception:
                        try:
                            do_emulate()
                        except Exception:
                            pass

                integration_action.triggered.connect(ccr_jump_and_force_filter)
        menu.exec(table.viewport().mapToGlobal(pos))

    def ensure_context_menu(self):
        if not _is_plugin_context(self):
            return
        table = getattr(self, 'opt_columns', None)
        if table is None or getattr(self, '_cc_filter_context_menu_installed', False):
            return
        try:
            table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        except Exception:
            table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda pos: show_columns_context_menu(self, pos))
        self._cc_filter_context_menu_installed = True

    def _read_filter_history():
        try:
            hist = gprefs.get('columns_helper_filter_history', [])
        except Exception:
            hist = []
        if not isinstance(hist, list):
            hist = []
        out = []
        for entry in hist:
            text = str(entry or '').strip()
            if text:
                out.append(text)
        return out[:50]

    def _write_filter_history(hist):
        cleaned = []
        for entry in (hist or []):
            text = str(entry or '').strip()
            if text:
                cleaned.append(text)
        cleaned = cleaned[:50]
        wrote = False
        try:
            gprefs['columns_helper_filter_history'] = cleaned
            wrote = True
        except Exception:
            pass
        if not wrote:
            try:
                gprefs.set('columns_helper_filter_history', cleaned)
                wrote = True
            except Exception:
                pass
        if wrote:
            try:
                gprefs.save()
            except Exception:
                pass

    def ensure_filter_ui(self):
        # Restrict filter box to modeless dialog only
        if not getattr(self, '_cdf_restrict_search_template_to_modeless', False):
            return

        if getattr(self, '_cc_filter_bar', None) is not None:
            return
        table = getattr(self, 'opt_columns', None)
        if table is None:
            return

        container = QWidget(self)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)

        bar = QWidget(container)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(6)

        label = QLabel(_('Filter:'), bar)
        bar_layout.addWidget(label)

        edit = QComboBox(bar)
        edit.setEditable(True)
        edit.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        edit.setStyleSheet(_ccr_combo_stylesheet())
        edit.lineEdit().setPlaceholderText(_('Search columns…  Examples: not desc:date  type:text  not hidden:yes'))
        edit.setToolTip(_(
            'Filter rows in the custom columns dialog.\n\n'
            'Examples:\n'
            '  pages            match anywhere in the row\n'
            '  lookup:#status   match lookup name\n'
            '  type:text        match type\n'
            '  desc:progress    match description\n'
            '  websearch:phind  match web search template\n'
            '  status:edited    match status\n'
            '  hidden:yes       only hidden columns\n'
            '  custom:yes       only custom columns\n'
            '  -text            exclude matches\n'
            '  not desc:date    exclude description contains date\n'
            'Use quotes for phrases. Press Ctrl+F to focus this box.'
        ))
        edit.setMaxCount(51)  # 50 history + 1 sentinel
        edit.lineEdit().setClearButtonEnabled(True)
        bar_layout.addWidget(edit, 1)

        _CLEAR_HISTORY_SENTINEL = '__columns_helper_clear_history__'
        _CLEAR_HISTORY_LABEL = _('Clear history')
        edit._ch_clear_history_sentinel = _CLEAR_HISTORY_SENTINEL
        edit._ch_clear_history_label = _CLEAR_HISTORY_LABEL
        edit._ch_is_clearing_history = False

        def refresh_history_dropdown(keep_text=''):
            """Rebuild the dropdown: history items + separator + italic Clear history"""
            combo = edit
            combo.blockSignals(True)
            combo.clear()
            history = _read_filter_history()
            for entry in history:
                combo.addItem(entry)
            if combo.count() > 0:
                try:
                    combo.insertSeparator(combo.count())
                except Exception:
                    pass
            combo.addItem(_CLEAR_HISTORY_LABEL, _CLEAR_HISTORY_SENTINEL)
            try:
                model = combo.model()
                item = model.item(combo.count() - 1)
                if item is not None:
                    f = item.font()
                    f.setItalic(True)
                    item.setFont(f)
            except Exception:
                pass
            combo.setEditText(keep_text)
            combo.blockSignals(False)

        def on_history_activated(index):
            try:
                if edit.itemData(index) == _CLEAR_HISTORY_SENTINEL:
                    edit._ch_is_clearing_history = True
                    try:
                        _write_filter_history([])
                        line_edit = edit.lineEdit()
                        if line_edit is not None:
                            line_edit.clear()
                        refresh_history_dropdown('')
                        try:
                            edit.setCurrentIndex(-1)
                        except Exception:
                            pass
                        apply_filter(self)
                    finally:
                        edit._ch_is_clearing_history = False
                    return
            except Exception:
                pass
            try:
                text = edit.itemText(index)
                if text and text != _CLEAR_HISTORY_LABEL:
                    edit.setEditText(text)
                    try:
                        save_filter_history(self, text)
                    except Exception:
                        pass
                    line_edit = edit.lineEdit()
                    if line_edit is not None:
                        line_edit.setFocus()
                        line_edit.end(False)
            except Exception:
                pass

        edit.activated.connect(on_history_activated)
        refresh_history_dropdown()

        status = QLabel('', bar)
        try:
            status.setStyleSheet('color: gray; font-style: italic;')
        except Exception:
            pass
        bar_layout.addWidget(status)

        inserted = False
        grid = getattr(self, 'gridLayout', None)
        if grid is not None:
            try:
                grid.removeWidget(table)
                container_layout.addWidget(bar)
                container_layout.addWidget(table)
                grid.addWidget(container, 1, 0, 1, 1)
                inserted = True
            except Exception:
                inserted = False

        if not inserted:
            try:
                parent = table.parentWidget()
                layout = parent.layout() if parent is not None else None
                if layout is not None and hasattr(layout, 'insertWidget'):
                    idx = layout.indexOf(table)
                    layout.removeWidget(table)
                    container_layout.addWidget(bar)
                    container_layout.addWidget(table)
                    layout.insertWidget(max(0, idx), container)
                    inserted = True
            except Exception:
                inserted = False

        if not inserted:
            return

        def focus_filter():
            edit.setFocus(Qt.FocusReason.ShortcutFocusReason)
            le = edit.lineEdit()
            if le is not None:
                le.selectAll()

        def escape_filter():
            le = edit.lineEdit()
            current_text = (le.text() if le is not None else '') or ''
            if bool(getattr(self, '_cdf_in_modeless_host', False)):
                host_dialog = getattr(self, '_cdf_host_dialog', None)
                if host_dialog is not None:
                    host_dialog.reject()
            elif current_text.strip():
                if le is not None:
                    le.clear()
            else:
                table.setFocus(Qt.FocusReason.ShortcutFocusReason)

        try:
            find_key = QKeySequence.StandardKey.Find
        except Exception:
            find_key = QKeySequence('Ctrl+F')
        focus_shortcut = QShortcut(find_key, self)
        focus_shortcut.activated.connect(focus_filter)
        escape_shortcut = QShortcut(QKeySequence('Esc'), edit)
        escape_shortcut.activated.connect(escape_filter)

        self._cc_filter_container = container
        self._cc_filter_bar = bar
        self._cc_filter_edit = edit
        self._cc_filter_status = status
        self._cc_filter_focus_shortcut = focus_shortcut
        self._cc_filter_escape_shortcut = escape_shortcut
        edit._ch_refresh_history = refresh_history_dropdown
        self._cc_filter_save_layout = lambda : save_filter_column_state(self)
        self._cc_filter_restore_layout = lambda : restore_filter_column_state(self)

        if not getattr(self, '_cc_filter_item_changed_connected', False):
            table.itemChanged.connect(lambda *_args: apply_filter(self))
            self._cc_filter_item_changed_connected = True

        # Connect combobox line edit for filter changes
        edit.lineEdit().textChanged.connect(lambda _text: apply_filter(self))

        # Save history only when the user commits the text (prevents spaces being stripped while typing)
        def commit_filter_history():
            try:
                le = edit.lineEdit()
                if le is None:
                    return
                current = le.text() or ''
                if current.strip():
                    save_filter_history(self, current)
            except Exception:
                pass

        try:
            edit.lineEdit().editingFinished.connect(commit_filter_history)
        except Exception:
            pass
        try:
            edit.lineEdit().returnPressed.connect(commit_filter_history)
        except Exception:
            pass

        # Save final table layout using the existing filter-column persistence path.
        # This runs after the Search template column exists, so widths/order line up.
        header = table.horizontalHeader()
        if header is not None:
            try:
                if not getattr(self, '_cc_filter_header_resize_connected', False):
                    header.sectionResized.connect(lambda *args: save_filter_column_state(self))
                    self._cc_filter_header_resize_connected = True
            except Exception:
                pass
            try:
                if not getattr(self, '_cc_filter_header_move_connected', False) and hasattr(header, 'sectionMoved'):
                    header.sectionMoved.connect(lambda *args: save_filter_column_state(self))
                    self._cc_filter_header_move_connected = True
            except Exception:
                pass

    def save_filter_history(widget, filter_text):
        """Save filter text to history in gprefs"""
        try:
            raw_text = filter_text if filter_text is not None else ''
            text = raw_text.strip()
            if not text:
                return
            combo = getattr(widget, '_cc_filter_edit', None)
            if combo is not None and isinstance(combo, QComboBox):
                if bool(getattr(combo, '_ch_is_clearing_history', False)):
                    return
                clear_label = getattr(combo, '_ch_clear_history_label', '')
                if text == clear_label:
                    return

            # Get existing history
            history = _read_filter_history()

            # Remove if already exists and add to front
            if text in history:
                history.remove(text)
            history.insert(0, text)

            # Keep only last 50 entries
            history = history[:50]

            _write_filter_history(history)

            # Update combobox if it exists — just call refresh_history_dropdown
            # via the sentinel refresh function stored on the widget
            if combo is not None and isinstance(combo, QComboBox):
                refresh_fn = getattr(combo, '_ch_refresh_history', None)
                if refresh_fn is not None:
                    try:
                        # Keep whatever the user typed (including spaces) in the edit box.
                        refresh_fn(keep_text=raw_text)
                    except Exception:
                        pass
        except Exception:
            pass

    def parse_terms(raw_text):
        clauses = []
        tokens = list(_split_filter_text(raw_text))
        i = 0
        while i < len(tokens):
            token = tokens[i]
            i += 1

            # Check for 'not' keyword (CCR-style)
            negative = False
            if token.lower() == 'not':
                negative = True
                if i >= len(tokens):
                    break
                token = tokens[i]
                i += 1
            elif token.startswith('-'):
                negative = True
                token = token[1:]

            token = token.strip()
            if not token:
                continue

            field = None
            value = token
            if ':' in token:
                maybe_field, maybe_value = token.split(':', 1)
                maybe_field = maybe_field.strip().casefold()
                supported_fields = {'hidden', 'visible', 'custom', 'builtin'}
                supported_fields.update(search_fields)
                supported_fields.update(template_fields)
                if maybe_field in field_aliases or maybe_field in supported_fields:
                    field = maybe_field
                    value = maybe_value.strip()
            value = value.casefold()
            if value:
                clauses.append((negative, field, value))
        return clauses

    def row_value_for_field(self, row, field):
        table = self.opt_columns
        if field in field_aliases:
            item = table.item(row, field_aliases[field])
            return str(item.text() if item is not None else '').casefold()

        order_item = table.item(row, order_column)
        key_item = table.item(row, key_column)
        key_text = str(key_item.text() if key_item is not None else '')
        is_custom = key_text.startswith('#')
        state = order_item.checkState() if order_item is not None else Qt.CheckState.Unchecked
        is_hidden = state == Qt.CheckState.Unchecked

        if field == 'hidden':
            return 'yes' if is_hidden else 'no'
        if field == 'visible':
            return 'no' if is_hidden else 'yes'
        if field == 'custom':
            return 'yes' if is_custom else 'no'
        if field == 'builtin':
            return 'no' if is_custom else 'yes'
        if field in search_fields:
            _composite_template, search_template = row_template_values(self, row)
            return search_template.casefold()
        if field in template_fields:
            composite_template, _search_template = row_template_values(self, row)
            return composite_template.casefold()

        texts = []
        for col in (
            header_column,
            key_column,
            type_column,
            description_column,
            status_column,
        ):
            item = table.item(row, col)
            if item is not None:
                texts.append(str(item.text()))
        composite_template, search_template = row_template_values(self, row)
        if composite_template:
            texts.append(composite_template)
        if search_template:
            texts.append(search_template)
        texts.append(_('custom') if is_custom else _('builtin'))
        texts.append(_('hidden') if is_hidden else _('visible'))
        return ' '.join(texts).casefold()

    def row_matches(self, row, clauses):
        if not clauses:
            return True
        for negative, field, value in clauses:
            haystack = row_value_for_field(self, row, field)
            matched = value in haystack
            if negative:
                if matched:
                    return False
            elif not matched:
                return False
        return True

    def apply_filter(self):
        table = getattr(self, 'opt_columns', None)
        edit = getattr(self, '_cc_filter_edit', None)
        status = getattr(self, '_cc_filter_status', None)
        if table is None or edit is None or status is None:
            return
        if getattr(self, '_cc_filter_in_apply', False):
            return

        self._cc_filter_in_apply = True
        try:
            # Handle both QComboBox and QLineEdit
            if isinstance(edit, QComboBox):
                filter_text = edit.lineEdit().text()
            else:
                filter_text = edit.text()

            clauses = parse_terms(filter_text)
            total = table.rowCount()
            visible = 0
            first_visible_row = -1

            for row in range(total):
                matched = row_matches(self, row, clauses)
                table.setRowHidden(row, not matched)
                if matched:
                    visible += 1
                    if first_visible_row < 0:
                        first_visible_row = row

            if clauses:
                status.setText(_('%d of %d') % (visible, total))
            else:
                status.setText(_('%d columns') % total)

            current_row = table.currentRow()
            if first_visible_row >= 0 and (current_row < 0 or table.isRowHidden(current_row)):
                target_col = header_column
                if table.columnCount() > 0:
                    target_col = max(0, min(target_col, table.columnCount() - 1))
                    table.setCurrentCell(first_visible_row, target_col)
                    item = table.item(first_visible_row, target_col) or table.item(first_visible_row, 0)
                    if item is not None:
                        table.scrollToItem(item)
        finally:
            self._cc_filter_in_apply = False

    def refresh_filter(self):
        if not _is_plugin_context(self):
            return
        try:
            ensure_filter_ui(self)
            ensure_search_template_column(self)
            ensure_context_menu(self)
            apply_filter(self)
        except Exception:
            pass

    def patched_genesis(self, gui):
        return original_genesis(self, gui)

    def patched_init_columns(self, defaults=False):
        if not _is_plugin_context(self):
            return original_init_columns(self, defaults=defaults)
        if COLUMNS_HELPER_DEBUG_ENABLED:
            try:
                table = getattr(self, 'opt_columns', None)
                before_count = table.columnCount() if table is not None else -1
            except Exception:
                before_count = -1
            debug_print('[ColumnsHelper][DEBUG] patched_init_columns: begin defaults=', defaults, 'existing columnCount=', before_count)
        self._cc_filter_search_template_column = None
        ans = original_init_columns(self, defaults=defaults)
        if COLUMNS_HELPER_DEBUG_ENABLED:
            try:
                table = getattr(self, 'opt_columns', None)
                after_count = table.columnCount() if table is not None else -1
            except Exception:
                after_count = -1
            debug_print('[ColumnsHelper][DEBUG] patched_init_columns: after original init columnCount=', after_count)
        refresh_filter(self)
        try:
            _ensure_move_top_bottom_buttons(self)
        except Exception:
            pass
        return ans

    def patched_header_moved(self, log_index, old_v_index, new_v_index):
        if not _is_plugin_context(self):
            if callable(original_header_moved):
                return original_header_moved(self, log_index, old_v_index, new_v_index)
            return None
        if has_search_template_column(self):
            save_filter_column_state(self)
            return
        if callable(original_header_moved):
            return original_header_moved(self, log_index, old_v_index, new_v_index)

    def patched_save_geometry(self, *args, **kwargs):
        if not _is_plugin_context(self):
            if callable(original_save_geometry):
                return original_save_geometry(self, *args, **kwargs)
            return None
        if has_search_template_column(self):
            save_filter_column_state(self)
            return
        if callable(original_save_geometry):
            return original_save_geometry(self, *args, **kwargs)

    def patched_restore_geometry(self, *args, **kwargs):
        if not _is_plugin_context(self):
            if callable(original_restore_geometry):
                return original_restore_geometry(self, *args, **kwargs)
            return None
        ans = original_restore_geometry(self, *args, **kwargs) if callable(original_restore_geometry) else None
        if has_search_template_column(self):
            try:
                restore_filter_column_state(self)
            except Exception:
                pass
        return ans

    def patched_set_up_down_enabled(self, *args, **kwargs):
        """Guard against NoneType from currentItem() when double-clicking to edit"""
        if not _is_plugin_context(self):
            return original_set_up_down_enabled(self, *args, **kwargs)
        try:
            try:
                _ensure_move_top_bottom_buttons(self)
            except Exception:
                pass

            item = self.opt_columns.currentItem()
            if item is None:
                up_button = getattr(self, 'up_button', None) or getattr(self, 'column_up', None)
                down_button = getattr(self, 'down_button', None) or getattr(self, 'column_down', None)
                if up_button is not None:
                    up_button.setEnabled(False)
                if down_button is not None:
                    down_button.setEnabled(False)
                top_button = getattr(self, '_cdf_move_top_button', None)
                bottom_button = getattr(self, '_cdf_move_bottom_button', None)
                if top_button is not None:
                    top_button.setEnabled(False)
                if bottom_button is not None:
                    bottom_button.setEnabled(False)
                return
            ans = original_set_up_down_enabled(self, *args, **kwargs)
            try:
                _update_move_top_bottom_enabled(self)
            except Exception:
                pass
            return ans
        except Exception:
            return original_set_up_down_enabled(self, *args, **kwargs)

    def wrap_and_refresh(original):
        def wrapped(self, *args, **kwargs):
            try:
                ans = original(self, *args, **kwargs)
            except TypeError:
                # Avoid duplicate values for named parameters (e.g. use_kbd_modifiers)
                try:
                    import inspect
                    sig = inspect.signature(original)
                    param_names = list(sig.parameters.keys())[1:]
                    # Build new positional args skipping any that have been provided via kwargs
                    new_pos = []
                    arg_iter = iter(args)
                    for name in param_names:
                        try:
                            val = next(arg_iter)
                        except StopIteration:
                            break
                        if name in kwargs:
                            continue
                        new_pos.append(val)
                    ans = original(self, *new_pos, **kwargs)
                except Exception:
                    # Fallback to original call which will re-raise if still failing
                    ans = original(self, *args, **kwargs)
            try:
                refresh_filter(self)
            except Exception:
                pass
            return ans
        return wrapped

    def wrap_zero_arg_and_refresh(original):
        def wrapped(self, *args, **kwargs):
            # Signals such as clicked(bool) pass extra args these methods don't accept
            ans = original(self)
            if _is_plugin_context(self):
                refresh_filter(self)
            return ans
        return wrapped

    cols.ConfigWidget.__init__ = patched_init
    cols.ConfigWidget.genesis = patched_genesis
    cols.ConfigWidget.init_columns = patched_init_columns
    if callable(original_header_moved):
        cols.ConfigWidget.header_moved = patched_header_moved
    cols.ConfigWidget.save_geometry = patched_save_geometry
    if callable(original_restore_geometry):
        cols.ConfigWidget.restore_geometry = patched_restore_geometry
    cols.ConfigWidget.set_up_down_enabled = patched_set_up_down_enabled
    cols.ConfigWidget._cdf_refresh_filter = refresh_filter
    cols.ConfigWidget._cdf_get_quick_create_presets = get_quick_create_presets
    cols.ConfigWidget._cdf_get_helper_group_definitions = get_helper_group_definitions
    cols.ConfigWidget._cdf_quick_create_columns = quick_create_columns
    cols.ConfigWidget.add_custcol = wrap_zero_arg_and_refresh(original_add_custcol)
    cols.ConfigWidget.edit_custcol = wrap_zero_arg_and_refresh(original_edit_custcol)
    cols.ConfigWidget.del_custcol = wrap_zero_arg_and_refresh(original_del_custcol)
    if callable(original_show_all):
        cols.ConfigWidget.show_all = wrap_zero_arg_and_refresh(original_show_all)
    if callable(original_hide_all):
        cols.ConfigWidget.hide_all = wrap_zero_arg_and_refresh(original_hide_all)
    cols.ConfigWidget.restore_defaults = wrap_zero_arg_and_refresh(original_restore_defaults)
    cols.ConfigWidget.table_sorted = wrap_and_refresh(original_table_sorted)
    cols.ConfigWidget.up_column = wrap_and_refresh(original_up_column)
    cols.ConfigWidget.down_column = wrap_and_refresh(original_down_column)
    cols.CreateCustomColumn = PatchedCreateCustomColumn
    cols._columns_dialog_filter_patch_installed = True
    return True


class ColumnsHelperAction(InterfaceAction):
    name = PLUGIN_NAME
    action_spec = (
        _(PLUGIN_NAME),
        None,
        _('Preview, create, and manage custom columns and column packs'),
        None
    )
    action_add_menu = True

    try:
        if QToolButton is not None and hasattr(QToolButton, 'ToolButtonPopupMode'):
            popup_type = QToolButton.ToolButtonPopupMode.MenuButtonPopup
        elif QToolButton is not None and hasattr(QToolButton, 'MenuButtonPopup'):
            popup_type = QToolButton.MenuButtonPopup
    except Exception:
        pass

    def rebuild_icon(self):
        icon_path = 'images/iconplugin_dark.png' if _is_dark_theme() else 'images/iconplugin_light.png'
        icon = _get_plugin_icon(icon_path, plugin_path=getattr(self, 'plugin_path', None), plugin_name=self.name)
        if icon is not None:
            self.qaction.setIcon(icon)

    def genesis(self):
        self.rebuild_icon()
        self._helper_group_definitions_cache = None
        self._quick_create_presets_cache = None
        if COLUMNS_HELPER_DEBUG_ENABLED:
            debug_print('[ColumnsHelper][DEBUG] genesis start')
        _install_columns_preferences_filter_patch()
        self._setup_toolbar_menu()
        self._register_shortcuts()
        self.qaction.triggered.connect(self.open_columns_preferences)
        # Connect to palette changes to update icon on theme switch
        try:
            app = QApplication.instance()
            if app is not None:
                app.paletteChanged.connect(self.rebuild_icon)
        except Exception:
            pass

        # Pre-cache QR code data from zip for About dialog
        try:
            from calibre.customize.zipplugin import get_resources
            self._cached_qr_data = get_resources(self.plugin_path, 'images/qrcode.png')
        except Exception:
            self._cached_qr_data = None

    def _setup_toolbar_menu(self):
        try:
            self.menu = self.qaction.menu()
            if self.menu is None:
                self.menu = QMenu(self.gui)
                self.qaction.setMenu(self.menu)
            self.menu.clear()

            def set_icon(action, icon):
                if action is None or icon is None:
                    return
                try:
                    if not icon.isNull():
                        action.setIcon(icon)
                except Exception:
                    pass

            open_action = self.menu.addAction(_('Open Columns Helper'))
            open_action.triggered.connect(self.open_columns_preferences)
            set_icon(open_action, _get_plugin_icon('images/iconplugin_light.png', plugin_name=PLUGIN_NAME))

            packs_action = self.menu.addAction(_('Open Column Pack Browser'))
            packs_action.triggered.connect(self.open_packs_dialog)
            set_icon(packs_action, _get_plugin_icon('images/pack_light.png', plugin_name=PLUGIN_NAME))

            about_action = self.menu.addAction(_('About'))
            about_action.triggered.connect(self.open_about_dialog)
            try:
                set_icon(about_action, QIcon.ic('help.png'))
            except Exception:
                pass
        except Exception:
            self.menu = None

    def _helper_group_definitions(self):
        if self._helper_group_definitions_cache is None:
            self._helper_group_definitions_cache = list(build_helper_group_definitions(_))
        return list(self._helper_group_definitions_cache)

    def _quick_create_presets(self):
        if self._quick_create_presets_cache is None:
            self._quick_create_presets_cache = build_quick_create_presets(_)
        return self._quick_create_presets_cache

    def _showroom_get_presets(self, group):
        return dict(self._quick_create_presets().get(group, {}))

    def _ensure_pack_browser_host(self, show_window=False):
        dialog = open_modeless_columns_dialog(self.gui, parent=self.gui, show_window=show_window)
        if dialog is not None:
            dialog._cdf_hidden_for_pack_browser = True
            if hasattr(self, '_cached_qr_data'):
                dialog._cached_qr_data = self._cached_qr_data
        return dialog

    def _run_showroom_quick_create(self, group, key):
        dialog = self._ensure_pack_browser_host(show_window=True)
        if dialog is not None:
            return dialog.run_quick_create(group, key)
        return None

    def _run_showroom_quick_create_batch(self, group, keys):
        dialog = self._ensure_pack_browser_host(show_window=True)
        if dialog is not None:
            return dialog.run_quick_create_batch(group, keys)
        return None

    def _register_shortcuts(self):
        try:
            self._shortcut_open_columns = QAction(_('Open Columns Helper'), self.gui)
            self._shortcut_open_columns.triggered.connect(self.open_columns_preferences)
            self.gui.addAction(self._shortcut_open_columns)
            self.gui.keyboard.register_shortcut(
                'plugin:columns_helper:open_main_window',
                _('Columns Helper: open main window'),
                default_keys=(),
                action=self._shortcut_open_columns,
                description=_('Open the Columns Helper window.'),
                group=PLUGIN_NAME,
                persist_shortcut=True,
            )
        except Exception:
            self._shortcut_open_columns = None
        try:
            self._shortcut_open_packs = QAction(_('Open Column Pack Browser'), self.gui)
            self._shortcut_open_packs.triggered.connect(self.open_packs_dialog)
            self.gui.addAction(self._shortcut_open_packs)
            self.gui.keyboard.register_shortcut(
                'plugin:columns_helper:open_pack_browser',
                _('Columns Helper: open Column Pack Browser'),
                default_keys=(),
                action=self._shortcut_open_packs,
                description=_('Open the Column Pack Browser window.'),
                group=PLUGIN_NAME,
                persist_shortcut=True,
            )
        except Exception:
            self._shortcut_open_packs = None

    def open_columns_preferences(self):
        _install_columns_preferences_filter_patch()
        dialog = open_modeless_columns_dialog(self.gui, parent=self.gui)
        if dialog is not None:
            dialog._cdf_hidden_for_pack_browser = False
        if dialog is not None and hasattr(self, '_cached_qr_data'):
            dialog._cached_qr_data = self._cached_qr_data

    def open_to_lookup(self, lookup_name):
        _install_columns_preferences_filter_patch()
        dialog = open_modeless_columns_dialog(self.gui, parent=self.gui)
        if dialog is not None:
            dialog._cdf_hidden_for_pack_browser = False
        if dialog is not None and hasattr(self, '_cached_qr_data'):
            dialog._cached_qr_data = self._cached_qr_data
        if dialog is not None and hasattr(dialog, 'open_to_lookup'):
            return bool(dialog.open_to_lookup(lookup_name))
        return False

    def open_about_dialog(self):
        dialog = open_modeless_columns_dialog(self.gui, parent=self.gui, show_window=False)
        if dialog is not None and hasattr(self, '_cached_qr_data'):
            dialog._cached_qr_data = self._cached_qr_data
        if dialog is not None:
            try:
                dialog.show_about_dialog()
            except Exception:
                pass

    def open_packs_dialog(self):
        dialog = open_helper_showroom_dialog(
            self.gui,
            group_definitions=self._helper_group_definitions(),
            get_presets=self._showroom_get_presets,
            create_one=self._run_showroom_quick_create,
            create_many=self._run_showroom_quick_create_batch,
        )
        if dialog is not None and hasattr(self, '_cached_qr_data'):
            dialog._cached_qr_data = self._cached_qr_data
        if dialog is not None:
            try:
                dialog.showNormal()
                dialog.raise_()
                dialog.activateWindow()
            except Exception:
                pass
