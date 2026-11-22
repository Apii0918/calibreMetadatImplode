from calibre.customize.conversion import OutputFormatPlugin

__license__ = 'GPL v3'
__copyright__ = '2026, SamLiao & Codex'


class CBZOutput(OutputFormatPlugin):
    name = 'CBZ Output'
    description = '依閱讀順序擷取書中圖片，封裝為檔名不重複的 CBZ 漫畫檔。'
    author = 'SamLiao & Codex'
    version = (0, 1)
    minimum_calibre_version = (9, 19, 0)
    supported_platforms = ['windows', 'osx', 'linux']
    file_type = 'cbz'

    def convert(self, oeb_book, output_path, input_plugin, opts, log):
        from calibre_plugins.cbz_output.core import ordered_images, write_cbz

        pages = ordered_images(oeb_book, log)
        write_cbz(output_path, pages)
        log.info(f'已匯出 {len(pages)} 頁圖片至 CBZ。')
