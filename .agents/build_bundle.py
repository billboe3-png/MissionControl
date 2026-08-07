import zipfile
from pathlib import Path
import shutil

bundle_dir = Path('.')
version_file = bundle_dir / 'agent-bundle-live.version'
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

versioned_bundle = bundle_dir / f'agent-bundle-{version_text}.zip'
with zipfile.ZipFile(versioned_bundle, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in root.rglob('*'):
        if f.is_file():
            arc = Path('agent') / f.relative_to(root)
            zf.write(f, arc)

live_bundle = bundle_dir / 'agent-bundle-live.zip'
if live_bundle.exists():
    live_bundle.unlink()
shutil.copy2(versioned_bundle, live_bundle)

version_file.write_text(version_text, encoding='utf-8')
print('built', versioned_bundle.name, versioned_bundle.stat().st_size, 'version', version_text)
print('live:', live_bundle.name, live_bundle.stat().st_size)
