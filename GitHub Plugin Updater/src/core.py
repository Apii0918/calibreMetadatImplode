"""Manifest validation and update planning; checking never downloads a package."""
import hashlib
import json
import re
import time
from datetime import datetime
from urllib.error import HTTPError
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zipfile import ZipFile

DEFAULT_REPO = 'SamLaio/calibreMetadatImplode'
FORMAT = 'calibre-github-plugins'
IDENTITY = 'github-plugin-identity.json'
FETCH_CACHE = None
API_TOKEN = ''
MAX_JSON = 2 * 1024 * 1024
MAX_PACKAGE = 256 * 1024 * 1024


def repository(value):
    value = value.strip()
    if '://' in value:
        parsed = urlsplit(value)
        if (parsed.scheme != 'https' or parsed.hostname != 'github.com' or parsed.username
                or parsed.password or parsed.port not in (None, 443)):
            raise ValueError('來源必須為 GitHub HTTPS 網址。')
        parts = parsed.path.strip('/').split('/')
        if len(parts) < 2:
            raise ValueError('GitHub 網址缺少庫名稱。')
        value = '/'.join(parts[:2])
    value = value.rstrip('/').removesuffix('.git')
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
            redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
            if redirected is not None:
                redirected.remove_header('Authorization')
            return redirected

    github_url(url)
    api = urlsplit(url).hostname == 'api.github.com'
    cache = Path(FETCH_CACHE) if api and FETCH_CACHE is not None else None
    cached = None
    if cache is not None:
        cache = cache / hashlib.sha256(API_TOKEN.encode()).hexdigest()
        cache.mkdir(parents=True, exist_ok=True)
        cached = cache / (hashlib.sha256(url.encode()).hexdigest() + '.json')
        if cached.is_file() and 0 <= time.time() - cached.stat().st_mtime < 300:
            data = cached.read_bytes()
            if len(data) <= limit:
                return data
        cooldown = cache / 'rate-limit.json'
        try:
            until = json.loads(cooldown.read_text(encoding='utf-8'))['until']
            if isinstance(until, (int, float)) and until > time.time():
                raise ValueError('GitHub API 額度已用完或暫時限流，請於 ' + datetime.fromtimestamp(until).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z') + ' 後重試。')
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            pass
    request = Request(url, headers={'User-Agent': 'calibre-github-plugin-updater/0.3.1'})
    if api and API_TOKEN:
        request.add_unredirected_header('Authorization', 'Bearer ' + validate_token(API_TOKEN))
    try:
        with build_opener(GitHubRedirect()).open(request, timeout=30) as response:
            github_url(response.url)
            data = response.read(limit + 1)
    except HTTPError as error:
        if api and error.code == 401:
            raise ValueError('GitHub Token 無效或已到期，請到管理來源重新設定或清除。') from None
        if not api or error.code not in (403, 429):
            raise
        message = error.read(MAX_JSON).decode('utf-8', errors='replace').lower()
        if error.code != 429 and error.headers.get('X-RateLimit-Remaining') != '0' and 'rate limit' not in message:
            raise
        now = time.time()
        try:
            until = max(now + 60, float(error.headers.get('X-RateLimit-Reset', 0)), now + float(error.headers.get('Retry-After', 0)))
        except ValueError:
            until = now + 60
        if cache is not None:
            cooldown.write_text(json.dumps({'until': until}), encoding='utf-8')
        raise ValueError('GitHub API 額度已用完或暫時限流，請於 ' + datetime.fromtimestamp(until).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z') + ' 後重試。' + ('已使用 Token；登入額度仍有限制。' if API_TOKEN else '匿名額度由同一出口 IP 共用。')) from None
    if len(data) > limit:
        raise ValueError('下載內容超過大小限制。')
    if cached is not None:
        json.loads(data)
        cached.write_bytes(data)
    return data


def validate_token(value):
    value = value.strip()
    if value and not re.fullmatch(r'[A-Za-z0-9_]{1,512}', value):
        raise ValueError('Token 格式無效，請只貼上 GitHub Token，不要包含網址或其他文字。')
    return value


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


def release_asset_url(repo, asset):
    url = asset['browser_download_url']
    prefix = f'https://github.com/{repo}/releases/download/'
    if not url.lower().startswith(prefix.lower()):
        raise ValueError('附件不屬於指定 GitHub 庫。')
    asset_id = asset.get('id')
    if type(asset_id) is int and asset_id > 0:
        url += ('&' if '?' in url else '?') + f'calibre_asset={asset_id}'
    return github_url(url)


def external_entry(repo, plugin_id, name, number, mode, release, expected):
    entry = dict(id=plugin_id, name=name, source=source_id(repo), repo=repo, version=list(number), mode=mode,
                 minimum_calibre_version=None, supported_platforms=None, sha256=None,
                 package_sha256=None, size=0, asset=expected, asset_id=None, url=None)
    try:
        if release is None:
            raise ValueError('相同外掛版號有多個正式發行，無法唯一配對。')
        assets = [a for a in release.get('assets', []) if a.get('name') == expected]
        if len(assets) != 1:
            raise ValueError('找不到唯一的版本 ZIP：' + expected)
        asset = assets[0]
        if type(asset.get('size')) is not int or not 0 < asset['size'] <= MAX_PACKAGE:
            raise ValueError('附件大小無效。')
        stamp = asset.get('digest')
        if stamp is not None and not re.fullmatch(r'sha256:[0-9a-f]{64}', stamp):
            raise ValueError('GitHub 附件 digest 無效。')
        entry.update(size=asset['size'], url=release_asset_url(repo, asset), asset_id=asset.get('id'),
                     package_sha256=stamp[7:] if stamp else None)
    except (KeyError, ValueError) as error:
        entry['error'] = str(error)
    return entry


def single_entries(repo, rule, get=fetch):
    release = json.loads(get(f'https://api.github.com/repos/{repo}/releases/latest', MAX_JSON))
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('只接受正式發行。')
    match = re.fullmatch(r'v?([0-9]+(?:\.[0-9]+)+)', release.get('tag_name', ''))
    if not match:
        raise ValueError('正式發行標籤無法解析成數字版號。')
    number = tuple(map(int, match[1].split('.')))
    return [external_entry(repo, rule['id'], rule['name'], number, 'single', release, rule['asset'])]


def prefixed_entries(repo, rules, get=fetch):
    candidates = {}
    for page in range(1, 21):
        releases = json.loads(get(f'https://api.github.com/repos/{repo}/releases?per_page=100&page={page}', 8 * MAX_JSON))
        if not isinstance(releases, list) or len(releases) > 100:
            raise ValueError('GitHub 發行列表格式無效。')
        for release in releases:
            if release.get('draft') or release.get('prerelease'):
                continue
            match = re.fullmatch(r'([a-z0-9_]+)-v?([0-9]+(?:\.[0-9]+)+)', release.get('tag_name', ''))
            if not match or match[1] not in rules:
                continue
            prefix, number = match[1], tuple(map(int, match[2].split('.')))
            previous = candidates.get(prefix)
            if previous is None or number > previous[0]:
                candidates[prefix] = (number, [release])
            elif number == previous[0]:
                previous[1].append(release)
        if len(releases) < 100:
            break
    else:
        raise ValueError('發行超過 2000 筆，未完成掃描，不採用部分結果。')
    result = []
    for prefix, (number, releases) in sorted(candidates.items()):
        release = releases[0] if len(releases) == 1 else None
        result.append(external_entry(repo, repo.split('/')[0].lower() + '.' + prefix.replace('_', '-'),
                                     rules[prefix], number, 'prefixed', release,
                                     releases[0]['tag_name'] + '.zip'))
    return result


def release_entries(repo, get=fetch):
    repo = repository(repo)
    if repo.lower() == 'kiwidude68/calibre_plugins':
        from .prefixes import PREFIX_RULES
        return prefixed_entries(repo, PREFIX_RULES[repo.lower()], get)
    if repo.lower() == 'hamsterexastris/calibre-azw6-image-merge':
        from .singles import SINGLE_RULES
        return single_entries(repo, SINGLE_RULES[repo.lower()], get)
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
    data = json.loads(get(release_asset_url(repo, by_name['plugins.json']), MAX_JSON))
    entries = manifest(data, repo)
    result = []
    for entry in entries:
        # GitHub rewrites spaces in uploaded attachment names to dots.
        asset = by_name.get(entry['asset']) or by_name.get(entry['asset'].replace(' ', '.'))
        if not asset or asset.get('size') != entry['size']:
            raise ValueError('清單與發行附件不一致。')
        result.append(dict(entry, mode='manifest', source=source_id(repo), repo=repo, url=release_asset_url(repo, asset)))
    return result


def plan(entry, installed, bindings, calibre_version, platform):
    current = installed.get(entry['name'])
    row = dict(entry, current=current['version'] if current else None, installed=current is not None, eligible=False,
               observed_sha256=current['sha256'] if current else '')
    if entry.get('error'):
        row['status'] = entry['error']
        return row
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
    elif entry.get('mode') in ('prefixed', 'single'):
        saved_digest = binding.get('package_sha256') if binding.get('accepted_sha256') == current['sha256'] else None
        if saved_digest and saved_digest == entry.get('package_sha256'):
            row['status'] = '附件相同'
        elif current['version'] is None:
            row['status'] = '目前外掛載入失敗，可勾選修復'
        elif tuple(current['version']) < version(entry['version']):
            row['status'], row['eligible'] = '可更新', True
        elif tuple(current['version']) == version(entry['version']):
            if binding.get('asset_id') and entry.get('asset_id') and binding['asset_id'] != entry['asset_id']:
                row['status'] = '版號相同（附件已更換，未驗證內容）'
            else:
                row['status'] = '版號相同（附件已變更或尚無校驗基準）'
        else:
            row['status'] = '遠端較舊（可勾選降版）'
        if not entry.get('package_sha256'):
            row['status'] += '；來源未提供附件 SHA'
    elif current['sha256'] == entry['sha256']:
        row['status'] = '內容相同'
    elif current['version'] is None:
        row['status'] = '目前外掛載入失敗，無法比較版號'
    elif tuple(calibre_version) < version(entry['minimum_calibre_version']) or platform not in entry['supported_platforms']:
        row['status'] = '不相容目前 calibre／平台'
    elif version(entry['version']) < tuple(current['version']):
        row['status'] = '遠端較舊（可勾選降版）'
    elif version(entry['version']) == tuple(current['version']):
        row['status'] = '同版內容不同（可勾選重裝）'
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


def install(entries, bindings, backup_root, get=fetch, force=False, auto_backup=True):
    import shutil
    import tempfile
    from datetime import datetime
    from uuid import uuid4
    from calibre.constants import numeric_version, iswindows, ismacos
    from calibre.customize.ui import (BLACKLISTED_PLUGINS, add_plugin, config, disable_plugin,
                                     enable_plugin, is_disabled, load_plugin, plugin_dir)
    installed, result = installed_plugins(), {'installed': [], 'failed': [], 'backups': [], 'installed_state': {}}
    platform = 'windows' if iswindows else 'osx' if ismacos else 'linux'
    for entry in entries:
        name = entry['name']
        try:
            external = entry.get('mode') in ('prefixed', 'single')
            if entry.get('error'):
                raise ValueError(entry['error'])
            current = installed.get(name)
            if not current or current['sha256'] != entry['observed_sha256']:
                raise ValueError('檢查後安裝內容已變更，請重新檢查。')
            if not force and payload_digest(current['path']) != current['sha256']:
                raise ValueError('目前安裝內容與身分 SHA 不符，請先處理本機變更。')
            incompatible = not external and (tuple(numeric_version) < version(entry['minimum_calibre_version'])
                                             or platform not in entry['supported_platforms'])
            if (name in BLACKLISTED_PLUGINS or incompatible
                    or (not force and not plan(entry, installed, bindings, numeric_version, platform)['eligible'])):
                raise ValueError('此外掛不相容、已被 calibre 封鎖，或一般更新條件不符。')
            data = get(entry['url'], MAX_PACKAGE)
            package_sha = hashlib.sha256(data).hexdigest()
            if len(data) != entry['size'] or (entry.get('package_sha256') and package_sha != entry['package_sha256']):
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
                content_sha = payload_digest(package)
                if not external:
                    stamp = identity(package)
                    if (not identity_matches(stamp, entry) or stamp['sha256'] != entry['sha256']
                            or content_sha != entry['sha256']):
                        raise ValueError('安裝包身分與更新清單不符。')
                # Keep temporary rollback material even when retained backups are disabled.
                backup = (Path(backup_root) / (datetime.now().strftime('%Y%m%d-%H%M%S-') + uuid4().hex[:12])
                          if auto_backup else Path(temporary) / 'recovery')
                backup.mkdir(parents=True)
                safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).strip(' .')[:100] or 'plugin'
                old_version = '.'.join(map(str, current['version'])) if current['version'] else '未知版號'
                previous = backup / f'{safe_name}-{old_version}.zip'
                shutil.copyfile(current['path'], previous)
                registry = dict(config['plugins'])
                disabled, enabled = set(config['disabled_plugins']), set(config['enabled_plugins'])
                customization = dict(config['plugin_customization'])
                state = {'name': name, 'version': current['version'], 'sha256': current['sha256'], 'package': previous.name,
                         'plugins': registry, 'disabled_plugins': sorted(disabled),
                         'enabled_plugins': sorted(enabled), 'plugin_customization': customization}
                if auto_backup:
                    (backup / 'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
                    result['backups'].append(str(backup))
                target = Path(plugin_dir) / (name + '.zip')
                had_target = target.is_file()
                changed = False
                try:
                    cls = load_plugin(str(package))
                    if cls.name != name or tuple(cls.version) != version(entry['version']):
                        raise ValueError('程式宣告的名稱或版號與清單不符。')
                    if not external and (tuple(cls.minimum_calibre_version) != version(entry['minimum_calibre_version']) or list(cls.supported_platforms) != entry['supported_platforms']):
                        raise ValueError('程式宣告的相容性與清單不符。')
                    if tuple(numeric_version) < tuple(cls.minimum_calibre_version) or platform not in cls.supported_platforms:
                        raise ValueError('外掛不相容目前 calibre／平台。')
                    was_disabled = is_disabled(name)
                    changed = True
                    add_plugin(str(package))
                    (disable_plugin if was_disabled else enable_plugin)(name)
                    if digest(target) != package_sha:
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
                bindings[name] = {'id': entry['id'], 'source': entry['source'], 'accepted_sha256': content_sha,
                                  'package_sha256': package_sha}
                if external:
                    bindings[name]['asset_id'] = entry.get('asset_id')
                result['installed_state'][name] = {'sha256': content_sha}
                result['installed'].append(name)
        except Exception as error:
            result['failed'].append(f'{name}：{error}')
    return result


def backup_directory(prefs, config_root):
    path = Path(prefs.get('backup_dir') or Path(config_root) / 'github-plugin-updater-backups').expanduser()
    if not path.is_absolute():
        raise ValueError('備份資料夾必須為完整路徑。')
    return path


def worker():
    global FETCH_CACHE, API_TOKEN
    import sys
    import traceback
    from calibre.utils.config import JSONConfig, config_dir
    job_path, report_path = map(Path, sys.argv[-2:])
    try:
        FETCH_CACHE = Path(config_dir) / 'github-plugin-updater-cache'
        job = json.loads(job_path.read_text(encoding='utf-8'))
        prefs = JSONConfig('plugins/github_plugin_updater')
        API_TOKEN = validate_token(prefs.get('github_token', ''))
        bindings = dict(prefs.get('bindings', {}))
        if job['mode'] == 'check':
            result = check(job['sources'], bindings)
            prefs['bindings'] = bindings
        elif job['mode'] == 'install':
            auto_backup = job.get('auto_backup', prefs.get('auto_backup', True)) is not False
            result = install(job['entries'], bindings, backup_directory(prefs, config_dir) if auto_backup else None,
                             force=job.get('force') is True, auto_backup=auto_backup)
            prefs['bindings'] = bindings
        else:
            raise ValueError('未知工作模式。')
    except Exception as error:
        result = {'error': str(error), 'details': traceback.format_exc()}
    report_path.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
