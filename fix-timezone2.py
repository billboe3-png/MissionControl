import re
import os

broken_files = [
    "src/pages/automation/SchedulesPage.tsx",
    "src/pages/automation/TriggersPage.tsx",
    "src/pages/automation/ExecutionsPage.tsx",
    "src/pages/automation/ApprovalsPage.tsx",
    "src/pages/automation/AuditPage.tsx",
]

for rel_path in broken_files:
    full_path = f"/opt/MissionControl/frontend/{rel_path}"
    if not os.path.exists(full_path):
        print(f"SKIP {rel_path}: not found")
        continue
    
    with open(full_path, 'r') as f:
        content = f.read()
    
    # Fix broken import blocks caused by regex inserting into multi-line imports
    # Pattern: import { \nimport { formatDateTime } from "...";\n    name,
    content = re.sub(
        r'import \{\nimport \{ formatDateTime \} from "([^"]+)";\n    ([^}]+)\n\} from "([^"]+)";',
        r'import { formatDateTime } from "\1";\nimport {\n    \2\n} from "\3";',
        content
    )
    
    # Fix single-line import breakage: import { \nimport { formatDateTime } from "...";\n    name,
    content = re.sub(
        r'import \{\nimport \{ formatDateTime \} from "([^"]+)";\n    ([^,]+),',
        r'import { formatDateTime } from "\1";\nimport { \2,',
        content
    )
    
    with open(full_path, 'w') as f:
        f.write(content)
    print(f"FIXED {rel_path}")
