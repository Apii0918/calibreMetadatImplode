"""Backup format and worker. Inspection never imports code from the backup."""
import ast
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

FORMAT = 'calibre-plugin-backup'
MAX_PACKAGE = 256 * 1024 * 1024
MAX_TOTAL = 2 * 1024 * 1024 * 1024
MAX_PLUGINS = 1000
MAX_SETTINGS_FILES = 10000
MAX_SETTINGS_SIZE = 256 * 1024 * 1024
MAX_SETTING_FILE = 64 * 1024 * 1024
SKIP_SETTINGS = {'caches', 'cache', 'logs', 'crash-logs', 'customize.py.json', 'plugin-backup-recovery'}
RESERVED_NAMES = {'CON', 'PRN', 'AUX', 'NUL',
                  *('COM' + str(i) for i in range(1, 10)), *('LPT' + str(i) for i in range(1, 10))}


def settings_target(root, relative):
    parts = relative.split('/') if isinstance(relative, str) else []
    if not parts or any(not p or p in ('.', '..') or re.search(r'[<>:"\\|?*\x00-\x1f]', p)
                        or p.endswith(('.', ' ')) or p.split('.')[0].upper() in RESERVED_NAMES for p in parts):
        raise ValueError('設定檔路徑無效。')
    target = Path(root).joinpath(*parts)
    if not target.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('設定檔路徑超出 calibre 設定資料夾。')
    return target


def settings_files(root):
    result = []
    for path in sorted(Path(root).rglob('*')):
        rel = path.relative_to(root)
        if any((parent / 'metadata.db').is_file() for parent in path.parents if parent.is_relative_to(Path(root))):
            continue
        if (not path.is_file() or path.is_symlink() or any(p.startswith('.') or p.lower() in SKIP_SETTINGS for p in rel.parts)
                or path.suffix.lower() in ('.lock', '.log', '.pyc')
                or (rel.parts[0].lower() == 'plugins' and len(rel.parts) == 2 and path.suffix.lower() == '.zip')):
            continue
        settings_target(root, rel.as_posix())
        result.append((rel.as_posix(), path))
    if len(result) > MAX_SETTINGS_FILES:
        raise ValueError('設定檔數量超過備份上限。')
    return result


