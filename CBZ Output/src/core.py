import os
import re
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZIP_STORED, ZipFile


EXTENSIONS = {
    'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif',
    'image/webp': '.webp', 'image/bmp': '.bmp', 'image/tiff': '.tiff',
    'image/avif': '.avif', 'image/jxl': '.jxl', 'image/svg+xml': '.svg',
}


def href_key(href):
    parsed = urlsplit(str(href))
    if parsed.scheme or parsed.netloc:
        return None
    return unquote(parsed.path)


def document_images(document, images, log):
    for element in document.data.iter():
        if not isinstance(element.tag, str):
            continue
        tag = element.tag.rsplit('}', 1)[-1].lower()
        if tag == 'img':
            source = element.get('src')
        elif tag == 'image':
            source = element.get('href') or element.get('{http://www.w3.org/1999/xlink}href')
        elif tag == 'object':
            source = element.get('data')
        else:
            continue
        if not source:
            continue
        if href_key(source) is None:
            log.warning(f'略過未嵌入書檔的外部圖片：{source}')
            continue
        target = images.get(href_key(document.abshref(source)))
        if target is None:
            if tag == 'object':
                continue
            raise ValueError(f'找不到書中引用的圖片：{source}')
        yield target


def ordered_images(book, log):
    manifest = list(book.manifest)
    images = {href_key(item.href): item for item in manifest
              if item.media_type.startswith('image/')}
    if not images:
        raise ValueError('書中沒有可匯出的圖片；此工具不會將文字頁面轉成圖片。')
    pages = []
    for document in book.spine:
        if document.media_type.startswith('image/'):
            pages.append(document)
        elif document.media_type in ('application/xhtml+xml', 'text/html', 'image/svg+xml'):
            pages.extend(document_images(document, images, log))

    cover = None
    ids = {str(item.id): item for item in images.values()}
    for value in getattr(book.metadata, 'cover', ()):
        cover = ids.get(str(value))
        if cover is not None:
            break
    if cover is None and 'cover' in book.guide:
        key = href_key(book.guide['cover'].href)
        cover = images.get(key)
        if cover is None:
            document = next((item for item in manifest if href_key(item.href) == key), None)
            if document is not None and document.media_type in ('application/xhtml+xml', 'text/html'):
                cover = next(document_images(document, images, log), None)

    if not pages:
        log.warning('沒有找到章節圖片參照，改依圖片路徑的自然順序匯出。')
        pages = sorted(images.values(), key=lambda item: [int(p) if p.isdigit() else p.casefold()
                       for p in re.split(r'(\d+)', href_key(item.href))])
    if cover is not None:
        pages = [cover] + [item for item in pages if item is not cover]
    return pages


def write_cbz(destination, pages):
    if not pages:
        raise ValueError('沒有可匯出的圖片。')
    destination = Path(destination)
    fd, temporary = tempfile.mkstemp(prefix='.cbz-', suffix='.zip', dir=destination.parent)
    os.close(fd)
    try:
        width = max(6, len(str(len(pages))))
        with ZipFile(temporary, 'w', compression=ZIP_STORED, allowZip64=True) as archive:
            for index, item in enumerate(pages, 1):
                extension = EXTENSIONS.get(item.media_type)
                if extension is None:
                    raise ValueError(f'不支援的圖片格式：{item.media_type}（{item.href}）')
                data = item.bytes_representation
                if not data:
                    raise ValueError(f'圖片內容為空：{item.href}')
                archive.writestr(f'{index:0{width}d}{extension}', data)
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
