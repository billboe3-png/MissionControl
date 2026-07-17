"""
Mission Control Automation Router

API endpoints for playbooks, steps, executions, approvals,
scheduling, triggers, audit trails, rollback, and dry run.

Sprint 2.8 - Automation & Playbooks.
"""

import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.approval import (
    ApprovalAction,
    ApprovalRequestListResponse,
    ApprovalRequestResponse,
    ApprovalWorkflowCreate,
    ApprovalWorkflowListResponse,
    ApprovalWorkflowResponse,
    ApprovalWorkflowUpdate,
)
from app.schemas.audit_trail import AuditTrailListResponse
from app.schemas.event_trigger import (
    EventTriggerCreate,
    EventTriggerListResponse,
    EventTriggerResponse,
    EventTriggerUpdate,
)
from app.schemas.execution_log import ExecutionLogListResponse
from app.schemas.playbook import (
    PlaybookCreate,
    PlaybookListResponse,
    PlaybookResponse,
    PlaybookUpdate,
)
from app.schemas.playbook_execution import (
    DryRunRequest,
    DryRunResponse,
    PlaybookExecuteRequest,
    PlaybookExecuteResponse,
    PlaybookExecutionListResponse,
    RollbackRequest,
    RollbackResponse,
)
from app.schemas.playbook_schedule import (
    PlaybookScheduleCreate,
    PlaybookScheduleListResponse,
    PlaybookScheduleResponse,
    PlaybookScheduleUpdate,
)
from app.schemas.playbook_step import (
    PlaybookStepCreate,
    PlaybookStepListResponse,
    PlaybookStepResponse,
    PlaybookStepUpdate,
)
from app.schemas.playbook_variable import (
    PlaybookVariableCreate,
    PlaybookVariableListResponse,
    PlaybookVariableResponse,
    PlaybookVariableUpdate,
)
from app.services.automation_service import (
    AutomationService,
    automation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/automation",
    tags=["Automation"],
    dependencies=[Depends(get_current_user)],
)


def get_automation_service() -> AutomationService:
    return automation_service


# ------------------------------------------------------------------ #
# Dashboard Summary                                                    #
# ------------------------------------------------------------------ #


