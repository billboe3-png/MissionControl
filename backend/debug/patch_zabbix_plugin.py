from pathlib import Path
import os

win_base = os.environ.get('MC_PATCH_BASE') or r'C:\MissionControlAgent\agent'
base = Path(win_base)
plugin = base / 'plugins' / 'zabbix_plugin.py'
if not plugin.exists():
    raise SystemExit('plugin file not found: ' + str(plugin))

text = plugin.read_text(encoding='utf-8')
old = '            result = await client.post(url, json=payload)'
new = """            logger.debug('ZABBIX POST %s payload keys=%s', url, sorted((payload or {}).keys()))
            result = await client.post(url, json=payload)
            logger.debug('ZABBIX response status=%s body=%r', result.status_code, result.text[:400])"""
if old not in text:
    raise SystemExit('target snippet not found in zabbix_plugin.py; already patched or different agent version')
plugin.write_text(text.replace(old, new, 1), encoding='utf-8')
print('patched', plugin)
