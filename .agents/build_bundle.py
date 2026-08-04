import zipfile
from pathlib import Path

bundle = Path('.agents/agent-bundle-live.zip')
root = Path('.agents/agent')
with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in root.rglob('*'):
        if f.is_file():
            arc = f.relative_to(root)
            zf.write(f, arc)
print('built', bundle, bundle.stat().st_size)