def selected_settings_files(root, plugins):
    # Only copy identifiable private files; shared calibre settings belong to full backups.
    prefixes = set()
    normalize = lambda value: re.sub(r'[^\w]', '', value.casefold())
    names = {normalize(p['name']) for p in plugins}
    for plugin in plugins:
        with ZipFile(plugin['path']) as archive:
            for member in archive.infolist():
                if not member.filename.endswith('.py') or member.file_size > MAX_SETTING_FILE:
                    continue
                try:
                    tree = ast.parse(archive.read(member).decode('utf-8-sig'))
                except (SyntaxError, UnicodeError):
                    continue
                for node in ast.walk(tree):
                    if (isinstance(node, ast.Call) and node.args
                            and isinstance(node.func, (ast.Name, ast.Attribute))
                            and (node.func.id if isinstance(node.func, ast.Name) else node.func.attr) == 'JSONConfig'
                            and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                        relative = node.args[0].value.replace('\\', '/') + '.json'
                        settings_target(root, relative)
                        if relative.startswith('plugins/'):
                            prefixes.add(relative)
    return [(relative, path) for relative, path in settings_files(root)
            if relative in prefixes or (relative.startswith('plugins/')
                and normalize(Path(relative).parts[1].removesuffix('.json')) in names)]


def check_name(name):
    if (not isinstance(name, str) or not name or len(name) > 180
            or name in ('.', '..') or name.endswith(('.', ' '))
            or re.search(r'[<>:"/\\|?*\x00-\x1f]', name)
            or name.split('.')[0].upper() in RESERVED_NAMES):
        raise ValueError('外掛名稱無效。')
    return name


def installed_plugins():
    from calibre.customize import PluginInstallationType
    from calibre.customize.ui import config, initialized_plugins, is_disabled, plugin_dir
    loaded = {p.name: p for p in initialized_plugins() if p.installation_type == PluginInstallationType.EXTERNAL}
    result = []
    for name, original_path in sorted(config['plugins'].items(), key=lambda item: item[0].casefold()):
        check_name(name)
        path = Path(plugin_dir) / (name + '.zip')
        if not path.is_file():
            path = Path(original_path)
        plugin = loaded.get(name)
        result.append({'name': name, 'version': list(plugin.version) if plugin else None,
                       'enabled': not is_disabled(name), 'path': str(path)})
    return result


def export_backup(destination, plugins, progress=None, settings_dir=None, customizations=None, builtin_states=None, selected_settings=False):
    destination = Path(destination)
    if not plugins:
        raise ValueError('目前沒有可匯出的第三方外掛。')
    if len(plugins) > MAX_PLUGINS:
        raise ValueError('外掛數量超過備份上限。')
    if destination.resolve() in {Path(p['path']).resolve() for p in plugins}:
        raise ValueError('備份檔不能覆蓋外掛安裝包。')
    if settings_dir is not None and destination.resolve().is_relative_to(Path(settings_dir).resolve()):
        raise ValueError('包含設定時，請將備份存到 calibre 設定資料夾以外。')
    fd, temporary = tempfile.mkstemp(prefix='.plugin-backup-', suffix='.zip', dir=destination.parent)
    os.close(fd)
    try:
        entries = []
        total = 0
        with ZipFile(temporary, 'w', compression=ZIP_DEFLATED) as z:
            for index, plugin in enumerate(plugins):
                name = check_name(plugin['name'])
                if progress:
                    progress(index, len(plugins), name)
                with Path(plugin['path']).open('rb') as f:
                    data = f.read(MAX_PACKAGE + 1)
                total += len(data)
                if len(data) > MAX_PACKAGE or total > MAX_TOTAL:
                    raise ValueError('外掛安裝包超過備份大小上限。')
                package = f'plugins/{index:04d}.zip'
                entries.append({'name': name, 'version': plugin['version'], 'enabled': plugin['enabled'],
                                'package': package, 'sha256': hashlib.sha256(data).hexdigest()})
                z.writestr(package, data)
            manifest = {'format': FORMAT, 'version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
                        'plugins': entries}
            if settings_dir is not None:
                settings, settings_size = [], 0
                for relative, path in (selected_settings_files(settings_dir, plugins) if selected_settings else settings_files(settings_dir)):
                    with path.open('rb') as f:
                        data = f.read(MAX_SETTING_FILE + 1)
                    settings_size += len(data)
                    if len(data) > MAX_SETTING_FILE or settings_size > MAX_SETTINGS_SIZE:
                        raise ValueError('設定資料超過備份大小上限。')
                    z.writestr('settings/' + relative, data)
                    settings.append({'path': relative, 'sha256': hashlib.sha256(data).hexdigest()})
                manifest['settings'] = {'files': settings, 'customizations': customizations or {}}
                if builtin_states is not None:
                    manifest['settings']['builtin_states'] = builtin_states
            z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8'))
        # Validate the completed archive before replacing any existing backup.
        inspect_backup(temporary)
        os.replace(temporary, destination)
        return entries
    finally:
        Path(temporary).unlink(missing_ok=True)


def inspect_backup(path):
    with nullcontext(path) if isinstance(path, ZipFile) else ZipFile(path) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(names)) or len(names) > MAX_PLUGINS + MAX_SETTINGS_FILES + 1:
            raise ValueError('備份含有重複或過多檔案。')
        info = z.getinfo('manifest.json')
        if info.file_size > 2 * 1024 * 1024:
            raise ValueError('備份清單過大。')
        manifest = json.loads(z.read(info))
        if not isinstance(manifest, dict) or manifest.get('format') != FORMAT or manifest.get('version') != 1:
            raise ValueError('這不是支援的 calibre 外掛備份格式。')
        entries = manifest.get('plugins')
        if not isinstance(entries, list) or not entries or len(entries) > MAX_PLUGINS:
            raise ValueError('備份的外掛清單無效或為空。')
        seen_names, packages = set(), set()
        total = 0
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError('外掛清單項目無效。')
            name = check_name(entry.get('name'))
            if name.casefold() in seen_names:
                raise ValueError('備份含有重複的外掛名稱。')
            seen_names.add(name.casefold())
            version = entry.get('version')
            if version is not None and (not isinstance(version, list) or not 1 <= len(version) <= 8
                    or any(type(v) is not int or v < 0 for v in version)):
                raise ValueError('外掛版本資料無效。')
            if type(entry.get('enabled')) is not bool:
                raise ValueError('外掛啟用狀態無效。')
            package = entry.get('package')
            if not isinstance(package, str) or not re.fullmatch(r'plugins/[0-9]{4}\.zip', package) or package in packages:
                raise ValueError('外掛安裝包路徑無效。')
            packages.add(package)
            item = z.getinfo(package)
            total += item.file_size
            if item.file_size > MAX_PACKAGE or total > MAX_TOTAL:
                raise ValueError('備份解壓後超過大小上限。')
            digest = entry.get('sha256')
            if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
                raise ValueError('外掛校驗資料無效。')
            data = z.read(item)
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError(f'「{name}」的安裝包校驗失敗。')
            # Inspect ZIP structure without executing plugin code.
            import io
            with ZipFile(io.BytesIO(data)) as plugin_zip:
                if '__init__.py' not in plugin_zip.namelist():
                    raise ValueError(f'「{name}」缺少外掛入口。')
                if sum(i.file_size for i in plugin_zip.infolist()) > MAX_PACKAGE:
                    raise ValueError(f'「{name}」解壓後超過大小上限。')
        settings = manifest.get('settings')
        settings_packages = set()
        if settings is not None:
            if (not isinstance(settings, dict) or not isinstance(settings.get('files'), list)
                    or len(settings['files']) > MAX_SETTINGS_FILES or not isinstance(settings.get('customizations'), dict)
                    or any(k not in {e['name'] for e in entries} or not isinstance(v, str) for k, v in settings['customizations'].items())):
                raise ValueError('設定備份清單無效。')
            states = settings.get('builtin_states', {'enabled': [], 'disabled': []})
            if (not isinstance(states, dict) or any(not isinstance(states.get(k), list)
                    or any(not isinstance(n, str) for n in states[k]) for k in ('enabled', 'disabled'))
                    or set(states['enabled']) & set(states['disabled'])):
                raise ValueError('內建外掛啟用狀態無效。')
            settings_size = 0
            for entry in settings['files']:
                if not isinstance(entry, dict):
                    raise ValueError('設定檔清單項目無效。')
                relative = entry.get('path')
                settings_target(Path.cwd(), relative)
                if relative.split('/')[0].lower() in SKIP_SETTINGS:
                    raise ValueError('設定備份包含不可還原的檔案。')
                if relative.lower().startswith('plugins/') and relative.count('/') == 1 and relative.lower().endswith('.zip'):
                    raise ValueError('設定檔不能包含外掛安裝包。')
                package = 'settings/' + relative
                if package.casefold() in settings_packages:
                    raise ValueError('設定備份含有重複路徑。')
                settings_packages.add(package.casefold())
                item = z.getinfo(package)
                settings_size += item.file_size
                if item.file_size > MAX_SETTING_FILE or settings_size > MAX_SETTINGS_SIZE:
                    raise ValueError('設定備份解壓後超過大小上限。')
                if hashlib.sha256(z.read(item)).hexdigest() != entry.get('sha256'):
                    raise ValueError(f'「{relative}」的設定檔校驗失敗。')
        expected_settings = {'settings/' + e['path'] for e in settings['files']} if settings else set()
        if set(names) != {'manifest.json', *packages, *expected_settings}:
            raise ValueError('備份含有清單以外的檔案。')
        return manifest


