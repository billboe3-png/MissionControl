const API = "/api/v1/automation";

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail;
        throw new Error(detail ?? `Request failed (${response.status})`);
    }
    if (response.status === 204) {
        return undefined as T;
    }
    return response.json();
}

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

// ------------------------------------------------------------------ //
// API Client                                                            //
// ------------------------------------------------------------------ //

export const automationApi = {
    // -- Dashboard --
    async getSummary(): Promise<AutomationSummaryData> {
        const response = await fetch(`${API}/dashboard`);
        return handleResponse(response);
    },

    // -- Playbooks --
    async listPlaybooks(
        search?: string,
        category?: string,
    ): Promise<PlaybookListData> {
        const params = new URLSearchParams();
        if (search) params.set("search", search);
        if (category) params.set("category", category);
        const qs = params.toString();
        const response = await fetch(
            `${API}/playbooks${qs ? `?${qs}` : ""}`
        );
        return handleResponse(response);
    },

    async getPlaybook(id: number): Promise<PlaybookData> {
        const response = await fetch(`${API}/playbooks/${id}`);
        return handleResponse(response);
    },

    async createPlaybook(
        data: PlaybookCreateInput,
    ): Promise<PlaybookData> {
        const response = await fetch(`${API}/playbooks`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse(response);
    },

    async updatePlaybook(
        id: number,
        data: PlaybookUpdateInput,
    ): Promise<PlaybookData> {
        const response = await fetch(`${API}/playbooks/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse(response);
    },

    async deletePlaybook(id: number): Promise<void> {
        const response = await fetch(`${API}/playbooks/${id}`, {
            method: "DELETE",
        });
        return handleResponse(response);
    },

    // -- Steps --
    async listSteps(
        playbookId: number,
    ): Promise<PlaybookStepListData> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/steps`
        );
        return handleResponse(response);
    },

    async createStep(
        playbookId: number,
        data: PlaybookStepCreateInput,
    ): Promise<PlaybookStepData> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/steps`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    async updateStep(
        stepId: number,
        data: PlaybookStepUpdateInput,
    ): Promise<PlaybookStepData> {
        const response = await fetch(`${API}/steps/${stepId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse(response);
    },

    async deleteStep(stepId: number): Promise<void> {
        const response = await fetch(`${API}/steps/${stepId}`, {
            method: "DELETE",
        });
        return handleResponse(response);
    },

    // -- Variables --
    async listVariables(
        playbookId: number,
    ): Promise<PlaybookVariableListData> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/variables`
        );
        return handleResponse(response);
    },

    async createVariable(
        playbookId: number,
        data: PlaybookVariableCreateInput,
    ): Promise<PlaybookVariableData> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/variables`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    async updateVariable(
        variableId: number,
        data: PlaybookVariableUpdateInput,
    ): Promise<PlaybookVariableData> {
        const response = await fetch(
            `${API}/variables/${variableId}`,
            {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    async deleteVariable(variableId: number): Promise<void> {
        const response = await fetch(
            `${API}/variables/${variableId}`,
            { method: "DELETE" }
        );
        return handleResponse(response);
    },

    // -- Executions --
    async listExecutions(
        playbookId?: number,
        statusFilter?: string,
    ): Promise<PlaybookExecutionListData> {
        const params = new URLSearchParams();
        if (playbookId) params.set("playbook_id", String(playbookId));
        if (statusFilter) params.set("status", statusFilter);
        const qs = params.toString();
        const response = await fetch(
            `${API}/executions${qs ? `?${qs}` : ""}`
        );
        return handleResponse(response);
    },

    async getExecution(
        id: number,
    ): Promise<PlaybookExecutionData> {
        const response = await fetch(`${API}/executions/${id}`);
        return handleResponse(response);
    },

    async executePlaybook(
        playbookId: number,
        data: PlaybookExecuteInput,
    ): Promise<PlaybookExecutionData> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/execute`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    async dryRun(
        playbookId: number,
        data: DryRunInput,
    ): Promise<DryRunData> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/dry-run`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    async rollback(
        executionId: number,
        data: RollbackInput,
    ): Promise<RollbackData> {
        const response = await fetch(
            `${API}/executions/${executionId}/rollback`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    // -- Execution Logs --
    async listExecutionLogs(
        executionId: number,
    ): Promise<ExecutionLogListData> {
        const response = await fetch(
            `${API}/executions/${executionId}/logs`
        );
        return handleResponse(response);
    },

    // -- Approval Workflows --
    async listWorkflows(
        playbookId: number,
    ): Promise<ApprovalWorkflowListData> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/workflows`
        );
        return handleResponse(response);
    },

    async createWorkflow(
        playbookId: number,
        data: ApprovalWorkflowCreateInput,
    ): Promise<ApprovalWorkflowData> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/workflows`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    async deleteWorkflow(workflowId: number): Promise<void> {
        const response = await fetch(
            `${API}/workflows/${workflowId}`,
            { method: "DELETE" }
        );
        return handleResponse(response);
    },

    // -- Approval Requests --
    async listPendingApprovals(): Promise<ApprovalRequestListData> {
        const response = await fetch(`${API}/approvals/pending`);
        return handleResponse(response);
    },

    async listExecutionApprovals(
        executionId: number,
    ): Promise<ApprovalRequestListData> {
        const response = await fetch(
            `${API}/executions/${executionId}/approvals`
        );
        return handleResponse(response);
    },

    async approveRequest(
        requestId: number,
        data: ApprovalActionInput,
    ): Promise<ApprovalRequestData> {
        const response = await fetch(
            `${API}/approvals/${requestId}/approve`,
            {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    async rejectRequest(
        requestId: number,
        data: ApprovalActionInput,
    ): Promise<ApprovalRequestData> {
        const response = await fetch(
            `${API}/approvals/${requestId}/reject`,
            {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    // -- Audit Trail --
    async listAuditTrail(
        entityType?: string,
        action?: string,
    ): Promise<AuditTrailListData> {
        const params = new URLSearchParams();
        if (entityType) params.set("entity_type", entityType);
        if (action) params.set("action", action);
        const qs = params.toString();
        const response = await fetch(
            `${API}/audit${qs ? `?${qs}` : ""}`
        );
        return handleResponse(response);
    },

    // -- Schedules --
    async listSchedules(
        playbookId?: number,
    ): Promise<PlaybookScheduleListData> {
        const params = new URLSearchParams();
        if (playbookId) params.set("playbook_id", String(playbookId));
        const qs = params.toString();
        const response = await fetch(
            `${API}/schedules${qs ? `?${qs}` : ""}`
        );
        return handleResponse(response);
    },

    async createSchedule(
        playbookId: number,
        data: PlaybookScheduleCreateInput,
    ): Promise<PlaybookScheduleData> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/schedules`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    async deleteSchedule(scheduleId: number): Promise<void> {
        const response = await fetch(
            `${API}/schedules/${scheduleId}`,
            { method: "DELETE" }
        );
        return handleResponse(response);
    },

    // -- Event Triggers --
    async listTriggers(
        playbookId?: number,
    ): Promise<EventTriggerListData> {
        const params = new URLSearchParams();
        if (playbookId) params.set("playbook_id", String(playbookId));
        const qs = params.toString();
        const response = await fetch(
            `${API}/triggers${qs ? `?${qs}` : ""}`
        );
        return handleResponse(response);
    },

    async createTrigger(
        playbookId: number,
        data: EventTriggerCreateInput,
    ): Promise<EventTriggerData> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/triggers`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },

    async deleteTrigger(triggerId: number): Promise<void> {
        const response = await fetch(
            `${API}/triggers/${triggerId}`,
            { method: "DELETE" }
        );
        return handleResponse(response);
    },
};
