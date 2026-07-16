import type {
    PlaybookCreateInput,
    PlaybookUpdateInput,
    PlaybookListData,
    PlaybookData,
    PlaybookStepCreateInput,
    PlaybookStepUpdateInput,
    PlaybookStepData,
    PlaybookStepListData,
    PlaybookVariableCreateInput,
    PlaybookVariableUpdateInput,
    PlaybookVariableData,
    PlaybookVariableListData,
    PlaybookExecuteInput,
    PlaybookExecutionListData,
    PlaybookExecutionData,
    DryRunInput,
    DryRunData,
    RollbackInput,
    RollbackData,
    ExecutionLogListData,
    ApprovalWorkflowCreateInput,
    ApprovalWorkflowListData,
    ApprovalWorkflowData,
    ApprovalRequestListData,
    ApprovalRequestData,
    ApprovalActionInput,
    AuditTrailData,
    AuditTrailListData,
    PlaybookScheduleCreateInput,
    PlaybookScheduleListData,
    PlaybookScheduleData,
    EventTriggerCreateInput,
    EventTriggerListData,
    EventTriggerData,
    AutomationSummaryData,
} from "../types/automation";

export type {
    PlaybookCreateInput,
    PlaybookUpdateInput,
    PlaybookListData,
    PlaybookData,
    PlaybookStepCreateInput,
    PlaybookStepUpdateInput,
    PlaybookStepData,
    PlaybookStepListData,
    PlaybookVariableCreateInput,
    PlaybookVariableUpdateInput,
    PlaybookVariableData,
    PlaybookVariableListData,
    PlaybookExecuteInput,
    PlaybookExecutionListData,
    PlaybookExecutionData,
    DryRunInput,
    DryRunData,
    RollbackInput,
    RollbackData,
    ExecutionLogListData,
    ApprovalWorkflowCreateInput,
    ApprovalWorkflowListData,
    ApprovalWorkflowData,
    ApprovalRequestListData,
    ApprovalRequestData,
    ApprovalActionInput,
    AuditTrailData,
    AuditTrailListData,
    PlaybookScheduleCreateInput,
    PlaybookScheduleListData,
    PlaybookScheduleData,
    EventTriggerCreateInput,
    EventTriggerListData,
    EventTriggerData,
    AutomationSummaryData,
} from "../types/automation";

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
    ): Promise<PlaybookStepListData> {
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
    ): Promise<PlaybookStepListData> {
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
    ): Promise<PlaybookVariableListData> {
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
    ): Promise<PlaybookVariableListData> {
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
    ): Promise<ApprovalWorkflowListData> {
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

    // -- Clone / Export / Import --
    async clonePlaybook(
        playbookId: number,
        name?: string,
    ): Promise<PlaybookData> {
        const params = new URLSearchParams();
        if (name) params.set("name", name);
        const qs = params.toString();
        const response = await fetch(
            `${API}/playbooks/${playbookId}/clone${qs ? `?${qs}` : ""}`,
            { method: "POST" }
        );
        return handleResponse(response);
    },

    async exportPlaybook(
        playbookId: number,
    ): Promise<{ playbook: unknown; steps: unknown[]; variables: unknown[] }> {
        const response = await fetch(
            `${API}/playbooks/${playbookId}/export`
        );
        return handleResponse(response);
    },

    async importPlaybook(
        data: { playbook: unknown; steps: unknown[]; variables: unknown[] },
    ): Promise<PlaybookData> {
        const response = await fetch(
            `${API}/playbooks/import`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            }
        );
        return handleResponse(response);
    },
};