def restore_settings(archive, settings, root):
    """Restore files with rollback; keep this machine's library path and registry."""
    root = Path(root)
    temporary = Path(tempfile.mkdtemp(prefix='.plugin-backup-recovery-', dir=root))
    keep_recovery = False
    try:
        changes = []
        try:
            for index, entry in enumerate(settings['files']):
                relative = entry['path']
                target = settings_target(root, relative)
                data = archive.read('settings/' + relative)
                if relative in ('global.py.json', 'gui.json'):
                    incoming = json.loads(data)
                    current = json.loads(target.read_bytes()) if target.exists() else {}
                    for key in ('library_path', 'library_usage_stats', 'installation_uuid'):
                        incoming.pop(key, None)
                        if key in current:
                            incoming[key] = current[key]
                    data = json.dumps(incoming, ensure_ascii=False).encode('utf-8')
                old = Path(temporary) / str(index)
                existed = target.exists()
                if existed:
                    shutil.copyfile(target, old)
                target.parent.mkdir(parents=True, exist_ok=True)
                fd, staging = tempfile.mkstemp(prefix='.restore-', dir=target.parent)
                try:
                    with os.fdopen(fd, 'wb') as f:
                        f.write(data)
                    os.replace(staging, target)
                    changes.append((target, old, existed))
                finally:
                    Path(staging).unlink(missing_ok=True)
        except Exception as error:
            errors = []
            for target, old, existed in reversed(changes):
                try:
                    if existed:
                        shutil.copyfile(old, target)
                    else:
                        target.unlink(missing_ok=True)
                except Exception as rollback_error:
                    errors.append(str(rollback_error))
            if errors:
                keep_recovery = True
                (temporary / 'paths.json').write_text(json.dumps(
                    {old.name: str(target) for target, old, existed in changes if existed}, ensure_ascii=False), 'utf-8')
                raise RuntimeError(f'{error}；部分設定回復失敗，原檔保存在 {temporary}：' + '；'.join(errors)) from error
            raise
    finally:
        if not keep_recovery:
            shutil.rmtree(temporary)


