import zipfile
from pathlib import Path

bundle = Path('../.agents/agent-bundle-live.zip')
version_file = Path('../.agents/agent-bundle-live.version')
root = Path('agent')

if version_file.exists():
    current = version_file.read_text(encoding='utf-8').strip()
    try:
        if current.startswith('v'):
            current = current[1:]
        _major, minor, patch = current.split('.')
        build_num = int(minor, 10) * 1000 + int(patch, 10)
    except ValueError:
        build_num = 0
else:
    build_num = 0

build_num += 1
minor = build_num // 1000
patch = build_num % 1000
version_text = f'v0.{minor}.{patch}'

with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in root.rglob('*'):
        if f.is_file() and f.name != 'agent.py':
            arc = Path('agent') / f.relative_to(root)
            zf.write(f, arc)
version_file.write_text(version_text, encoding='utf-8')
print('built', bundle, bundle.stat().st_size, 'version', version_text)
