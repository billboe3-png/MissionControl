// ------------------------------------------------------------------ //
// Playbook Types                                                       //
// ------------------------------------------------------------------ //

export interface PlaybookCreateInput {
    name: string;
    description?: string;
    category?: string;
    tags?: string;
    enabled?: boolean;
    requires_approval?: boolean;
    auto_rollback?: boolean;
    timeout_seconds?: number;
    max_retries?: number;
    created_by?: string;
}

export interface PlaybookUpdateInput {
    name?: string;
    description?: string;
    category?: string;
    tags?: string;
    enabled?: boolean;
    requires_approval?: boolean;
    auto_rollback?: boolean;
    timeout_seconds?: number;
    max_retries?: number;
}

export interface PlaybookData {
    id: number;
    name: string;
    description: string | null;
    version: number;
    category: string | null;
    tags: string | null;
    enabled: boolean;
    requires_approval: boolean;
    auto_rollback: boolean;
    timeout_seconds: number;
    max_retries: number;
    created_by: string | null;
    created_at: string;
    updated_at: string;
}

export interface PlaybookListData {
    count: number;
    items: PlaybookData[];
}

// ------------------------------------------------------------------ //
// Step Types                                                           //
// ------------------------------------------------------------------ //

export interface PlaybookStepCreateInput {
    name: string;
    description?: string;
    step_type: string;
    provider?: string;
    command: string;
    target_host?: string;
    shell?: string;
    working_directory?: string;
    environment_variables?: string;
    timeout_seconds?: number;
    retry_count?: number;
    continue_on_failure?: boolean;
    rollback_command?: string;
    step_order?: number;
}

export interface PlaybookStepUpdateInput {
    name?: string;
    description?: string;
    step_type?: string;
    provider?: string;
    command?: string;
    target_host?: string;
    shell?: string;
    working_directory?: string;
    timeout_seconds?: number;
    retry_count?: number;
    continue_on_failure?: boolean;
    rollback_command?: string;
    step_order?: number;
}

export interface PlaybookStepData {
    id: number;
    playbook_id: number;
    name: string;
    description: string | null;
    step_type: string;
    provider: string;
    command: string;
    target_host: string | null;
    shell: string | null;
    working_directory: string | null;
    environment_variables: string | null;
    timeout_seconds: number;
    retry_count: number;
    continue_on_failure: boolean;
    rollback_command: string | null;
    step_order: number;
    created_at: string;
    updated_at: string;
}

export interface PlaybookStepListData {
    count: number;
    items: PlaybookStepData[];
}

// ------------------------------------------------------------------ //
// Variable Types                                                       //
// ------------------------------------------------------------------ //

export interface PlaybookVariableCreateInput {
    name: string;
    value?: string;
    variable_type?: string;
    description?: string;
    required?: boolean;
    sensitive?: boolean;
    default_value?: string;
}

export interface PlaybookVariableUpdateInput {
    name?: string;
    value?: string;
    variable_type?: string;
    description?: string;
    required?: boolean;
    sensitive?: boolean;
    default_value?: string;
}

export interface PlaybookVariableData {
    id: number;
    playbook_id: number;
    name: string;
    value: string | null;
    variable_type: string;
    description: string | null;
    required: boolean;
    sensitive: boolean;
    default_value: string | null;
    created_at: string;
    updated_at: string;
}

export interface PlaybookVariableListData {
    count: number;
    items: PlaybookVariableData[];
}

// ------------------------------------------------------------------ //
// Execution Types                                                      //
// ------------------------------------------------------------------ //

export interface PlaybookExecuteInput {
    mode?: string;
    triggered_by?: string;
    variables?: Record<string, string>;
}

export interface PlaybookExecutionData {
    id: number;
    playbook_id: number;
    status: string;
    mode: string;
    trigger_type: string;
    triggered_by: string | null;
    variables_used: string | null;
    steps_total: number;
    steps_completed: number;
    steps_failed: number;
    steps_skipped: number;
    output: string | null;
    error: string | null;
    rollback_status: string | null;
    rollback_output: string | null;
    approval_required: boolean;
    approval_status: string | null;
    duration_ms: number | null;
    started_at: string | null;
    completed_at: string | null;
    created_at: string;
}

export interface PlaybookExecutionListData {
    count: number;
    items: PlaybookExecutionData[];
}

export interface DryRunInput {
    variables?: Record<string, string>;
}