def import_backup(path, progress=None, include_settings=False):
    """Run in a separate calibre process; preserve each existing package on failure."""
    from calibre.customize.ui import BLACKLISTED_PLUGINS, add_plugin, builtin_names, config, disable_plugin, enable_plugin, load_plugin, plugin_dir
    result = {'installed': [], 'failed': [], 'settings_restored': False}
    with tempfile.TemporaryDirectory(prefix='plugin-backup-') as temporary, ZipFile(path) as archive:
        manifest = inspect_backup(archive)
        entries = manifest['plugins']
        for index, entry in enumerate(entries):
            name = entry['name']
            if progress:
                progress(index, len(entries), name)
            package = Path(temporary) / 'incoming.zip'
            target = Path(plugin_dir) / (name + '.zip')
            previous = Path(temporary) / 'previous.zip'
            registry = dict(config['plugins'])
            disabled, enabled = set(config['disabled_plugins']), set(config['enabled_plugins'])
            had_target = target.is_file()
            changed = False
            try:
                package.write_bytes(archive.read(entry['package']))
                if had_target:
                    shutil.copyfile(target, previous)
                if name in BLACKLISTED_PLUGINS:
                    raise ValueError('此版本 calibre 已封鎖這支外掛。')
                plugin_class = load_plugin(str(package))
                if plugin_class.name != name or (entry['version'] is not None and list(plugin_class.version) != entry['version']):
                    raise ValueError('安裝包的名稱或版本與備份清單不符。')
                changed = True
                add_plugin(str(package))
                if entry['enabled']:
                    enable_plugin(name)
                else:
                    disable_plugin(name)
                result['installed'].append(name)
            except Exception as error:
                details = str(error) or type(error).__name__
                if changed:
                    try:
                        if had_target:
                            shutil.copyfile(previous, target)
                        else:
                            target.unlink(missing_ok=True)
                        config['plugins'] = registry
                        config['disabled_plugins'] = disabled
                        config['enabled_plugins'] = enabled
                    except Exception as rollback_error:
                        details += f'；回復原安裝包失敗：{rollback_error}'
                        # Keep a recovery copy outside the temporary directory.
                        if had_target and previous.is_file():
                            recovery = Path(plugin_dir) / (name + '.recovery.zip')
                            shutil.copyfile(previous, recovery)
                            details += f'；原安裝包保存在 {recovery}'
                result['failed'].append({'name': name, 'error': details})
        if include_settings and manifest.get('settings') and not result['failed']:
            previous_customizations = dict(config['plugin_customization'])
            previous_disabled, previous_enabled = set(config['disabled_plugins']), set(config['enabled_plugins'])
            try:
                from calibre.utils.config import config_dir
                customizations = dict(previous_customizations)
                for entry in entries:
                    customizations.pop(entry['name'], None)
                customizations.update(manifest['settings']['customizations'])
                config['plugin_customization'] = customizations
                states = manifest['settings'].get('builtin_states')
                if states is not None:
                    config['disabled_plugins'] = (previous_disabled - builtin_names) | (set(states['disabled']) & builtin_names)
                    config['enabled_plugins'] = (previous_enabled - builtin_names) | (set(states['enabled']) & builtin_names)
                restore_settings(archive, manifest['settings'], config_dir)
                result['settings_restored'] = True
            except Exception as error:
                details = str(error)
                try:
                    config['plugin_customization'] = previous_customizations
                    config['disabled_plugins'] = previous_disabled
                    config['enabled_plugins'] = previous_enabled
                except Exception as rollback_error:
                    details += f'；自訂字串回復失敗：{rollback_error}'
                result['failed'].append({'name': '設定還原', 'error': details})
    if progress:
        progress(len(entries), len(entries), '')
    return result


