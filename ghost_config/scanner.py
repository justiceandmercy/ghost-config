from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

SKIP_DIRS = {'.git', 'node_modules', '__pycache__', 'dist', 'build', '.venv', 'venv', '.tox'}


def _skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _walk(root: Path):
    for path in root.rglob('*'):
        if path.is_file() and not _skip(path):
            yield path
    for path in root.rglob('.env*'):
        if path.is_file() and not _skip(path):
            yield path


def is_config_path(path: Path) -> bool:
    name = path.name.lower()
    return name == '.env' or name.startswith('.env.') or path.suffix.lower() in {'.json', '.toml'}


def find_config_files(root: Path) -> list[Path]:
    return sorted({path for path in _walk(root) if is_config_path(path)})


def find_source_files(root: Path) -> list[Path]:
    files = set()
    for path in _walk(root):
        if path.suffix.lower() in {'.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.java', '.rb', '.php', '.c', '.cpp', '.cs', '.sh', '.yaml', '.yml'}:
            if not is_config_path(path):
                files.add(path)
    return sorted(files)


def _walk_mapping(obj, prefix='', keys=None):
    if keys is None:
        keys = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            name = f'{prefix}.{key}' if prefix else str(key)
            keys.add(name)
            _walk_mapping(value, name, keys)
    elif isinstance(obj, list):
        for item in obj:
            _walk_mapping(item, prefix, keys)
    return keys


def load_config_keys(path: Path) -> set[str]:
    keys = set()
    name = path.name.lower()
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return keys

    if name == '.env' or name.startswith('.env.'):
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('export '):
                line = line[7:].strip()
            if '=' in line:
                key = line.split('=', 1)[0].strip()
            else:
                key = line
            if key and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
                keys.add(key)
        return keys

    if path.suffix.lower() == '.json':
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return keys
        return _walk_mapping(data)

    if path.suffix.lower() == '.toml':
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            return keys
        return _walk_mapping(data)

    return keys


Q = '"' + "'"
REF_PATTERNS = [
    re.compile('os[.]getenv[(][ ]*[' + Q + ']([A-Za-z0-9_.-]+)[' + Q + ']'),
    re.compile('os[.]environ[[][ ]*[' + Q + ']([A-Za-z0-9_.-]+)[' + Q + ']'),
    re.compile('os[.]environ[.]get[(][ ]*[' + Q + ']([A-Za-z0-9_.-]+)[' + Q + ']'),
    re.compile('process[.]env[.]([A-Za-z_][A-Za-z0-9_]*)'),
    re.compile('process[.]env[[][ ]*[' + Q + ']([A-Za-z0-9_.-]+)[' + Q + ']'),
    re.compile('getenv[(][ ]*[' + Q + ']([A-Za-z0-9_.-]+)[' + Q + ']'),
    re.compile('[.]get[(][ ]*[' + Q + ']([A-Za-z0-9_.-]+)[' + Q + ']'),
    re.compile('(?:config|settings|conf|cfg|env)[[][ ]*[' + Q + ']([A-Za-z0-9_.-]+)[' + Q + ']'),
]


def extract_references(text: str) -> set[str]:
    references = set()
    for pattern in REF_PATTERNS:
        references.update(pattern.findall(text))
    return references


def _occurs(key: str, text: str) -> bool:
    return re.search('(?<![A-Za-z0-9_.-])' + re.escape(key) + '(?![A-Za-z0-9_.-])', text) is not None


def scan(root, config_dir=None, source_dir=None):
    root_path = Path(root)
    cfg_root = Path(config_dir) if config_dir else root_path
    src_root = Path(source_dir) if source_dir else root_path

    config_files = find_config_files(cfg_root)
    keys = set()
    for path in config_files:
        keys.update(load_config_keys(path))

    source_files = find_source_files(src_root)
    source_texts = []
    references = set()
    for path in source_files:
        try:
            text = path.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        source_texts.append(text)
        references.update(extract_references(text))

    joined = '\n'.join(source_texts)
    unused = sorted(key for key in keys if not _occurs(key, joined))
    missing = sorted(reference for reference in references if reference not in keys)

    return {
        'root': str(root_path),
        'config_files': [str(path) for path in config_files],
        'source_files': [str(path) for path in source_files],
        'keys': sorted(keys),
        'references': sorted(references),
        'unused': unused,
        'missing': missing,
    }


def format_report(result) -> str:
    lines = []
    lines.append('ghost-config scan')
    lines.append(f"root: {result['root']}")
    lines.append(f"config keys: {len(result['keys'])}; references: {len(result['references'])}")
    lines.append(f"config files: {len(result['config_files'])}; source files: {len(result['source_files'])}")
    lines.append('')
    if result['unused']:
        lines.append('Unused config keys:')
        lines.extend(f"  - {key}" for key in result['unused'])
    else:
        lines.append('No unused config keys.')
    lines.append('')
    if result['missing']:
        lines.append('Missing config keys:')
        lines.extend(f"  - {key}" for key in result['missing'])
    else:
        lines.append('No missing config keys.')
    return '\n'.join(lines)
