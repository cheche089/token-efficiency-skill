#!/usr/bin/env python3
"""Budget checker for token efficiency. Tracks file-read budgets per turn."""

import json
import os
import sys
from datetime import datetime, timezone

MAX_FILES = 10
MAX_LINES = 5000
MAX_BYTES = 50 * 1024
MAX_FULL_SCANS_PER_10 = 1


def _budget_path():
    base = os.environ.get('TOKEN_CACHE_DIR') or os.environ.get('TEMP') or os.path.expanduser('~')
    d = os.path.join(base, 'codex-token-eff-cache')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, 'budget.json')


def read_budget(bp):
    if os.path.exists(bp):
        try:
            with open(bp, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, PermissionError):
            pass
    return {
        'session_id': datetime.now(timezone.utc).isoformat()[:19],
        'turn': 0,
        'current': {'files': 0, 'lines': 0, 'bytes': 0},
        'full_scans': {'count': 0, 'last_turn': 0},
        'history': [],
    }


def write_budget(bp, state):
    with open(bp, 'w') as f:
        json.dump(state, f, indent=2)


def new_turn(state):
    state['turn'] += 1
    state['current']['files'] = 0
    state['current']['lines'] = 0
    state['current']['bytes'] = 0
    return state


def main():
    if len(sys.argv) < 2:
        print('Usage:')
        print('  python budget_check.py new-turn')
        print('  python budget_check.py track <file> <lines> <bytes> [--full-scan]')
        print('  python budget_check.py check [--files N] [--lines N] [--bytes N]')
        print('  python budget_check.py status')
        sys.exit(1)

    bp = _budget_path()
    cmd = sys.argv[1]

    if cmd == 'new-turn':
        st = read_budget(bp)
        st = new_turn(st)
        write_budget(bp, st)
        print('[BUDGET] New turn ' + str(st['turn']) + ' - budgets reset')
        print('  files=0/' + str(MAX_FILES) + ' lines=0/' + str(MAX_LINES) + ' bytes=0/' + str(MAX_BYTES))

    elif cmd == 'track':
        st = read_budget(bp)
        filepath = sys.argv[2] if len(sys.argv) > 2 else 'unknown'
        lines_c = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        bytes_c = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        is_full = '--full-scan' in sys.argv

        st['current']['files'] += 1
        st['current']['lines'] += lines_c
        st['current']['bytes'] += bytes_c
        st['history'].append({
            'ts': datetime.now(timezone.utc).isoformat(),
            'turn': st['turn'],
            'file': filepath, 'lines': lines_c, 'bytes': bytes_c,
        })
        if len(st['history']) > 100:
            st['history'] = st['history'][-100:]
        if is_full:
            st['full_scans']['count'] += 1
            st['full_scans']['last_turn'] = st['turn']

        write_budget(bp, st)
        c = st['current']
        over = []
        if c['files'] > MAX_FILES:
            over.append('files ' + str(c['files']) + '/' + str(MAX_FILES))
        if c['lines'] > MAX_LINES:
            over.append('lines ' + str(c['lines']) + '/' + str(MAX_LINES))
        if c['bytes'] > MAX_BYTES:
            over.append('bytes ' + str(c['bytes']) + '/' + str(MAX_BYTES))
        print('[BUDGET] Tracked: ' + filepath + ' (' + str(lines_c) + ' lines, ' + str(bytes_c) + ' bytes)')
        print('  Current: files=' + str(c['files']) + '/' + str(MAX_FILES) + ' lines=' + str(c['lines']) + '/' + str(MAX_LINES) + ' bytes=' + str(c['bytes']) + '/' + str(MAX_BYTES))
        if over:
            print('  [BUDGET_OVER] ' + ', '.join(over) + ' - justify override')

    elif cmd == 'check':
        st = read_budget(bp)
        extra_files = int(sys.argv[sys.argv.index('--files') + 1]) if '--files' in sys.argv else 0
        extra_lines = int(sys.argv[sys.argv.index('--lines') + 1]) if '--lines' in sys.argv else 0
        extra_bytes = int(sys.argv[sys.argv.index('--bytes') + 1]) if '--bytes' in sys.argv else 0
        c = st['current']
        would = []
        if c['files'] + extra_files > MAX_FILES:
            would.append('files')
        if c['lines'] + extra_lines > MAX_LINES:
            would.append('lines')
        if c['bytes'] + extra_bytes > MAX_BYTES:
            would.append('bytes')
        print('[BUDGET:CHECK] Current: files=' + str(c['files']) + '/' + str(MAX_FILES) + ' lines=' + str(c['lines']) + '/' + str(MAX_LINES) + ' bytes=' + str(c['bytes']) + '/' + str(MAX_BYTES))
        if would:
            print('  Would exceed: ' + ', '.join(would))
            print('  -> Need [BUDGET_OVERRIDE] reason + estimate')
        else:
            print('  [BUDGET:OK] Within limits.')

    elif cmd == 'status':
        st = read_budget(bp)
        c = st['current']
        full_ok = True
        if st['full_scans']['count'] >= MAX_FULL_SCANS_PER_10:
            since = st['turn'] - st['full_scans']['last_turn']
            full_ok = since >= 10
        print('[BUDGET:STATUS] Turn ' + str(st['turn']))
        print('  This turn: files=' + str(c['files']) + '/' + str(MAX_FILES) + ' lines=' + str(c['lines']) + '/' + str(MAX_LINES) + ' bytes=' + str(c['bytes']) + '/' + str(MAX_BYTES))
        print('  Full scans: ' + str(st['full_scans']['count']) + ' (last turn ' + str(st['full_scans']['last_turn']) + ')')
        print('  Can full scan: ' + str(full_ok))

    else:
        print('[BUDGET:ERROR] Unknown command: ' + cmd)


if __name__ == '__main__':
    main()