def worker():
    def progress(done, total, name):
        print('PLUGIN_BACKUP_PROGRESS ' + json.dumps([done, total, name], ensure_ascii=True), flush=True)
    try:
        if sys.argv[1] == 'export':
            from calibre.utils.config import config_dir
            from calibre.customize.ui import builtin_names, config
            plugins = installed_plugins()
            names = json.loads(sys.argv[5]) if len(sys.argv) > 5 else None
            if names is not None:
                if not isinstance(names, list) or not names or any(not isinstance(n, str) for n in names):
                    raise ValueError('請先勾選要匯出的外掛。')
                plugins = [p for p in plugins if p['name'] in names]
                if {p['name'] for p in plugins} != set(names):
                    raise ValueError('外掛清單已變更，請重新開啟備份視窗。')
            customizations = {p['name']: config['plugin_customization'][p['name']] for p in plugins if p['name'] in config['plugin_customization']}
            include = len(sys.argv) > 4 and sys.argv[4] == '1'
            states = {'enabled': sorted(set(config['enabled_plugins']) & builtin_names),
                      'disabled': sorted(set(config['disabled_plugins']) & builtin_names)}
            entries = export_backup(sys.argv[2], plugins, progress, config_dir if include else None, customizations, states if names is None else None, selected_settings=names is not None)
            report = {'exported': len(entries), 'installed': [], 'failed': [], 'settings_included': include}
        elif sys.argv[1] == 'import':
            report = import_backup(sys.argv[2], progress, len(sys.argv) > 4 and sys.argv[4] == '1')
        else:
            raise ValueError('不支援的操作。')
    except Exception as error:
        report = {'installed': [], 'failed': [{'name': '備份檔', 'error': str(error)}]}
    Path(sys.argv[3]).write_text(json.dumps(report, ensure_ascii=False), 'utf-8')
