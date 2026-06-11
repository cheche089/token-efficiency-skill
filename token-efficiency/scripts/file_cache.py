#!/usr/bin/env python3
"""File cache manager for token efficiency. Tracks hashes, summaries, and read counts."""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone


def _get_cache_dir():
    """Return a guaranteed-writable directory for cache files."""
    base = os.environ.get('TOKEN_CACHE_DIR') or os.environ.get('TEMP') or os.path.expanduser('~')
    d = os.path.join(base, 'codex-token-eff-cache')
    os.makedirs(d, exist_ok=True)
    return d


def _cache_path():
    return os.path.join(_get_cache_dir(), 'file-cache.json')


def file_hash(path):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        return None


def read_cache(cache_path):
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, PermissionError):
            return {'files': {}, 'structure': {}}
    return {'files': {}, 'structure': {}}


def write_cache(cache_path, cache):
    d = os.path.dirname(cache_path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def check_file(cache, path):
    if path not in cache.get('files', {}):
        return 'MISS', None
    entry = cache['files'][path]
    current_hash = file_hash(path)
    if current_hash is None:
        return 'ERROR', entry
    if current_hash == entry.get('hash'):
        return 'HIT', entry
    return 'MODIFIED', entry


def add_or_update(cache, path, summary='', key_findings=None, imports=None):
    h = file_hash(path)
    if h is None:
        return False
    try:
        mtime = os.path.getmtime(path)
        mtime_iso = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        size = os.path.getsize(path)
    except OSError:
        mtime_iso = 'unknown'
        size = 0
    if 'files' not in cache:
        cache['files'] = {}
    old = cache['files'].get(path, {})
    cache['files'][path] = {
        'hash': h, 'size': size, 'mtime': mtime_iso,
        'summary': summary or old.get('summary', ''),
        'key_findings': key_findings or old.get('key_findings', []),
        'imports': imports or old.get('imports', []),
        'last_read': datetime.now(timezone.utc).isoformat(),
        'read_count': old.get('read_count', 0) + 1,
    }
    return True


def evict_deleted(cache):
    if 'files' not in cache:
        return []
    to_evict = [p for p in cache['files'] if not os.path.exists(p)]
    for p in to_evict:
        del cache['files'][p]
    return to_evict


def main():
    if len(sys.argv) < 2:
        print('Usage:')
        print('  python file_cache.py check <path>')
        print('  python file_cache.py update <path> [--summary s] [--findings a|b|c]')
        print('  python file_cache.py show')
        print('  python file_cache.py evict')
        sys.exit(1)

    cmd = sys.argv[1]
    cp = _cache_path()

    if cmd == 'check':
        filepath = sys.argv[2] if len(sys.argv) > 2 else '.'
        cache = read_cache(cp)
        status, entry = check_file(cache, filepath)
        if status == 'HIT':
            print('[CACHE:HIT] ' + filepath)
            print('  Hash: ' + entry['hash'][:12] + '...')
            print('  Summary: ' + entry.get('summary', 'N/A'))
            print('  Read count: ' + str(entry.get('read_count', 0)))
            kf = entry.get('key_findings', [])
            if kf:
                print('  Key findings: ' + ', '.join(kf))
        elif status == 'MODIFIED':
            print('[CACHE:MISS] ' + filepath + ' - hash changed')
            print('  Old: ' + entry['hash'][:12] + '...')
        else:
            print('[CACHE:MISS] ' + filepath + ' - not in cache')

    elif cmd == 'update':
        filepath = sys.argv[2] if len(sys.argv) > 2 else '.'
        summary = ''
        key_findings = []
        if '--summary' in sys.argv:
            i = sys.argv.index('--summary')
            if i + 1 < len(sys.argv):
                summary = sys.argv[i + 1]
        if '--findings' in sys.argv:
            i = sys.argv.index('--findings')
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                key_findings = [f.strip() for f in sys.argv[i + 1].split('|')]
        cache = read_cache(cp)
        if add_or_update(cache, filepath, summary=summary, key_findings=key_findings):
            write_cache(cp, cache)
            print('[CACHE:UPDATED] ' + filepath)
        else:
            print('[CACHE:ERROR] Could not update ' + filepath)

    elif cmd == 'show':
        cache = read_cache(cp)
        files = cache.get('files', {})
        if not files:
            print('[CACHE] Empty.')
        else:
            print('[CACHE] ' + str(len(files)) + ' files tracked:')
            for p, e in sorted(files.items()):
                print('  ' + p + ' [' + e.get('hash', '?')[:8] + '] count=' + str(e.get('read_count', 0)))

    elif cmd == 'evict':
        cache = read_cache(cp)
        evicted = evict_deleted(cache)
        if evicted:
            write_cache(cp, cache)
            print('[CACHE:EVICTED] ' + str(len(evicted)) + ' files removed')
        else:
            print('[CACHE] No stale entries.')

    else:
        print('[CACHE:ERROR] Unknown command: ' + cmd)


if __name__ == '__main__':
    main()
