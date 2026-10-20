import argparse
import json
import sys

from .scanner import format_report, scan


def main(argv=None):
    parser = argparse.ArgumentParser(prog='ghost-config', description='Find unused or missing configuration keys.')
    parser.add_argument('root', nargs='?', default='.', help='project directory to scan')
    parser.add_argument('--config-dir', help='directory containing configuration files')
    parser.add_argument('--source-dir', help='directory containing source files')
    parser.add_argument('--format', choices=('text', 'json'), default='text', help='output format')
    parser.add_argument('--fail-on', choices=('none', 'unused', 'missing', 'any'), default='none', help='exit non-zero on selected issues')
    args = parser.parse_args(argv)

    result = scan(args.root, args.config_dir, args.source_dir)

    if args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print(format_report(result))

    has_unused = bool(result['unused'])
    has_missing = bool(result['missing'])

    if args.fail_on == 'unused' and has_unused:
        return 1
    if args.fail_on == 'missing' and has_missing:
        return 1
    if args.fail_on == 'any' and (has_unused or has_missing):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