@router.get("/dashboard")
async def get_automation_dashboard(
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> dict:
    return await service.get_automation_summary(db)


# ------------------------------------------------------------------ #
# Playbook Endpoints                                                   #
# ------------------------------------------------------------------ #


@router.get("/playbooks", response_model=PlaybookListResponse)
async def list_playbooks(
    search: str | None = Query(None),
    category: str | None = Query(None),
    enabled: bool | None = Query(None),
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookListResponse:
    return await service.get_playbooks(db, search, category, enabled)


@router.get(
    "/playbooks/{playbook_id}",
    response_model=PlaybookResponse,
)
async def get_playbook(
    playbook_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookResponse:
    return await service.get_playbook_by_id(db, playbook_id)


@router.post(
    "/playbooks",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaybookResponse,
)
async def create_playbook(
    payload: PlaybookCreate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookResponse:
    return await service.create_playbook(db, payload)


@router.put(
    "/playbooks/{playbook_id}",
    response_model=PlaybookResponse,
)
async def update_playbook(
    playbook_id: int,
    payload: PlaybookUpdate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookResponse:
    return await service.update_playbook(db, playbook_id, payload)


@router.delete(
    "/playbooks/{playbook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_playbook(
    playbook_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> None:
    await service.delete_playbook(db, playbook_id)


# ------------------------------------------------------------------ #
# Playbook Steps                                                       #
# ------------------------------------------------------------------ #


@router.get(
    "/playbooks/{playbook_id}/steps",
    response_model=PlaybookStepListResponse,
)
async def list_playbook_steps(
    playbook_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookStepListResponse:
    return await service.get_playbook_steps(db, playbook_id)


@router.post(
    "/playbooks/{playbook_id}/steps",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaybookStepResponse,
)
async def create_playbook_step(
    playbook_id: int,
    payload: PlaybookStepCreate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookStepResponse:
    return await service.create_playbook_step(
        db, playbook_id, payload
    )


@router.put(
    "/steps/{step_id}",
    response_model=PlaybookStepResponse,
)
async def update_playbook_step(
    step_id: int,
    payload: PlaybookStepUpdate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookStepResponse:
    return await service.update_playbook_step(db, step_id, payload)


@router.delete(
    "/steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_playbook_step(
    step_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> None:
    await service.delete_playbook_step(db, step_id)


# ------------------------------------------------------------------ #
# Playbook Variables                                                   #
# ------------------------------------------------------------------ #


@router.get(
    "/playbooks/{playbook_id}/variables",
    response_model=PlaybookVariableListResponse,
)
async def list_playbook_variables(
    playbook_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookVariableListResponse:
    return await service.get_playbook_variables(db, playbook_id)


@router.post(
    "/playbooks/{playbook_id}/variables",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaybookVariableResponse,
)
async def create_playbook_variable(
    playbook_id: int,
    payload: PlaybookVariableCreate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookVariableResponse:
    return await service.create_playbook_variable(
        db, playbook_id, payload
    )


@router.put(
    "/variables/{variable_id}",
    response_model=PlaybookVariableResponse,
)
async def update_playbook_variable(
    variable_id: int,
    payload: PlaybookVariableUpdate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookVariableResponse:
    return await service.update_playbook_variable(
        db, variable_id, payload
    )


@router.delete(
    "/variables/{variable_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_playbook_variable(
    variable_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> None:
    await service.delete_playbook_variable(db, variable_id)


# ------------------------------------------------------------------ #
# Playbook Execution                                                   #
# ------------------------------------------------------------------ #


@router.get(
    "/executions", response_model=PlaybookExecutionListResponse
)
async def list_executions(
    playbook_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookExecutionListResponse:
    return await service.get_executions(
        db, playbook_id, status_filter, limit
    )


@router.get(
    "/executions/{execution_id}",
    response_model=PlaybookExecuteResponse,
)
async def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookExecuteResponse:
    return await service.get_execution_by_id(db, execution_id)


@router.post(
    "/playbooks/{playbook_id}/execute",
    response_model=PlaybookExecuteResponse,
)
async def execute_playbook(
    playbook_id: int,
    payload: PlaybookExecuteRequest,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookExecuteResponse:
    return await service.execute_playbook(db, playbook_id, payload)


@router.post(
    "/playbooks/{playbook_id}/dry-run",
    response_model=DryRunResponse,
)
async def dry_run_playbook(
    playbook_id: int,
    payload: DryRunRequest,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> DryRunResponse:
    return await service.dry_run_playbook(db, playbook_id, payload)


@router.post(
    "/executions/{execution_id}/rollback",
    response_model=RollbackResponse,
)
async def rollback_execution(
    execution_id: int,
    payload: RollbackRequest,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> RollbackResponse:
    return await service.rollback_execution(
        db, execution_id, payload
    )


# ------------------------------------------------------------------ #
# Execution Logs                                                       #
# ------------------------------------------------------------------ #


@router.get(
    "/executions/{execution_id}/logs",
    response_model=ExecutionLogListResponse,
)
async def get_execution_logs(
    execution_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> ExecutionLogListResponse:
    return await service.get_execution_logs(db, execution_id)


# ------------------------------------------------------------------ #
# Approval Workflows                                                   #
# ------------------------------------------------------------------ #


@router.get(
    "/playbooks/{playbook_id}/workflows",
    response_model=ApprovalWorkflowListResponse,
)
async def list_approval_workflows(
    playbook_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> ApprovalWorkflowListResponse:
    return await service.get_approval_workflows(db, playbook_id)


@router.post(
    "/playbooks/{playbook_id}/workflows",
    status_code=status.HTTP_201_CREATED,
    response_model=ApprovalWorkflowResponse,
)
async def create_approval_workflow(
    playbook_id: int,
    payload: ApprovalWorkflowCreate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> ApprovalWorkflowResponse:
    return await service.create_approval_workflow(
        db, playbook_id, payload
    )


@router.put(
    "/workflows/{workflow_id}",
    response_model=ApprovalWorkflowResponse,
)
async def update_approval_workflow(
    workflow_id: int,
    payload: ApprovalWorkflowUpdate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> ApprovalWorkflowResponse:
    return await service.update_approval_workflow(
        db, workflow_id, payload
    )


@router.delete(
    "/workflows/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_approval_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> None:
    await service.delete_approval_workflow(db, workflow_id)


# ------------------------------------------------------------------ #
# Approval Requests                                                    #
# ------------------------------------------------------------------ #


@router.get(
    "/approvals/pending",
    response_model=ApprovalRequestListResponse,
)
async def list_pending_approvals(
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> ApprovalRequestListResponse:
    return await service.get_pending_approvals(db)


@router.get(
    "/executions/{execution_id}/approvals",
    response_model=ApprovalRequestListResponse,
)
async def list_execution_approvals(
    execution_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> ApprovalRequestListResponse:
    return await service.get_approval_requests(db, execution_id)


@router.put(
    "/approvals/{request_id}/approve",
    response_model=ApprovalRequestResponse,
)
async def approve_request(
    request_id: int,
    payload: ApprovalAction,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> ApprovalRequestResponse:
    return await service.approve_request(db, request_id, payload)


@router.put(
    "/approvals/{request_id}/reject",
    response_model=ApprovalRequestResponse,
)
async def reject_request(
    request_id: int,
    payload: ApprovalAction,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> ApprovalRequestResponse:
    return await service.reject_request(db, request_id, payload)


# ------------------------------------------------------------------ #
# Audit Trail                                                          #
# ------------------------------------------------------------------ #


@router.get(
    "/audit", response_model=AuditTrailListResponse
)
async def list_audit_trail(
    entity_type: str | None = Query(None),
    action: str | None = Query(None),
    actor: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> AuditTrailListResponse:
    return await service.get_audit_trail(
        db, entity_type, action, actor, limit
    )


# ------------------------------------------------------------------ #
# Schedules                                                            #
# ------------------------------------------------------------------ #


@router.get(
    "/schedules", response_model=PlaybookScheduleListResponse
)
async def list_schedules(
    playbook_id: int | None = Query(None),
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookScheduleListResponse:
    return await service.get_schedules(db, playbook_id)


@router.post(
    "/playbooks/{playbook_id}/schedules",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaybookScheduleResponse,
)
async def create_schedule(
    playbook_id: int,
    payload: PlaybookScheduleCreate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookScheduleResponse:
    return await service.create_schedule(db, playbook_id, payload)


@router.put(
    "/schedules/{schedule_id}",
    response_model=PlaybookScheduleResponse,
)
async def update_schedule(
    schedule_id: int,
    payload: PlaybookScheduleUpdate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookScheduleResponse:
    return await service.update_schedule(db, schedule_id, payload)


@router.delete(
    "/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> None:
    await service.delete_schedule(db, schedule_id)


# ------------------------------------------------------------------ #
# Event Triggers                                                       #
# ------------------------------------------------------------------ #


@router.get(
    "/triggers", response_model=EventTriggerListResponse
)
async def list_triggers(
    playbook_id: int | None = Query(None),
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> EventTriggerListResponse:
    return await service.get_triggers(db, playbook_id)


@router.post(
    "/playbooks/{playbook_id}/triggers",
    status_code=status.HTTP_201_CREATED,
    response_model=EventTriggerResponse,
)
async def create_trigger(
    playbook_id: int,
    payload: EventTriggerCreate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> EventTriggerResponse:
    return await service.create_trigger(db, playbook_id, payload)


@router.put(
    "/triggers/{trigger_id}",
    response_model=EventTriggerResponse,
)
async def update_trigger(
    trigger_id: int,
    payload: EventTriggerUpdate,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> EventTriggerResponse:
    return await service.update_trigger(db, trigger_id, payload)


@router.delete(
    "/triggers/{trigger_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_trigger(
    trigger_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> None:
    await service.delete_trigger(db, trigger_id)


@router.post("/triggers/fire/{event_type}")
async def fire_event(
    event_type: str,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> dict:
    results = await service.fire_event(db, event_type)
    return {
        "event_type": event_type,
        "playbooks_triggered": len(results),
    }


# ------------------------------------------------------------------ #
# Clone / Export / Import                                             #
# ------------------------------------------------------------------ #


@router.post("/playbooks/{playbook_id}/clone")
async def clone_playbook(
    playbook_id: int,
    name: str | None = Query(None, description="Name for the cloned playbook"),
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookResponse:
    return await service.clone_playbook(db, playbook_id, name)


@router.get("/playbooks/{playbook_id}/export")
async def export_playbook(
    playbook_id: int,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> dict:
    return await service.export_playbook(db, playbook_id)


@router.post("/playbooks/import", status_code=status.HTTP_201_CREATED)
async def import_playbook(
    payload: dict,
    db: Session = Depends(get_db),
    service: AutomationService = Depends(get_automation_service),
) -> PlaybookResponse:
    return await service.import_playbook(db, payload)
