# ghost-config

Find configuration keys that are defined but never used, or referenced but never defined.

ghost-config scans configuration files and source code in a project, builds a set of declared configuration keys, extracts references from source, and reports mismatches. It helps remove stale settings, catch typos, and keep `.env.example` honest.

## Features

- Scans `.env`, JSON, and TOML configuration files.
- Recursively collects nested JSON/TOML keys as dotted paths.
- Extracts references from common patterns such as `os.getenv`, `process.env`, and `config.get`.
- Reports unused configuration keys and missing references.
- Supports text and JSON output.
- No runtime dependencies beyond the Python standard library.

## Install

```
python -m pip install .
```

Or run directly:

```
python -m ghost_config .
```

## Usage

```
ghost-config .
ghost-config scan . --format json
ghost-config . --fail-on any
```

Options:

- `root`: project directory to scan (default: current directory)
- `--config-dir`: directory containing configuration files
- `--source-dir`: directory containing source files
- `--format`: `text` or `json`
- `--fail-on`: `none`, `unused`, `missing`, or `any`

## License

MIT
