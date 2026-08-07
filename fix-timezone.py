import re
import os

TZ_IMPORT = 'import { formatDateTime } from "../utils/dateFormat";'

pages_to_patch = [
    "src/pages/agents/AgentRemoteTargetsTab.tsx",
    "src/pages/agents/TopologyPage.tsx",
    "src/pages/agents/AgentDetailPage.tsx",
    "src/pages/projects/ProjectsPage.tsx",
    "src/pages/unifi/ControllersPage.tsx",
    "src/pages/unifi/AlertsPage.tsx",
    "src/pages/zabbix/ProblemsPage.tsx",
    "src/pages/zabbix/EventsPage.tsx",
    "src/pages/zabbix/OverviewPage.tsx",
    "src/pages/resume/ResumesPage.tsx",
    "src/pages/veeam/SessionsPage.tsx",
    "src/pages/remote/CommandCenterPage.tsx",
    "src/pages/remote/HistoryPage.tsx",
    "src/pages/remote/TimelinePage.tsx",
    "src/pages/monitoring/ZabbixServersPage.tsx",
    "src/pages/automation/SchedulesPage.tsx",
    "src/pages/automation/ExecutionsPage.tsx",
    "src/pages/automation/TriggersPage.tsx",
    "src/pages/automation/ApprovalsPage.tsx",
    "src/pages/automation/AuditPage.tsx",
    "src/pages/settings/IntegrationsPage.tsx",
    "src/pages/hyperv/VirtualMachinesPage.tsx",
    "src/pages/hyperv/CheckpointsPage.tsx",
    "src/pages/agents/AgentsOverviewPage.tsx",
]

replacements = [
    # Common patterns
    (r'new Date\(([^)]+)\)\.toLocaleString\(\)', r'formatDateTime(\1)'),
    (r'new Date\(([^)]+)\)\.toLocaleDateString\(\)', r'formatDateTime(\1)'),
    (r'new Date\(([^)]+)\)\.toLocaleTimeString\(\)', r'formatDateTime(\1)'),
]

for rel_path in pages_to_patch:
    full_path = f"/opt/MissionControl/frontend/{rel_path}"
    if not os.path.exists(full_path):
        print(f"SKIP {rel_path}: not found")
        continue
    
    with open(full_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # Add import if not present
    if 'formatDateTime' not in content:
        # Determine relative import path
        depth = rel_path.count('/') - 1  # pages/ is one level
        import_path = '../' * depth + 'utils/dateFormat'
        import_line = f'import {{ formatDateTime }} from "{import_path}";'
        
        # Insert after last import
        lines = content.split('\n')
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import '):
                last_import_idx = i
        lines.insert(last_import_idx + 1, import_line)
        content = '\n'.join(lines)
    
    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"PATCHED {rel_path}")
    else:
        print(f"NO CHANGE {rel_path}")
