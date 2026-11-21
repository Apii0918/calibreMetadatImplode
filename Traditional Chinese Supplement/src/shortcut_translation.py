from calibre.gui2 import keyboard
from calibre.utils.icu import lower
from qt.core import Qt


def install_shortcut_translation(texts):
    original_doc = keyboard.Delegate.to_doc
    original_editor = keyboard.Editor.initialize
    original_matches = keyboard.ConfigModel.get_matches

    def to_doc(delegate, index):
        doc = original_doc(delegate, index)
        node = index.data(Qt.ItemDataRole.UserRole)
        if node is not None:
            source = node.data['name'] if node.is_shortcut else node.data
            translated = texts.get(source, source)
            if translated != source:
                cursor = doc.find(source)
                if not cursor.isNull():
                    cursor.insertText(translated)
        return doc

    def initialize(editor, shortcut, all_shortcuts):
        original_editor(editor, shortcut, all_shortcuts)
        source = shortcut['name']
        translated = texts.get(source, source)
        if translated != source:
            from calibre import prepare_string_for_xml
            editor.header.setText(editor.header.text().replace(source, prepare_string_for_xml(translated), 1))

    def get_matches(model, location, query, candidates=None):
        if candidates is None:
            candidates = model.universal_set()
        candidates = set(candidates)
        matches = original_matches(model, location, query, candidates)
        if query:
            query = lower(query)
            for group, row in candidates:
                node = model.root_nodes[group]
                sources = (node.data,) if row < 0 else (
                    node.children[row].data['name'], node.children[row].data.get('desc') or '',
                )
                if any(query in lower(texts.get(source, source)) for source in sources):
                    matches.add((group, row))
        return matches

    keyboard.Delegate.to_doc = to_doc
    keyboard.Editor.initialize = initialize
    keyboard.ConfigModel.get_matches = get_matches
    return original_doc, original_editor, original_matches


def restore_shortcut_translation(originals):
    keyboard.Delegate.to_doc, keyboard.Editor.initialize, keyboard.ConfigModel.get_matches = originals
