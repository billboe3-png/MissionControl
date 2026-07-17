import { apiClient } from "../utils/apiClient";
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
    ExecutionLogData,
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
    ExecutionLogData,
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

// ------------------------------------------------------------------ //
// API Client                                                            //
// ------------------------------------------------------------------ //

export const automationApi = {
    // -- Dashboard --
    async getSummary(): Promise<AutomationSummaryData> {
        return apiClient<AutomationSummaryData>(`${API}/dashboard`);
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
        return apiClient<PlaybookListData>(
            `${API}/playbooks${qs ? `?${qs}` : ""}`
        );
    },

    async getPlaybook(id: number): Promise<PlaybookData> {
        return apiClient<PlaybookData>(`${API}/playbooks/${id}`);
    },

    async createPlaybook(
        data: PlaybookCreateInput,
    ): Promise<PlaybookData> {
        return apiClient<PlaybookData>(`${API}/playbooks`, {
            method: "POST",
            json: data,
        });
    },

    async updatePlaybook(
        id: number,
        data: PlaybookUpdateInput,
    ): Promise<PlaybookData> {
        return apiClient<PlaybookData>(`${API}/playbooks/${id}`, {
            method: "PUT",
            json: data,
        });
    },

    async deletePlaybook(id: number): Promise<void> {
        return apiClient<void>(`${API}/playbooks/${id}`, {
            method: "DELETE",
        });
    },

    // -- Steps --
    async listSteps(
        playbookId: number,
    ): Promise<PlaybookStepListData> {
        return apiClient<PlaybookStepListData>(
            `${API}/playbooks/${playbookId}/steps`
        );
    },

    async createStep(
        playbookId: number,
        data: PlaybookStepCreateInput,
    ): Promise<PlaybookStepListData> {
        return apiClient<PlaybookStepListData>(
            `${API}/playbooks/${playbookId}/steps`,
            {
                method: "POST",
                json: data,
            }
        );
    },

    async updateStep(
        stepId: number,
        data: PlaybookStepUpdateInput,
    ): Promise<PlaybookStepListData> {
        return apiClient<PlaybookStepListData>(`${API}/steps/${stepId}`, {
            method: "PUT",
            json: data,
        });
    },

    async deleteStep(stepId: number): Promise<void> {
        return apiClient<void>(`${API}/steps/${stepId}`, {
            method: "DELETE",
        });
    },

    // -- Variables --
    async listVariables(
        playbookId: number,
    ): Promise<PlaybookVariableListData> {
        return apiClient<PlaybookVariableListData>(
            `${API}/playbooks/${playbookId}/variables`
        );
    },

    async createVariable(
        playbookId: number,
        data: PlaybookVariableCreateInput,
    ): Promise<PlaybookVariableListData> {
        return apiClient<PlaybookVariableListData>(
            `${API}/playbooks/${playbookId}/variables`,
            {
                method: "POST",
                json: data,
            }
        );
    },

    async updateVariable(
        variableId: number,
        data: PlaybookVariableUpdateInput,
    ): Promise<PlaybookVariableListData> {
        return apiClient<PlaybookVariableListData>(
            `${API}/variables/${variableId}`,
            {
                method: "PUT",
                json: data,
            }
        );
    },

    async deleteVariable(variableId: number): Promise<void> {
        return apiClient<void>(
            `${API}/variables/${variableId}`,
            { method: "DELETE" }
        );
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
        return apiClient<PlaybookExecutionListData>(
            `${API}/executions${qs ? `?${qs}` : ""}`
        );
    },

    async getExecution(
        id: number,
    ): Promise<PlaybookExecutionData> {
        return apiClient<PlaybookExecutionData>(`${API}/executions/${id}`);
    },

    async executePlaybook(
        playbookId: number,
        data: PlaybookExecuteInput,
    ): Promise<PlaybookExecutionData> {
        return apiClient<PlaybookExecutionData>(
            `${API}/playbooks/${playbookId}/execute`,
            {
                method: "POST",
                json: data,
            }
        );
    },

    async dryRun(
        playbookId: number,
        data: DryRunInput,
    ): Promise<DryRunData> {
        return apiClient<DryRunData>(
            `${API}/playbooks/${playbookId}/dry-run`,
            {
                method: "POST",
                json: data,
            }
        );
    },

    async rollback(
        executionId: number,
        data: RollbackInput,
    ): Promise<RollbackData> {
        return apiClient<RollbackData>(
            `${API}/executions/${executionId}/rollback`,
            {
                method: "POST",
                json: data,
            }
        );
    },

    // -- Execution Logs --
    async listExecutionLogs(
        executionId: number,
    ): Promise<ExecutionLogListData> {
        return apiClient<ExecutionLogListData>(
            `${API}/executions/${executionId}/logs`
        );
    },

    // -- Approval Workflows --
    async listWorkflows(
        playbookId: number,
    ): Promise<ApprovalWorkflowListData> {
        return apiClient<ApprovalWorkflowListData>(
            `${API}/playbooks/${playbookId}/workflows`
        );
    },

    async createWorkflow(
        playbookId: number,
        data: ApprovalWorkflowCreateInput,
    ): Promise<ApprovalWorkflowListData> {
        return apiClient<ApprovalWorkflowListData>(
            `${API}/playbooks/${playbookId}/workflows`,
            {
                method: "POST",
                json: data,
            }
        );
    },

    async deleteWorkflow(workflowId: number): Promise<void> {
        return apiClient<void>(
            `${API}/workflows/${workflowId}`,
            { method: "DELETE" }
        );
    },

    // -- Approval Requests --
    async listPendingApprovals(): Promise<ApprovalRequestListData> {
        return apiClient<ApprovalRequestListData>(`${API}/approvals/pending`);
    },

    async listExecutionApprovals(
        executionId: number,
    ): Promise<ApprovalRequestListData> {
        return apiClient<ApprovalRequestListData>(
            `${API}/executions/${executionId}/approvals`
        );
    },

    async approveRequest(
        requestId: number,
        data: ApprovalActionInput,
    ): Promise<ApprovalRequestData> {
        return apiClient<ApprovalRequestData>(
            `${API}/approvals/${requestId}/approve`,
            {
                method: "PUT",
                json: data,
            }
        );
    },

    async rejectRequest(
        requestId: number,
        data: ApprovalActionInput,
    ): Promise<ApprovalRequestData> {
        return apiClient<ApprovalRequestData>(
            `${API}/approvals/${requestId}/reject`,
            {
                method: "PUT",
                json: data,
            }
        );
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
        return apiClient<AuditTrailListData>(
            `${API}/audit${qs ? `?${qs}` : ""}`
        );
    },

    // -- Schedules --
    async listSchedules(
        playbookId?: number,
    ): Promise<PlaybookScheduleListData> {
        const params = new URLSearchParams();
        if (playbookId) params.set("playbook_id", String(playbookId));
        const qs = params.toString();
        return apiClient<PlaybookScheduleListData>(
            `${API}/schedules${qs ? `?${qs}` : ""}`
        );
    },

    async createSchedule(
        playbookId: number,
        data: PlaybookScheduleCreateInput,
    ): Promise<PlaybookScheduleData> {
        return apiClient<PlaybookScheduleData>(
            `${API}/playbooks/${playbookId}/schedules`,
            {
                method: "POST",
                json: data,
            }
        );
    },

    async deleteSchedule(scheduleId: number): Promise<void> {
        return apiClient<void>(
            `${API}/schedules/${scheduleId}`,
            { method: "DELETE" }
        );
    },

    // -- Event Triggers --
    async listTriggers(
        playbookId?: number,
    ): Promise<EventTriggerListData> {
        const params = new URLSearchParams();
        if (playbookId) params.set("playbook_id", String(playbookId));
        const qs = params.toString();
        return apiClient<EventTriggerListData>(
            `${API}/triggers${qs ? `?${qs}` : ""}`
        );
    },

    async createTrigger(
        playbookId: number,
        data: EventTriggerCreateInput,
    ): Promise<EventTriggerData> {
        return apiClient<EventTriggerData>(
            `${API}/playbooks/${playbookId}/triggers`,
            {
                method: "POST",
                json: data,
            }
        );
    },

    async deleteTrigger(triggerId: number): Promise<void> {
        return apiClient<void>(
            `${API}/triggers/${triggerId}`,
            { method: "DELETE" }
        );
    },

    // -- Clone / Export / Import --
    async clonePlaybook(
        playbookId: number,
        name?: string,
    ): Promise<PlaybookData> {
        const params = new URLSearchParams();
        if (name) params.set("name", name);
        const qs = params.toString();
        return apiClient<PlaybookData>(
            `${API}/playbooks/${playbookId}/clone${qs ? `?${qs}` : ""}`,
            { method: "POST" }
        );
    },

    async exportPlaybook(
        playbookId: number,
    ): Promise<{ playbook: unknown; steps: unknown[]; variables: unknown[] }> {
        return apiClient(
            `${API}/playbooks/${playbookId}/export`
        );
    },

    async importPlaybook(
        data: { playbook: unknown; steps: unknown[]; variables: unknown[] },
    ): Promise<PlaybookData> {
        return apiClient<PlaybookData>(
            `${API}/playbooks/import`,
            {
                method: "POST",
                json: data,
            }
        );
    },
};
