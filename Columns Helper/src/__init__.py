__license__   = 'GPL v3'
__copyright__ = '2026, Comfy.n'
__docformat__ = 'restructuredtext en'

from calibre.customize import InterfaceActionBase
import os

load_translations()


class ColumnsHelperPlugin(InterfaceActionBase):
    name = 'Columns Helper'
    description = _('Preview, create, and manage custom columns faster with quick-create links, curated column packs and template-aware tools')
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Comfy.n'
    version = (2, 1, 1, 1)
    minimum_calibre_version = (5, 44, 0)

    actual_plugin = 'calibre_plugins.columns_helper.ui:ColumnsHelperAction'

    def initialize(self):
        return super().initialize()
