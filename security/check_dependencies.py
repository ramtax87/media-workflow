"""Fail closed if the stdlib-only dependency policy changes without review."""
import ast
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1]
pins = [line for line in (root / 'requirements.lock').read_text().splitlines()
        if line.strip() and not line.lstrip().startswith('#')]
if pins:
    raise SystemExit('Third-party dependencies added: configure pinned vulnerability auditing first.')
known = sys.stdlib_module_names
for base in (root / 'skills', root / 'tests', root / 'security', root / 'tools'):
    if not base.exists():
        continue
    for path in base.rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or '']
            else:
                continue
            for name in names:
                if name.split('.')[0] not in known:
                    raise SystemExit(f'Review dependency import in {path.relative_to(root)}: {name}')
print('Dependency boundary passed: no third-party runtime/test dependencies declared or directly imported.')
