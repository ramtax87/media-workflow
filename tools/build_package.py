"""Build a private install ZIP from a fixed source allowlist, never working jobs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

FILES = ('plugin.json', 'README.md', 'INSTALL.md', 'AGENTS.md', 'requirements.lock',
         '.agents/plugins/marketplace.json')
DIRECTORIES = ('skills', 'templates', 'docs', 'security', 'tools', 'tests')


def build(root: Path, output: Path) -> dict:
    root = root.resolve()
    manifest = json.loads((root / 'plugin.json').read_text(encoding='utf-8'))
    paths = [root / name for name in FILES]
    for directory in DIRECTORIES:
        paths.extend(p for p in (root / directory).rglob('*') if p.is_file() or p.is_symlink())
    selected = []
    for path in sorted(set(paths)):
        relative = path.relative_to(root)
        if any(part.startswith('.') or part == '__pycache__' for part in relative.parts):
            if relative.as_posix() != '.agents/plugins/marketplace.json':
                continue
        if path.suffix in ('.pyc', '.pyo'):
            continue
        if path.is_symlink() or root not in path.resolve().parents:
            raise ValueError(f'Package path escapes source tree: {relative}')
        if not path.is_file():
            raise ValueError(f'Missing package file: {relative}')
        selected.append((path, relative.as_posix()))
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError('Archive already exists; choose a new output or remove that exact old archive.')
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path, name in selected:
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return {'path': str(output), 'version': manifest['version'], 'files': len(selected),
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    version = json.loads((root / 'plugin.json').read_text())['version']
    output = args.output or root / 'dist' / f'media-workflow-{version}.zip'
    print(json.dumps(build(root, output), indent=2))


if __name__ == '__main__':
    main()
