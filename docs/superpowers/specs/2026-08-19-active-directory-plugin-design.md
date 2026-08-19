# Active Directory Plugin SSH-Relay Integration Design

**Date**: 2026-08-19
**Status**: Approved (Draft)

## Problem Statement
The Active Directory dashboard currently falls back to mock data or fails to display inventory because:
1. Integration profile ID 4 ("KG Active Directory") is disabled (`enabled=f`).
2. Agent 1 (`CORHQROBERTB`) reports `active_directory: {available: false}` in inventory.
3. `.agents/agent/plugins/active_directory_plugin.py` relies on `ldap3` (not bundled in agent dependencies) and local environment variables.
4. Backend `AgentActiveDirectoryProvider` returns dict shapes incompatible with `ADSummaryResponse`, `ADUsersResponse`, `ADGroupsResponse`, and `ADDevicesResponse` schemas, causing validation and display issues.

## Solution Overview
Re-architect the Active Directory plugin to use the established **SSH relay pattern** (used by Veeam and Hyper-V):
1. **Agent**: Relays PowerShell ActiveDirectory module cmdlets to domain controller `CORHQDC01` (`192.168.10.15`, target ID 1) over SSH.
2. **Agent Dispatch**: Route `active_directory` namespace commands through `edge_core.py` to the plugin.
3. **Backend Provider**: Fix `AgentActiveDirectoryProvider` output shapes to match Pydantic schemas and route write operations through `AgentCommand` queue to the agent.
4. **Database**: Enable integration profile ID 4 in PostgreSQL.

---

## Technical Specifications

### 1. Agent Plugin (`.agents/agent/plugins/active_directory_plugin.py`)
- **Target Resolution**: Reads `remote_targets` from context filtered for `active_directory` in `target_plugins`.
- **Inventory Collection (`collect_inventory`)**:
  - Connects to target ID 1 (`CORHQDC01`) via `remote_manager.execute_on_target`.
  - Runs PowerShell scripts:
    - Domain/Forest info: `Get-ADDomain`, `Get-ADForest`, `Get-ADDomainController`
    - Users: `Get-ADUser -Filter * -Properties sAMAccountName, displayName, mail, department, title, Enabled, DistinguishedName`
    - Groups: `Get-ADGroup -Filter * -Properties Name, Description`
    - Computers: `Get-ADComputer -Filter * -Properties Name, DNSHostName, OperatingSystem`
    - Health/Replication: `Get-ADReplicationPartner` or `repadmin /replsummary`
  - Returns structured inventory JSON:
    ```json
    {
      "available": true,
      "domain": {"name": "kg.local", "base_dn": "DC=kg,DC=local"},
      "forest": "kg.local",
      "domain_controllers": ["CORHQDC01.kg.local"],
      "users": [
        {
          "sam_account_name": "administrator",
          "display_name": "Administrator",
          "email": "admin@kg.local",
          "department": "IT",
          "title": "Domain Admin",
          "enabled": true,
          "distinguished_name": "CN=Administrator,CN=Users,DC=kg,DC=local"
        }
      ],
      "groups": [
        {"name": "Domain Admins", "description": "Designated administrators of the domain"}
      ],
      "devices": [
        {"name": "CORHQDC01", "dns_name": "CORHQDC01.kg.local", "os_version": "Windows Server 2022 DataCenter"}
      ],
      "health": {
        "status": "healthy",
        "replication": {"status": "healthy", "pending_replications": 0, "failed_replications": 0}
      }
    }
    ```

- **Command Execution (`execute_command`)**:
  - Implements handlers:
    - `test_connection`: verifies AD connection
    - `reset-password`: `Set-ADAccountPassword`
    - `unlock`: `Unlock-ADAccount`
    - `enable`: `Enable-ADAccount`
    - `disable`: `Disable-ADAccount`
    - `rename`: `Set-ADUser -DisplayName ...`
    - `get-user-groups`: `Get-ADPrincipalGroupMembership`
    - `add-to-group`: `Add-ADGroupMember`
    - `remove-from-group`: `Remove-ADGroupMember`

### 2. Edge Core Dispatch (`.agents/agent/edge_core.py`)
- Update `_execute_remote_execute`:
  ```python
  if namespace == "active_directory":
      plugin_result = await self._plugin_manager.execute_plugin_command(
          "active_directory", op or "", params
      )
      ok = bool(plugin_result.get("success", False))
      return {
          "success": ok,
          "stdout": _json.dumps(plugin_result),
          "stderr": plugin_result.get("error") or plugin_result.get("stderr") or "",
          "exit_code": 0 if ok else 1,
      }
  ```

### 3. Backend Provider (`backend/app/providers/identity/agent_ad_provider.py`)
- Fix response schemas:
  - `get_summary()`: Returns `{"connected": True, "domain": {"name": ..., "base_dn": ...}, "user_count": ..., "group_count": ..., "computer_count": ...}`.
  - `get_users()`: Returns `{"connected": True, "users": [...], "total_count": len(users)}`.
  - `get_groups()`: Returns `{"connected": True, "groups": [...], "total_count": len(groups)}`.
  - `get_devices()`: Returns `{"connected": True, "devices": [...], "total_count": len(devices)}`.
  - `get_health()`: Returns `{"connected": True, "status": "healthy", "replication": {...}}`.
- Implement write operations:
  - Create `AgentSshExecutor` queue dispatch using `namespace: "active_directory"` for reset password, unlock, enable, disable, rename, group membership operations.

### 4. Database Integration Profile
- Enable AD integration profile ID 4: `UPDATE integration_profiles SET enabled = true WHERE id = 4;`

---

## Verification Plan
1. **Agent Unit / Integration Tests**:
   - Verify `active_directory_plugin.py` handles SSH relay and parses JSON response from `remote_manager.execute_on_target`.
2. **Backend Unit Tests**:
   - Run `pytest tests/test_identity_providers.py` and `pytest tests/test_identity_service.py` to ensure schema compatibility and mock safety.
3. **End-to-End Verification**:
   - Build agent bundle `v0.0.16`.
   - Verify agent pulls new bundle and updates inventory.
   - Verify `/api/v1/identity/ad/summary`, `/users`, `/groups`, `/devices`, `/health` return real data from CORHQDC01.
