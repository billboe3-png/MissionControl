import re
import os

broken_files = [
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
    "src/pages/hyperv/VirtualMachinesPage.tsx",
    "src/pages/hyperv/CheckpointsPage.tsx",
    "src/pages/settings/IntegrationsPage.tsx",
]

for rel_path in broken_files:
    full_path = f"/opt/MissionControl/frontend/{rel_path}"
    if not os.path.exists(full_path):
        print(f"SKIP {rel_path}: not found")
        continue
    
    with open(full_path, 'r') as f:
        lines = f.readlines()
    
    # Find all import { blocks and fix broken ones
    new_lines = []
    i = 0
    fixed = False
    while i < len(lines):
        line = lines[i]
        
        # Pattern: import {\nimport { formatDateTime } from "...";
        if line.strip() == 'import {' and i + 1 < len(lines):
            next_line = lines[i + 1]
            if next_line.strip().startswith('import { formatDateTime }'):
                # Skip the broken inner import
                i += 1
                # Insert formatDateTime import BEFORE this block
                import_line = lines[i]
                new_lines.append(import_line)
                fixed = True
                i += 1
                continue
        
        # Pattern: import { formatDateTime } from "...";\n    name,
        if line.strip().startswith('import { formatDateTime } from') and i + 1 < len(lines):
            import_line = line
            next_line = lines[i + 1]
            if next_line.strip().startswith('import {') or next_line.strip().startswith('import {'):
                # This is a standalone line before another import block - keep it
                new_lines.append(import_line)
                i += 1
                continue
            elif next_line.strip().startswith('    ') or next_line.strip().startswith('\t'):
                # This is indented content that should be part of the next block
                # Skip this line and let the next iteration handle it
                i += 1
                continue
        
        new_lines.append(line)
        i += 1
    
    content = ''.join(new_lines)
    
    # Also fix: standalone import { formatDateTime } followed by another import block
    # that should be merged
    content = re.sub(
        r'import \{ formatDateTime \} from "([^"]+)";\nimport \{\n    ([^}]+)\n\} from "([^"]+)";',
        r'import { formatDateTime } from "\1";\nimport {\n    \2\n} from "\3";',
        content
    )
    
    if content != ''.join(lines):
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"FIXED {rel_path}")
    else:
        print(f"OK {rel_path}")
