"""Manifest validation and update planning; checking never downloads a package."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zipfile import ZipFile

DEFAULT_REPO = 'SamLaio/calibreMetadatImplode'
FORMAT = 'calibre-github-plugins'
IDENTITY = 'github-plugin-identity.json'
MAX_JSON = 2 * 1024 * 1024
MAX_PACKAGE = 256 * 1024 * 1024


def repository(value):
    value = value.strip().removeprefix('https://github.com/').rstrip('/')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+', value):
        raise ValueError('來源必須為 GitHub 的 owner/repo。')
    if value.split('/')[1] in ('.', '..'):
        raise ValueError('GitHub 庫名稱無效。')
    return value


def source_id(repo):
    return 'github:' + repository(repo).lower()


def version(value):
    if not isinstance(value, list) or not value or len(value) > 16 or any(type(n) is not int or n < 0 for n in value):
        raise ValueError('外掛數字版號無效。')
    return tuple(value)


def digest(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def payload_digest(path):
    result = hashlib.sha256(b'calibre-plugin-content-v1\0')
    with ZipFile(path) as archive:
        for member in sorted(archive.infolist(), key=lambda m: m.filename):
            if member.is_dir() or member.filename == IDENTITY:
                continue
            if member.file_size > MAX_PACKAGE:
                raise ValueError('外掛檔案超過大小限制。')
            name = member.filename.encode('utf-8')
            result.update(len(name).to_bytes(8, 'big'))
            result.update(name)
            result.update(member.file_size.to_bytes(8, 'big'))
            with archive.open(member) as stream:
                while chunk := stream.read(1024 * 1024):
                    result.update(chunk)
    return result.hexdigest()


def identity_matches(data, expected):
    return isinstance(data, dict) and all(data.get(k) == expected[k] for k in ('id', 'source'))


def identity(path):
    with ZipFile(path) as archive:
        names = archive.namelist()
        if IDENTITY not in names:
            return None
        if names.count(IDENTITY) != 1 or archive.getinfo(IDENTITY).file_size > MAX_JSON:
            raise ValueError('外掛身分檔重複或過大。')
        data = json.loads(archive.read(IDENTITY))
        if not isinstance(data, dict) or not isinstance(data.get('id'), str) or not isinstance(data.get('source'), str):
            raise ValueError('外掛身分檔無效。')
        if not re.fullmatch(r'[0-9a-f]{64}', data.get('sha256', '')):
            raise ValueError('外掛身分檔缺少內容 SHA-256。')
        return data


def github_url(url):
    parsed = urlsplit(url)
    host = parsed.hostname or ''
    if (parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None, 443)
            or not (host in ('github.com', 'api.github.com') or host.endswith('.githubusercontent.com'))):
        raise ValueError('下載網址必須為 GitHub HTTPS 網址。')
    return url


def fetch(url, limit):
    class GitHubRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            github_url(newurl)
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    request = Request(github_url(url), headers={'User-Agent': 'calibre-github-plugin-updater/0.1'})
    with build_opener(GitHubRedirect()).open(request, timeout=30) as response:
        github_url(response.url)
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('下載內容超過大小限制。')
    return data


def manifest(data, repo):
    if not isinstance(data, dict) or data.get('format') != FORMAT or data.get('schema') != 1 or data.get('source') != source_id(repo):
        raise ValueError('更新清單格式或來源不符。')
    entries = data.get('plugins')
    if not isinstance(entries, list) or len(entries) > 1000:
        raise ValueError('外掛清單無效或過長。')
    ids, names, assets = set(), set(), set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('外掛清單項目無效。')
        for key in ('id', 'name', 'asset', 'sha256', 'package_sha256'):
            if not isinstance(entry.get(key), str) or not entry[key]:
                raise ValueError('外掛清單缺少必要欄位。')
        if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,159}', entry['id']):
            raise ValueError('外掛 ID 無效。')
        if any(c in entry['name'] for c in '/\\\x00') or len(entry['name']) > 180:
            raise ValueError('外掛名稱無效。')
        if any(not re.fullmatch(r'[0-9a-f]{64}', entry[k]) for k in ('sha256', 'package_sha256')):
            raise ValueError('SHA-256 格式無效。')
        if '/' in entry['asset'] or '\\' in entry['asset'] or not entry['asset'].endswith('.zip'):
            raise ValueError('安裝附件名稱無效。')
        version(entry.get('version'))
        version(entry.get('minimum_calibre_version'))
        platforms = entry.get('supported_platforms')
        if not isinstance(platforms, list) or not platforms or any(p not in ('windows', 'osx', 'linux') for p in platforms):
            raise ValueError('支援平台無效。')
        if type(entry.get('size')) is not int or not 0 < entry['size'] <= MAX_PACKAGE:
            raise ValueError('安裝包大小無效。')
        if entry['id'] in ids or entry['name'] in names or entry['asset'] in assets:
            raise ValueError('更新清單有重複外掛或附件。')
        ids.add(entry['id']); names.add(entry['name']); assets.add(entry['asset'])
    return entries


def release_entries(repo, get=fetch):
    repo = repository(repo)
    release = json.loads(get(f'https://api.github.com/repos/{repo}/releases/latest', MAX_JSON))
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('只接受正式發行。')
    assets = release.get('assets', [])
    by_name = {}
    for asset in assets:
        if asset['name'] in by_name:
            raise ValueError('發行附件名稱重複。')
        by_name[asset['name']] = asset
    if 'plugins.json' not in by_name:
        raise ValueError('此庫最新正式發行沒有 plugins.json，請發布更新清單。')
    prefix = f'https://github.com/{repo}/releases/download/'
    def asset_url(asset):
        url = asset['browser_download_url']
        if not url.lower().startswith(prefix.lower()):
            raise ValueError('附件不屬於指定 GitHub 庫。')
        return github_url(url)
    data = json.loads(get(asset_url(by_name['plugins.json']), MAX_JSON))
    entries = manifest(data, repo)
    result = []
    for entry in entries:
        asset = by_name.get(entry['asset'])
        if not asset or asset.get('size') != entry['size']:
            raise ValueError('清單與發行附件不一致。')
        result.append(dict(entry, source=source_id(repo), repo=repo, url=asset_url(asset)))
    return result


def plan(entry, installed, bindings, calibre_version, platform):
    current = installed.get(entry['name'])
    row = dict(entry, current=current['version'] if current else None, eligible=False,
               observed_sha256=current['sha256'] if current else '')
    if current is None:
        row['status'] = '未安裝（不自動新增）'
        return row
    binding = bindings.get(entry['name'])
    expected = {'source': entry['source'], 'id': entry['id']}
    local_identity = current.get('identity')
    if binding is None and identity_matches(local_identity, expected):
        binding = expected
    if binding is None or {k: binding.get(k) for k in expected} != expected:
        row['status'] = '需要綁定來源' if binding is None else '已綁定其他來源'
    elif not identity_matches(local_identity, expected) and binding.get('accepted_sha256') != current['sha256']:
        row['status'] = '安裝來源已變更，請重新綁定'
    elif current['sha256'] == entry['sha256']:
        row['status'] = '內容相同'
    elif current['version'] is None:
        row['status'] = '目前外掛載入失敗，無法比較版號'
    elif tuple(calibre_version) < version(entry['minimum_calibre_version']) or platform not in entry['supported_platforms']:
        row['status'] = '不相容目前 calibre／平台'
    elif version(entry['version']) < tuple(current['version']):
        row['status'] = '遠端較舊，不降版'
    elif version(entry['version']) == tuple(current['version']):
        row['status'] = '同版內容不符，請來源修正版號'
    else:
        row['status'] = '可更新'
        row['eligible'] = True
    return row


def installed_plugins():
    from calibre.customize import PluginInstallationType
    from calibre.customize.ui import config, initialized_plugins, plugin_dir
    loaded = {p.name: p for p in initialized_plugins() if p.installation_type == PluginInstallationType.EXTERNAL}
    result = {}
    for name, original in config['plugins'].items():
        path = Path(plugin_dir) / (name + '.zip')
        if not path.is_file():
            path = Path(original)
        try:
            stamp = identity(path)
            result[name] = {'path': str(path), 'version': list(loaded[name].version) if name in loaded else None,
                            'sha256': stamp['sha256'] if stamp else payload_digest(path), 'identity': stamp}
        except Exception as error:
            result[name] = {'path': str(path), 'version': None, 'sha256': '', 'identity': None, 'error': str(error)}
    return result


def check(sources, bindings):
    from calibre.constants import numeric_version, iswindows, ismacos
    installed = installed_plugins()
    platform = 'windows' if iswindows else 'osx' if ismacos else 'linux'
    rows, errors = [], []
    for repo in sources:
        try:
            entries = release_entries(repo)
            for entry in entries:
                current = installed.get(entry['name'])
                expected = {'id': entry['id'], 'source': entry['source']}
                if entry['name'] not in bindings and current and identity_matches(current.get('identity'), expected):
                    bindings[entry['name']] = dict(expected, accepted_sha256=current['sha256'])
            rows.extend(plan(e, installed, bindings, numeric_version, platform) for e in entries)
        except Exception as error:
            errors.append(f'{repo}：{error}')
    return {'rows': rows, 'errors': errors}


def install(entries, bindings, backup_root, get=fetch):
    import shutil
    import tempfile
    from datetime import datetime
    from uuid import uuid4
    from calibre.constants import numeric_version, iswindows, ismacos
    from calibre.customize.ui import (BLACKLISTED_PLUGINS, add_plugin, config, disable_plugin,
                                     enable_plugin, is_disabled, load_plugin, plugin_dir)
    installed, result = installed_plugins(), {'installed': [], 'failed': [], 'backups': []}
    platform = 'windows' if iswindows else 'osx' if ismacos else 'linux'
    for entry in entries:
        name = entry['name']
        try:
            current = installed.get(name)
            if not current or current['sha256'] != entry['observed_sha256']:
                raise ValueError('檢查後安裝內容已變更，請重新檢查。')
            if payload_digest(current['path']) != current['sha256']:
                raise ValueError('目前安裝內容與身分 SHA 不符，請先處理本機變更。')
            if not plan(entry, installed, bindings, numeric_version, platform)['eligible'] or name in BLACKLISTED_PLUGINS:
                raise ValueError('此外掛不可更新或來源尚未綁定。')
            data = get(entry['url'], MAX_PACKAGE)
            if len(data) != entry['size'] or hashlib.sha256(data).hexdigest() != entry['package_sha256']:
                raise ValueError('下載檔案的大小或 SHA-256 與清單不符。')
            with tempfile.TemporaryDirectory(prefix='github-plugin-update-') as temporary:
                package = Path(temporary) / 'incoming.zip'
                package.write_bytes(data)
                with ZipFile(package) as archive:
                    members = archive.infolist()
                    if len(members) > 10000 or sum(m.file_size for m in members) > 1024 * 1024 * 1024:
                        raise ValueError('安裝包解壓大小或檔案數超過上限。')
                    if len({m.filename for m in members}) != len(members) or any(
                            m.filename.startswith('/') or '\\' in m.filename or ':' in m.filename
                            or '..' in m.filename.split('/') for m in members):
                        raise ValueError('安裝包包含重複或不安全路徑。')
                stamp = identity(package)
                if (not identity_matches(stamp, entry) or stamp['sha256'] != entry['sha256']
                        or payload_digest(package) != entry['sha256']):
                    raise ValueError('安裝包身分與更新清單不符。')
                # Persist recovery material before importing any incoming plugin code.
                backup = Path(backup_root) / (datetime.now().strftime('%Y%m%d-%H%M%S-') + uuid4().hex[:12])
                backup.mkdir(parents=True)
                previous = backup / 'previous.zip'
                shutil.copyfile(current['path'], previous)
                registry = dict(config['plugins'])
                disabled, enabled = set(config['disabled_plugins']), set(config['enabled_plugins'])
                customization = dict(config['plugin_customization'])
                state = {'name': name, 'version': current['version'], 'sha256': current['sha256'],
                         'plugins': registry, 'disabled_plugins': sorted(disabled),
                         'enabled_plugins': sorted(enabled), 'plugin_customization': customization}
                (backup / 'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
                result['backups'].append(str(backup))
                target = Path(plugin_dir) / (name + '.zip')
                had_target = target.is_file()
                changed = False
                try:
                    cls = load_plugin(str(package))
                    if cls.name != name or tuple(cls.version) != version(entry['version']):
                        raise ValueError('程式宣告的名稱或版號與清單不符。')
                    if tuple(cls.minimum_calibre_version) != version(entry['minimum_calibre_version']) or list(cls.supported_platforms) != entry['supported_platforms']:
                        raise ValueError('程式宣告的相容性與清單不符。')
                    was_disabled = is_disabled(name)
                    changed = True
                    add_plugin(str(package))
                    (disable_plugin if was_disabled else enable_plugin)(name)
                    if digest(target) != entry['package_sha256']:
                        raise ValueError('安裝後檔案校驗不符。')
                except Exception:
                    if changed:
                        if had_target:
                            shutil.copyfile(previous, target)
                        else:
                            target.unlink(missing_ok=True)
                        config['plugins'] = registry
                        config['disabled_plugins'] = disabled
                        config['enabled_plugins'] = enabled
                        config['plugin_customization'] = customization
                    raise
                bindings[name] = {'id': entry['id'], 'source': entry['source'], 'accepted_sha256': entry['sha256']}
                result['installed'].append(name)
        except Exception as error:
            result['failed'].append(f'{name}：{error}')
    return result


def worker():
    import sys
    import traceback
    from calibre.utils.config import JSONConfig, config_dir
    job_path, report_path = map(Path, sys.argv[-2:])
    try:
        job = json.loads(job_path.read_text(encoding='utf-8'))
        prefs = JSONConfig('plugins/github_plugin_updater')
        bindings = dict(prefs.get('bindings', {}))
        if job['mode'] == 'check':
            result = check(job['sources'], bindings)
            prefs['bindings'] = bindings
        elif job['mode'] == 'install':
            result = install(job['entries'], bindings, Path(config_dir) / 'github-plugin-updater-backups')
            prefs['bindings'] = bindings
        else:
            raise ValueError('未知工作模式。')
    except Exception as error:
        result = {'error': str(error), 'details': traceback.format_exc()}
    report_path.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
