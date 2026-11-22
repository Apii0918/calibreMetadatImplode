def install_layout():
    from calibre.gui2.preferences.main import Browser
    from qt.core import QHBoxLayout

    if getattr(Browser, '_github_updater_second_row', False):
        return
    original = Browser.__init__

    def initialize(browser, *args, **kwargs):
        original(browser, *args, **kwargs)
        for category in browser.widgets:
            index = next((i for i, plugin in enumerate(category.plugins)
                          if plugin.name == 'GitHub Plugin Updater'), None)
            if index is None:
                continue
            button = category.buttons[index][0]
            category.bar_layout.removeWidget(button)
            row = QHBoxLayout()
            row.addWidget(button)
            row.addStretch()
            category._layout.addLayout(row)
            # Keep the native column widths, excluding our dedicated second row.
            browser.columns = max(1, max(len(w.plugins) - (w is category) for w in browser.widgets))
            for widget in browser.widgets:
                widget.columns = browser.columns
            browser.update_category_widths()
            break

    Browser.__init__ = initialize
    Browser._github_updater_second_row = True