export interface DryRunData {
    execution_id: number;
    status: string;
    steps_validated: number;
    steps_total: number;
    output: string;
    warnings: string[];
    errors: string[];
}

export interface RollbackInput {
    reason?: string;
}

export interface RollbackData {
    execution_id: number;
    rollback_status: string;
    output: string | null;
    error: string | null;
}

// ------------------------------------------------------------------ //
// Execution Log Types                                                  //
// ------------------------------------------------------------------ //

export interface ExecutionLogData {
    id: number;
    execution_id: number;
    step_id: number | null;
    level: string;
    message: string;
    stdout: string | null;
    stderr: string | null;
    exit_code: number | null;
    duration_ms: number | null;
    timestamp: string;
}

export interface ExecutionLogListData {
    count: number;
    items: ExecutionLogData[];
}

// ------------------------------------------------------------------ //
// Approval Types                                                       //
// ------------------------------------------------------------------ //

export interface ApprovalWorkflowCreateInput {
    name: string;
    required_approvers?: number;
    approver_roles?: string;
    auto_approve_on_timeout?: boolean;
    timeout_minutes?: number;
    enabled?: boolean;
}

export interface ApprovalWorkflowUpdateInput {
    name?: string;
    required_approvers?: number;
    approver_roles?: string;
    auto_approve_on_timeout?: boolean;
    timeout_minutes?: number;
    enabled?: boolean;
}

export interface ApprovalWorkflowData {
    id: number;
    playbook_id: number;
    name: string;
    required_approvers: number;
    approver_roles: string | null;
    auto_approve_on_timeout: boolean;
    timeout_minutes: number;
    enabled: boolean;
    created_at: string;
    updated_at: string;
}

export interface ApprovalWorkflowListData {
    count: number;
    items: ApprovalWorkflowData[];
}

export interface ApprovalRequestData {
    id: number;
    execution_id: number;
    workflow_id: number;
    status: string;
    requested_by: string | null;
    approved_by: string | null;
    comments: string | null;
    requested_at: string;
    responded_at: string | null;
}

export interface ApprovalRequestListData {
    count: number;
    items: ApprovalRequestData[];
}

export interface ApprovalActionInput {
    approved_by: string;
    comments?: string;
}

// ------------------------------------------------------------------ //
// Audit Trail Types                                                    //
// ------------------------------------------------------------------ //

export interface AuditTrailData {
    id: number;
    entity_type: string;
    entity_id: number | null;
    action: string;
    actor: string | null;
    details: string | null;
    ip_address: string | null;
    timestamp: string;
}

export interface AuditTrailListData {
    count: number;
    items: AuditTrailData[];
}

// ------------------------------------------------------------------ //
// Schedule Types                                                       //
// ------------------------------------------------------------------ //

export interface PlaybookScheduleCreateInput {
    name: string;
    cron_expression: string;
    enabled?: boolean;
    variables_override?: string;
}

export interface PlaybookScheduleUpdateInput {
    name?: string;
    cron_expression?: string;
    enabled?: boolean;
    variables_override?: string;
}

export interface PlaybookScheduleData {
    id: number;
    playbook_id: number;
    name: string;
    cron_expression: string;
    enabled: boolean;
    variables_override: string | null;
    last_run: string | null;
    next_run: string | null;
    created_at: string;
    updated_at: string;
}

export interface PlaybookScheduleListData {
    count: number;
    items: PlaybookScheduleData[];
}

// ------------------------------------------------------------------ //
// Event Trigger Types                                                  //
// ------------------------------------------------------------------ //

export interface EventTriggerCreateInput {
    name: string;
    event_type: string;
    conditions?: string;
    enabled?: boolean;
}

export interface EventTriggerUpdateInput {
    name?: string;
    event_type?: string;
    conditions?: string;
    enabled?: boolean;
}

export interface EventTriggerData {
    id: number;
    playbook_id: number;
    name: string;
    event_type: string;
    conditions: string | null;
    enabled: boolean;
    last_triggered: string | null;
    trigger_count: number;
    created_at: string;
    updated_at: string;
}

export interface EventTriggerListData {
    count: number;
    items: EventTriggerData[];
}

// ------------------------------------------------------------------ //
// Dashboard Summary                                                    //
// ------------------------------------------------------------------ //

export interface AutomationSummaryData {
    total_playbooks: number;
    total_executions: number;
    running: number;
    completed: number;
    failed: number;
    pending_approvals: number;
    audit_entries: number;
}
