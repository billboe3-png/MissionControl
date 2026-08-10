"""
Mission Control Automation Service

Business logic for automation: playbooks, steps, executions,
approvals, scheduling, event triggers, audit trails, rollback,
and dry run mode.

Sprint 2.8 - Automation & Playbooks.
"""

import contextlib
import json
import logging
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.providers.automation.base_provider import ExecutionContext, StepResult
from app.providers.automation.provider_factory import (
    get_automation_provider,
)
from app.repositories.approval_repository import (
    ApprovalRequestRepository,
    ApprovalWorkflowRepository,
)
from app.repositories.audit_trail_repository import AuditTrailRepository
from app.repositories.event_trigger_repository import EventTriggerRepository
from app.repositories.execution_log_repository import ExecutionLogRepository
from app.repositories.playbook_execution_repository import (
    PlaybookExecutionRepository,
)
from app.repositories.playbook_repository import PlaybookRepository
from app.repositories.playbook_schedule_repository import (
    PlaybookScheduleRepository,
)
from app.repositories.playbook_step_repository import (
    PlaybookStepRepository,
)
from app.repositories.playbook_variable_repository import (
    PlaybookVariableRepository,
)
from app.schemas.approval import (
    ApprovalAction,
    ApprovalRequestListResponse,
    ApprovalRequestResponse,
    ApprovalWorkflowCreate,
    ApprovalWorkflowListResponse,
    ApprovalWorkflowResponse,
    ApprovalWorkflowUpdate,
)
from app.schemas.audit_trail import (
    AuditTrailListResponse,
    AuditTrailResponse,
)
from app.schemas.event_trigger import (
    EventTriggerCreate,
    EventTriggerListResponse,
    EventTriggerResponse,
    EventTriggerUpdate,
)
from app.schemas.execution_log import (
    ExecutionLogListResponse,
    ExecutionLogResponse,
)
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

logger = logging.getLogger(__name__)


class AutomationService:
    """Orchestration layer for all automation operations."""

    # ------------------------------------------------------------------ #
    # Playbook CRUD                                                       #
    # ------------------------------------------------------------------ #

    async def get_playbooks(
        self,
        db: Session,
        search: str | None = None,
        category: str | None = None,
        enabled: bool | None = None,
    ) -> PlaybookListResponse:
        items = PlaybookRepository.get_filtered(
            db, search=search, category=category, enabled=enabled
        )
        return PlaybookListResponse(
            count=len(items),
            items=[
                PlaybookResponse.model_validate(i) for i in items
            ],
        )

    async def get_playbook_by_id(
        self, db: Session, playbook_id: int
    ) -> PlaybookResponse:
        entity = PlaybookRepository.get_by_id(db, playbook_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook {playbook_id} not found",
            )
        return PlaybookResponse.model_validate(entity)

    async def create_playbook(
        self, db: Session, payload: PlaybookCreate
    ) -> PlaybookResponse:
        entity = PlaybookRepository.create(
            db,
            name=payload.name,
            description=payload.description,
            category=payload.category,
            tags=payload.tags,
            enabled=payload.enabled,
            requires_approval=payload.requires_approval,
            auto_rollback=payload.auto_rollback,
            timeout_seconds=payload.timeout_seconds,
            max_retries=payload.max_retries,
            created_by=payload.created_by,
        )
        AuditTrailRepository.create(
            db,
            entity_type="playbook",
            entity_id=entity.id,
            action="created",
            actor=payload.created_by,
            details=f"Created playbook '{payload.name}'",
        )
        return PlaybookResponse.model_validate(entity)

    async def update_playbook(
        self,
        db: Session,
        playbook_id: int,
        payload: PlaybookUpdate,
    ) -> PlaybookResponse:
        entity = PlaybookRepository.get_by_id(db, playbook_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook {playbook_id} not found",
            )
        update_data = payload.model_dump(exclude_unset=True)
        if "version" not in update_data:
            entity.version += 1
        updated = PlaybookRepository.update(db, entity, **update_data)
        AuditTrailRepository.create(
            db,
            entity_type="playbook",
            entity_id=updated.id,
            action="updated",
            details=f"Updated playbook '{updated.name}'",
        )
        return PlaybookResponse.model_validate(updated)

    async def delete_playbook(
        self, db: Session, playbook_id: int
    ) -> None:
        entity = PlaybookRepository.get_by_id(db, playbook_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook {playbook_id} not found",
            )
        AuditTrailRepository.create(
            db,
            entity_type="playbook",
            entity_id=entity.id,
            action="deleted",
            details=f"Deleted playbook '{entity.name}'",
        )
        PlaybookRepository.delete(db, entity)

    # ------------------------------------------------------------------ #
    # Playbook Steps                                                      #
    # ------------------------------------------------------------------ #

    async def get_playbook_steps(
        self, db: Session, playbook_id: int
    ) -> PlaybookStepListResponse:
        self._ensure_playbook_exists(db, playbook_id)
        items = PlaybookStepRepository.get_by_playbook(
            db, playbook_id
        )
        return PlaybookStepListResponse(
            count=len(items),
            items=[
                PlaybookStepResponse.model_validate(i)
                for i in items
            ],
        )

    async def create_playbook_step(
        self,
        db: Session,
        playbook_id: int,
        payload: PlaybookStepCreate,
    ) -> PlaybookStepResponse:
        self._ensure_playbook_exists(db, playbook_id)
        existing = PlaybookStepRepository.get_by_playbook(
            db, playbook_id
        )
        order = payload.step_order
        if order == 0 and existing:
            order = max(s.step_order for s in existing) + 1
        entity = PlaybookStepRepository.create(
            db,
            playbook_id=playbook_id,
            name=payload.name,
            step_type=payload.step_type,
            provider=payload.provider,
            command=payload.command,
            step_order=order,
            description=payload.description,
            target_host=payload.target_host,
            shell=payload.shell,
            working_directory=payload.working_directory,
            environment_variables=payload.environment_variables,
            timeout_seconds=payload.timeout_seconds,
            retry_count=payload.retry_count,
            continue_on_failure=payload.continue_on_failure,
            rollback_command=payload.rollback_command,
        )
        return PlaybookStepResponse.model_validate(entity)

    async def update_playbook_step(
        self,
        db: Session,
        step_id: int,
        payload: PlaybookStepUpdate,
    ) -> PlaybookStepResponse:
        entity = PlaybookStepRepository.get_by_id(db, step_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Step {step_id} not found",
            )
        update_data = payload.model_dump(exclude_unset=True)
        updated = PlaybookStepRepository.update(
            db, entity, **update_data
        )
        return PlaybookStepResponse.model_validate(updated)

    async def delete_playbook_step(
        self, db: Session, step_id: int
    ) -> None:
        entity = PlaybookStepRepository.get_by_id(db, step_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Step {step_id} not found",
            )
        PlaybookStepRepository.delete(db, entity)

    # ------------------------------------------------------------------ #
    # Playbook Variables                                                  #
    # ------------------------------------------------------------------ #

    async def get_playbook_variables(
        self, db: Session, playbook_id: int
    ) -> PlaybookVariableListResponse:
        self._ensure_playbook_exists(db, playbook_id)
        items = PlaybookVariableRepository.get_by_playbook(
            db, playbook_id
        )
        return PlaybookVariableListResponse(
            count=len(items),
            items=[
                PlaybookVariableResponse.model_validate(i)
                for i in items
            ],
        )

    async def create_playbook_variable(
        self,
        db: Session,
        playbook_id: int,
        payload: PlaybookVariableCreate,
    ) -> PlaybookVariableResponse:
        self._ensure_playbook_exists(db, playbook_id)
        entity = PlaybookVariableRepository.create(
            db,
            playbook_id=playbook_id,
            name=payload.name,
            value=payload.value,
            variable_type=payload.variable_type,
            description=payload.description,
            required=payload.required,
            sensitive=payload.sensitive,
            default_value=payload.default_value,
        )
        return PlaybookVariableResponse.model_validate(entity)

    async def update_playbook_variable(
        self,
        db: Session,
        variable_id: int,
        payload: PlaybookVariableUpdate,
    ) -> PlaybookVariableResponse:
        entity = PlaybookVariableRepository.get_by_id(
            db, variable_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variable {variable_id} not found",
            )
        update_data = payload.model_dump(exclude_unset=True)
        updated = PlaybookVariableRepository.update(
            db, entity, **update_data
        )
        return PlaybookVariableResponse.model_validate(updated)

    async def delete_playbook_variable(
        self, db: Session, variable_id: int
    ) -> None:
        entity = PlaybookVariableRepository.get_by_id(
            db, variable_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variable {variable_id} not found",
            )
        PlaybookVariableRepository.delete(db, entity)

    # ------------------------------------------------------------------ #
    # Playbook Execution                                                  #
    # ------------------------------------------------------------------ #

    async def execute_playbook(
        self,
        db: Session,
        playbook_id: int,
        payload: PlaybookExecuteRequest,
    ) -> PlaybookExecuteResponse:
        playbook = PlaybookRepository.get_by_id(db, playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook {playbook_id} not found",
            )
        if not playbook.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Playbook is disabled",
            )

        steps = PlaybookStepRepository.get_by_playbook(
            db, playbook_id
        )
        variables = PlaybookVariableRepository.get_by_playbook(
            db, playbook_id
        )

        merged_vars = {}
        for v in variables:
            val = payload.variables.get(v.name) if payload.variables else None
            merged_vars[v.name] = val or v.value or v.default_value or ""

        approval_required = playbook.requires_approval
        execution = PlaybookExecutionRepository.create(
            db,
            playbook_id=playbook_id,
            status="pending" if approval_required else "running",
            mode=payload.mode,
            trigger_type="manual",
            triggered_by=payload.triggered_by,
            variables_used=json.dumps(merged_vars) if merged_vars else None,
            steps_total=len(steps),
            approval_required=approval_required,
        )

        AuditTrailRepository.create(
            db,
            entity_type="playbook_execution",
            entity_id=execution.id,
            action="started",
            actor=payload.triggered_by,
            details=f"Execution of playbook '{playbook.name}' (mode={payload.mode})",
        )

        if approval_required:
            workflows = ApprovalWorkflowRepository.get_by_playbook(
                db, playbook_id
            )
            for wf in workflows:
                if wf.enabled:
                    ApprovalRequestRepository.create(
                        db,
                        execution_id=execution.id,
                        workflow_id=wf.id,
                        requested_by=payload.triggered_by,
                    )

            return PlaybookExecuteResponse.model_validate(
                execution
            )

        if payload.mode == "live":
            await self._run_playbook_steps(
                db, execution.id, steps, merged_vars, playbook.auto_rollback
            )

        execution = PlaybookExecutionRepository.get_by_id(
            db, execution.id
        )
        return PlaybookExecuteResponse.model_validate(execution)

    async def _run_playbook_steps(
        self,
        db: Session,
        execution_id: int,
        steps: list,
        variables: dict[str, str],
        auto_rollback: bool,
    ) -> None:
        PlaybookExecutionRepository.update(
            db,
            PlaybookExecutionRepository.get_by_id(
                db, execution_id
            ),
            status="running",
            started_at=datetime.now(UTC),
        )

        completed = 0
        failed = 0
        skipped = 0
        all_output = []

        for step in steps:
            ExecutionLogRepository.create(
                db,
                execution_id=execution_id,
                step_id=step.id,
                level="info",
                message=f"Starting step: {step.name}",
            )

            max_attempts = 1 + (step.retry_count or 0)
            last_result = None

            for attempt in range(max_attempts):
                if attempt > 0:
                    ExecutionLogRepository.create(
                        db,
                        execution_id=execution_id,
                        step_id=step.id,
                        level="info",
                        message=f"Retrying step '{step.name}' (attempt {attempt + 1}/{max_attempts})",
                    )

                try:
                    provider = get_automation_provider(step.provider)

                    ctx = ExecutionContext(
                        playbook_id=step.playbook_id,
                        execution_id=execution_id,
                        step_id=step.id,
                        step_name=step.name,
                        command=step.command,
                        provider=step.provider,
                        target_host=step.target_host,
                        shell=step.shell,
                        working_directory=step.working_directory,
                        timeout_seconds=step.timeout_seconds,
                        variables=variables,
                    )

                    result = await provider.execute_step(ctx)
                    last_result = result

                    if result.success:
                        break

                except Exception as exc:
                    last_result = StepResult(
                        success=False,
                        error=str(exc),
                        exit_code=-1,
                    )

            if last_result is None:
                raise RuntimeError(
                    f"Step '{step.name}' produced no result after {max_attempts} attempt(s)"
                )

            ExecutionLogRepository.create(
                db,
                execution_id=execution_id,
                step_id=step.id,
                level="info" if last_result.success else "error",
                message=(
                    f"Step '{step.name}' "
                    f"{'succeeded' if last_result.success else 'failed'}"
                    + (f" after {max_attempts} attempt(s)" if max_attempts > 1 else "")
                ),
                stdout=last_result.stdout,
                stderr=last_result.stderr,
                exit_code=last_result.exit_code,
                duration_ms=last_result.duration_ms,
            )

            if last_result.success:
                completed += 1
                all_output.append(
                    f"[STEP {step.step_order}] {step.name}: OK"
                )
            else:
                failed += 1
                all_output.append(
                    f"[STEP {step.step_order}] {step.name}: FAILED - {last_result.error or last_result.stderr}"
                )

                if not step.continue_on_failure:
                    if auto_rollback:
                        await self._execute_rollback(
                            db,
                            execution_id,
                            steps,
                            step,
                            variables,
                        )
                    skipped += len(steps) - completed - failed
                    break

        final_status = "completed" if failed == 0 else "failed"

        PlaybookExecutionRepository.update(
            db,
            PlaybookExecutionRepository.get_by_id(
                db, execution_id
            ),
            status=final_status,
            steps_completed=completed,
            steps_failed=failed,
            steps_skipped=skipped,
            output="\n".join(all_output),
            completed_at=datetime.now(UTC),
        )

        AuditTrailRepository.create(
            db,
            entity_type="playbook_execution",
            entity_id=execution_id,
            action=final_status,
            details=f"Execution {final_status}: {completed} ok, {failed} failed, {skipped} skipped",
        )

    async def _execute_rollback(
        self,
        db: Session,
        execution_id: int,
        all_steps: list,
        failed_step,
        variables: dict[str, str],
    ) -> None:
        PlaybookExecutionRepository.update(
            db,
            PlaybookExecutionRepository.get_by_id(
                db, execution_id
            ),
            rollback_status="running",
        )

        rollback_output = []

        for step in reversed(all_steps):
            if step.step_order >= failed_step.step_order:
                continue
            if not step.rollback_command:
                continue

            try:
                provider = get_automation_provider(step.provider)
                ctx = ExecutionContext(
                    playbook_id=step.playbook_id,
                    execution_id=execution_id,
                    step_id=step.id,
                    step_name=step.name,
                    command=step.rollback_command,
                    provider=step.provider,
                    target_host=step.target_host,
                    shell=step.shell,
                    working_directory=step.working_directory,
                    timeout_seconds=step.timeout_seconds,
                    variables=variables,
                )
                result = await provider.rollback_step(
                    ctx, step.rollback_command
                )
                rollback_output.append(
                    f"Rollback {step.name}: {'OK' if result.success else 'FAILED'}"
                )
            except Exception as exc:
                rollback_output.append(
                    f"Rollback {step.name}: EXCEPTION - {exc}"
                )

        PlaybookExecutionRepository.update(
            db,
            PlaybookExecutionRepository.get_by_id(
                db, execution_id
            ),
            rollback_status="completed",
            rollback_output="\n".join(rollback_output),
        )

    async def get_executions(
        self,
        db: Session,
        playbook_id: int | None = None,
        status_filter: str | None = None,
        limit: int = 50,
    ) -> PlaybookExecutionListResponse:
        items = PlaybookExecutionRepository.get_filtered(
            db,
            playbook_id=playbook_id,
            status=status_filter,
            limit=limit,
        )
        return PlaybookExecutionListResponse(
            count=len(items),
            items=[
                PlaybookExecuteResponse.model_validate(i)
                for i in items
            ],
        )

    async def get_execution_by_id(
        self, db: Session, execution_id: int
    ) -> PlaybookExecuteResponse:
        entity = PlaybookExecutionRepository.get_by_id(
            db, execution_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found",
            )
        return PlaybookExecuteResponse.model_validate(entity)

    # ------------------------------------------------------------------ #
    # Dry Run                                                             #
    # ------------------------------------------------------------------ #

    async def dry_run_playbook(
        self,
        db: Session,
        playbook_id: int,
        payload: DryRunRequest,
    ) -> DryRunResponse:
        playbook = PlaybookRepository.get_by_id(db, playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook {playbook_id} not found",
            )

        steps = PlaybookStepRepository.get_by_playbook(
            db, playbook_id
        )
        variables = PlaybookVariableRepository.get_by_playbook(
            db, playbook_id
        )

        merged_vars = {}
        for v in variables:
            val = payload.variables.get(v.name) if payload.variables else None
            merged_vars[v.name] = val or v.value or v.default_value or ""

        warnings = []
        errors = []

        for step in steps:
            try:
                provider = get_automation_provider(step.provider)
                ctx = ExecutionContext(
                    playbook_id=playbook_id,
                    execution_id=0,
                    step_id=step.id,
                    step_name=step.name,
                    command=step.command,
                    provider=step.provider,
                    target_host=step.target_host,
                    shell=step.shell,
                    working_directory=step.working_directory,
                    timeout_seconds=step.timeout_seconds,
                    variables=merged_vars,
                )
                validation = await provider.validate_step(ctx)
                for w in validation.get("warnings", []):
                    warnings.append(f"[{step.name}] {w}")
                for e in validation.get("errors", []):
                    errors.append(f"[{step.name}] {e}")
            except ValueError as exc:
                errors.append(f"[{step.name}] {exc}")

        execution = PlaybookExecutionRepository.create(
            db,
            playbook_id=playbook_id,
            status="dry_run",
            mode="dry_run",
            trigger_type="manual",
            variables_used=json.dumps(merged_vars) if merged_vars else None,
            steps_total=len(steps),
        )

        AuditTrailRepository.create(
            db,
            entity_type="playbook",
            entity_id=playbook_id,
            action="dry_run",
            details=f"Dry run of playbook '{playbook.name}'",
        )

        return DryRunResponse(
            execution_id=execution.id,
            status="dry_run_completed",
            steps_validated=len(steps) - len(errors),
            steps_total=len(steps),
            output=f"Dry run completed for '{playbook.name}'",
            warnings=warnings,
            errors=errors,
        )

    # ------------------------------------------------------------------ #
    # Rollback                                                             #
    # ------------------------------------------------------------------ #

    async def rollback_execution(
        self,
        db: Session,
        execution_id: int,
        payload: RollbackRequest,
    ) -> RollbackResponse:
        execution = PlaybookExecutionRepository.get_by_id(
            db, execution_id
        )
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found",
            )

        steps = PlaybookStepRepository.get_by_playbook(
            db, execution.playbook_id
        )

        variables = {}
        if execution.variables_used:
            with contextlib.suppress(json.JSONDecodeError, TypeError):
                variables = json.loads(execution.variables_used)

        await self._execute_rollback(
            db, execution_id, steps, None, variables
        )

        AuditTrailRepository.create(
            db,
            entity_type="playbook_execution",
            entity_id=execution_id,
            action="rollback",
            details=payload.reason or "Manual rollback",
        )

        execution = PlaybookExecutionRepository.get_by_id(
            db, execution_id
        )

        return RollbackResponse(
            execution_id=execution_id,
            rollback_status=execution.rollback_status or "unknown",
            output=execution.rollback_output,
            error=None,
        )

    # ------------------------------------------------------------------ #
    # Approval Workflows                                                  #
    # ------------------------------------------------------------------ #

    async def get_approval_workflows(
        self, db: Session, playbook_id: int
    ) -> ApprovalWorkflowListResponse:
        items = ApprovalWorkflowRepository.get_by_playbook(
            db, playbook_id
        )
        return ApprovalWorkflowListResponse(
            count=len(items),
            items=[
                ApprovalWorkflowResponse.model_validate(i)
                for i in items
            ],
        )

    async def create_approval_workflow(
        self,
        db: Session,
        playbook_id: int,
        payload: ApprovalWorkflowCreate,
    ) -> ApprovalWorkflowResponse:
        self._ensure_playbook_exists(db, playbook_id)
        entity = ApprovalWorkflowRepository.create(
            db,
            playbook_id=playbook_id,
            name=payload.name,
            required_approvers=payload.required_approvers,
            approver_roles=payload.approver_roles,
            auto_approve_on_timeout=payload.auto_approve_on_timeout,
            timeout_minutes=payload.timeout_minutes,
            enabled=payload.enabled,
        )
        return ApprovalWorkflowResponse.model_validate(entity)

    async def update_approval_workflow(
        self,
        db: Session,
        workflow_id: int,
        payload: ApprovalWorkflowUpdate,
    ) -> ApprovalWorkflowResponse:
        entity = ApprovalWorkflowRepository.get_by_id(
            db, workflow_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )
        update_data = payload.model_dump(exclude_unset=True)
        updated = ApprovalWorkflowRepository.update(
            db, entity, **update_data
        )
        return ApprovalWorkflowResponse.model_validate(updated)

    async def delete_approval_workflow(
        self, db: Session, workflow_id: int
    ) -> None:
        entity = ApprovalWorkflowRepository.get_by_id(
            db, workflow_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )
        ApprovalWorkflowRepository.delete(db, entity)

    # ------------------------------------------------------------------ #
    # Approval Requests                                                   #
    # ------------------------------------------------------------------ #

    async def get_pending_approvals(
        self, db: Session
    ) -> ApprovalRequestListResponse:
        items = ApprovalRequestRepository.get_pending(db)
        return ApprovalRequestListResponse(
            count=len(items),
            items=[
                ApprovalRequestResponse.model_validate(i)
                for i in items
            ],
        )

    async def get_approval_requests(
        self, db: Session, execution_id: int
    ) -> ApprovalRequestListResponse:
        items = ApprovalRequestRepository.get_by_execution(
            db, execution_id
        )
        return ApprovalRequestListResponse(
            count=len(items),
            items=[
                ApprovalRequestResponse.model_validate(i)
                for i in items
            ],
        )

    async def approve_request(
        self,
        db: Session,
        request_id: int,
        payload: ApprovalAction,
    ) -> ApprovalRequestResponse:
        entity = ApprovalRequestRepository.get_by_id(
            db, request_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request {request_id} not found",
            )
        if entity.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request already {entity.status}",
            )

        updated = ApprovalRequestRepository.update(
            db,
            entity,
            status="approved",
            approved_by=payload.approved_by,
            comments=payload.comments,
            responded_at=datetime.now(UTC),
        )

        execution = PlaybookExecutionRepository.get_by_id(
            db, entity.execution_id
        )
        if execution:
            workflow = ApprovalWorkflowRepository.get_by_id(
                db, entity.workflow_id
            )
            all_requests = (
                ApprovalRequestRepository.get_by_execution(
                    db, execution.id
                )
            )
            approved_count = sum(
                1 for r in all_requests if r.status == "approved"
            )

            if (
                workflow
                and approved_count >= workflow.required_approvers
            ):
                PlaybookExecutionRepository.update(
                    db,
                    execution,
                    status="running",
                    approval_status="approved",
                )
                AuditTrailRepository.create(
                    db,
                    entity_type="playbook_execution",
                    entity_id=execution.id,
                    action="approved",
                    actor=payload.approved_by,
                    details=f"Approved by {payload.approved_by}",
                )

                playbook = PlaybookRepository.get_by_id(
                    db, execution.playbook_id
                )
                steps = PlaybookStepRepository.get_by_playbook(
                    db, execution.playbook_id
                )
                variables = {}
                if execution.variables_used:
                    with contextlib.suppress(json.JSONDecodeError, TypeError):
                        variables = json.loads(
                            execution.variables_used
                        )

                if playbook and steps:
                    await self._run_playbook_steps(
                        db,
                        execution.id,
                        steps,
                        variables,
                        playbook.auto_rollback,
                    )

        AuditTrailRepository.create(
            db,
            entity_type="approval_request",
            entity_id=updated.id,
            action="approved",
            actor=payload.approved_by,
            details=payload.comments or "Approved",
        )

        return ApprovalRequestResponse.model_validate(updated)

    async def reject_request(
        self,
        db: Session,
        request_id: int,
        payload: ApprovalAction,
    ) -> ApprovalRequestResponse:
        entity = ApprovalRequestRepository.get_by_id(
            db, request_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request {request_id} not found",
            )
        if entity.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request already {entity.status}",
            )

        updated = ApprovalRequestRepository.update(
            db,
            entity,
            status="rejected",
            approved_by=payload.approved_by,
            comments=payload.comments,
            responded_at=datetime.now(UTC),
        )

        execution = PlaybookExecutionRepository.get_by_id(
            db, entity.execution_id
        )
        if execution:
            PlaybookExecutionRepository.update(
                db,
                execution,
                status="rejected",
                approval_status="rejected",
            )

        AuditTrailRepository.create(
            db,
            entity_type="approval_request",
            entity_id=updated.id,
            action="rejected",
            actor=payload.approved_by,
            details=payload.comments or "Rejected",
        )

        return ApprovalRequestResponse.model_validate(updated)

    # ------------------------------------------------------------------ #
    # Execution Logs                                                      #
    # ------------------------------------------------------------------ #

    async def get_execution_logs(
        self, db: Session, execution_id: int
    ) -> ExecutionLogListResponse:
        items = ExecutionLogRepository.get_by_execution(
            db, execution_id
        )
        return ExecutionLogListResponse(
            count=len(items),
            items=[
                ExecutionLogResponse.model_validate(i)
                for i in items
            ],
        )

    # ------------------------------------------------------------------ #
    # Audit Trail                                                         #
    # ------------------------------------------------------------------ #

    async def get_audit_trail(
        self,
        db: Session,
        entity_type: str | None = None,
        action: str | None = None,
        actor: str | None = None,
        limit: int = 100,
    ) -> AuditTrailListResponse:
        items = AuditTrailRepository.get_filtered(
            db,
            entity_type=entity_type,
            action=action,
            actor=actor,
            limit=limit,
        )
        return AuditTrailListResponse(
            count=len(items),
            items=[
                AuditTrailResponse.model_validate(i)
                for i in items
            ],
        )

    # ------------------------------------------------------------------ #
    # Schedules                                                           #
    # ------------------------------------------------------------------ #

    async def get_schedules(
        self, db: Session, playbook_id: int | None = None
    ) -> PlaybookScheduleListResponse:
        if playbook_id:
            items = PlaybookScheduleRepository.get_by_playbook(
                db, playbook_id
            )
        else:
            items = PlaybookScheduleRepository.get_all(db)
        return PlaybookScheduleListResponse(
            count=len(items),
            items=[
                PlaybookScheduleResponse.model_validate(i)
                for i in items
            ],
        )

    async def create_schedule(
        self,
        db: Session,
        playbook_id: int,
        payload: PlaybookScheduleCreate,
    ) -> PlaybookScheduleResponse:
        self._ensure_playbook_exists(db, playbook_id)
        entity = PlaybookScheduleRepository.create(
            db,
            playbook_id=playbook_id,
            name=payload.name,
            cron_expression=payload.cron_expression,
            enabled=payload.enabled,
            variables_override=payload.variables_override,
        )
        return PlaybookScheduleResponse.model_validate(entity)

    async def update_schedule(
        self,
        db: Session,
        schedule_id: int,
        payload: PlaybookScheduleUpdate,
    ) -> PlaybookScheduleResponse:
        entity = PlaybookScheduleRepository.get_by_id(
            db, schedule_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule {schedule_id} not found",
            )
        update_data = payload.model_dump(exclude_unset=True)
        updated = PlaybookScheduleRepository.update(
            db, entity, **update_data
        )
        return PlaybookScheduleResponse.model_validate(updated)

    async def delete_schedule(
        self, db: Session, schedule_id: int
    ) -> None:
        entity = PlaybookScheduleRepository.get_by_id(
            db, schedule_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule {schedule_id} not found",
            )
        PlaybookScheduleRepository.delete(db, entity)

    # ------------------------------------------------------------------ #
    # Event Triggers                                                      #
    # ------------------------------------------------------------------ #

    async def get_triggers(
        self, db: Session, playbook_id: int | None = None
    ) -> EventTriggerListResponse:
        if playbook_id:
            items = EventTriggerRepository.get_by_playbook(
                db, playbook_id
            )
        else:
            items = EventTriggerRepository.get_all(db)
        return EventTriggerListResponse(
            count=len(items),
            items=[
                EventTriggerResponse.model_validate(i)
                for i in items
            ],
        )

    async def create_trigger(
        self,
        db: Session,
        playbook_id: int,
        payload: EventTriggerCreate,
    ) -> EventTriggerResponse:
        self._ensure_playbook_exists(db, playbook_id)
        entity = EventTriggerRepository.create(
            db,
            playbook_id=playbook_id,
            name=payload.name,
            event_type=payload.event_type,
            conditions=payload.conditions,
            enabled=payload.enabled,
        )
        return EventTriggerResponse.model_validate(entity)

    async def update_trigger(
        self,
        db: Session,
        trigger_id: int,
        payload: EventTriggerUpdate,
    ) -> EventTriggerResponse:
        entity = EventTriggerRepository.get_by_id(
            db, trigger_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger {trigger_id} not found",
            )
        update_data = payload.model_dump(exclude_unset=True)
        updated = EventTriggerRepository.update(
            db, entity, **update_data
        )
        return EventTriggerResponse.model_validate(updated)

    async def delete_trigger(
        self, db: Session, trigger_id: int
    ) -> None:
        entity = EventTriggerRepository.get_by_id(
            db, trigger_id
        )
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger {trigger_id} not found",
            )
        EventTriggerRepository.delete(db, entity)

    async def fire_event(
        self, db: Session, event_type: str
    ) -> list[PlaybookExecuteResponse]:
        triggers = EventTriggerRepository.get_by_event_type(
            db, event_type
        )
        results = []
        for trigger in triggers:
            trigger.trigger_count += 1
            trigger.last_triggered = datetime.now(UTC)
            db.commit()

            req = PlaybookExecuteRequest(
                mode="live",
                triggered_by=f"event:{event_type}",
            )
            result = await self.execute_playbook(
                db, trigger.playbook_id, req
            )
            results.append(result)

        return results

    # ------------------------------------------------------------------ #
    # Automation Dashboard Summary                                        #
    # ------------------------------------------------------------------ #

    async def get_automation_summary(
        self, db: Session
    ) -> dict:
        total_playbooks = PlaybookRepository.count(db)
        total_executions = PlaybookExecutionRepository.count(db)
        running = PlaybookExecutionRepository.count_by_status(
            db, "running"
        )
        completed = PlaybookExecutionRepository.count_by_status(
            db, "completed"
        )
        failed = PlaybookExecutionRepository.count_by_status(
            db, "failed"
        )
        pending = PlaybookExecutionRepository.count_by_status(
            db, "pending"
        )
        audit_count = AuditTrailRepository.count(db)

        return {
            "total_playbooks": total_playbooks,
            "total_executions": total_executions,
            "running": running,
            "completed": completed,
            "failed": failed,
            "pending_approvals": pending,
            "audit_entries": audit_count,
        }

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _ensure_playbook_exists(
        self, db: Session, playbook_id: int
    ) -> None:
        entity = PlaybookRepository.get_by_id(db, playbook_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook {playbook_id} not found",
            )

    # ------------------------------------------------------------------ #
    # Clone / Export / Import                                             #
    # ------------------------------------------------------------------ #

    async def clone_playbook(
        self, db: Session, playbook_id: int, name: str | None = None
    ) -> PlaybookResponse:
        """Clone a playbook with all its steps and variables."""
        source = PlaybookRepository.get_by_id(db, playbook_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook {playbook_id} not found",
            )

        clone_name = name or f"{source.name} (Copy)"
        new_playbook = PlaybookRepository.create(
            db,
            name=clone_name,
            description=source.description,
            category=source.category,
            tags=source.tags,
            enabled=False,
            requires_approval=source.requires_approval,
            auto_rollback=source.auto_rollback,
            timeout_seconds=source.timeout_seconds,
            max_retries=source.max_retries,
            created_by="clone",
        )

        source_steps = PlaybookStepRepository.get_by_playbook(
            db, playbook_id
        )
        for step in source_steps:
            PlaybookStepRepository.create(
                db,
                playbook_id=new_playbook.id,
                name=step.name,
                description=step.description,
                step_type=step.step_type,
                provider=step.provider,
                command=step.command,
                target_host=step.target_host,
                shell=step.shell,
                working_directory=step.working_directory,
                environment_variables=step.environment_variables,
                timeout_seconds=step.timeout_seconds,
                retry_count=step.retry_count,
                continue_on_failure=step.continue_on_failure,
                rollback_command=step.rollback_command,
                step_order=step.step_order,
            )

        source_vars = PlaybookVariableRepository.get_by_playbook(
            db, playbook_id
        )
        for var in source_vars:
            PlaybookVariableRepository.create(
                db,
                playbook_id=new_playbook.id,
                name=var.name,
                value=var.value,
                variable_type=var.variable_type,
                description=var.description,
                required=var.required,
                sensitive=var.sensitive,
                default_value=var.default_value,
            )

        return PlaybookResponse.model_validate(new_playbook)

    async def export_playbook(
        self, db: Session, playbook_id: int
    ) -> dict:
        """Export a playbook with all steps and variables as a dict."""
        playbook = PlaybookRepository.get_by_id(db, playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playbook {playbook_id} not found",
            )

        steps = PlaybookStepRepository.get_by_playbook(
            db, playbook_id
        )
        variables = PlaybookVariableRepository.get_by_playbook(
            db, playbook_id
        )

        return {
            "playbook": {
                "name": playbook.name,
                "description": playbook.description,
                "category": playbook.category,
                "tags": playbook.tags,
                "requires_approval": playbook.requires_approval,
                "auto_rollback": playbook.auto_rollback,
                "timeout_seconds": playbook.timeout_seconds,
                "max_retries": playbook.max_retries,
            },
            "steps": [
                {
                    "name": s.name,
                    "description": s.description,
                    "step_type": s.step_type,
                    "provider": s.provider,
                    "command": s.command,
                    "target_host": s.target_host,
                    "shell": s.shell,
                    "working_directory": s.working_directory,
                    "environment_variables": s.environment_variables,
                    "timeout_seconds": s.timeout_seconds,
                    "retry_count": s.retry_count,
                    "continue_on_failure": s.continue_on_failure,
                    "rollback_command": s.rollback_command,
                    "step_order": s.step_order,
                }
                for s in steps
            ],
            "variables": [
                {
                    "name": v.name,
                    "value": v.value if not v.sensitive else None,
                    "variable_type": v.variable_type,
                    "description": v.description,
                    "required": v.required,
                    "sensitive": v.sensitive,
                    "default_value": v.default_value,
                }
                for v in variables
            ],
        }

    async def import_playbook(
        self, db: Session, data: dict
    ) -> PlaybookResponse:
        """Import a playbook from exported data."""
        pb_data = data.get("playbook", {})
        name = pb_data.get("name", "Imported Playbook")

        existing = PlaybookRepository.get_filtered(db, search=name)
        if len(existing) > 0:
            name = f"{name} (Imported)"

        new_playbook = PlaybookRepository.create(
            db,
            name=name,
            description=pb_data.get("description"),
            category=pb_data.get("category"),
            tags=pb_data.get("tags"),
            enabled=False,
            requires_approval=pb_data.get("requires_approval", False),
            auto_rollback=pb_data.get("auto_rollback", False),
            timeout_seconds=pb_data.get("timeout_seconds", 3600),
            max_retries=pb_data.get("max_retries", 0),
            created_by="import",
        )

        for step_data in data.get("steps", []):
            PlaybookStepRepository.create(
                db,
                playbook_id=new_playbook.id,
                name=step_data.get("name", "Unnamed Step"),
                description=step_data.get("description"),
                step_type=step_data.get("step_type", "remote_command"),
                provider=step_data.get("provider", "ssh"),
                command=step_data.get("command", ""),
                target_host=step_data.get("target_host"),
                shell=step_data.get("shell"),
                working_directory=step_data.get("working_directory"),
                environment_variables=step_data.get("environment_variables"),
                timeout_seconds=step_data.get("timeout_seconds", 300),
                retry_count=step_data.get("retry_count", 0),
                continue_on_failure=step_data.get("continue_on_failure", False),
                rollback_command=step_data.get("rollback_command"),
                step_order=step_data.get("step_order", 0),
            )

        for var_data in data.get("variables", []):
            PlaybookVariableRepository.create(
                db,
                playbook_id=new_playbook.id,
                name=var_data.get("name", "unnamed"),
                value=var_data.get("value"),
                variable_type=var_data.get("variable_type", "string"),
                description=var_data.get("description"),
                required=var_data.get("required", False),
                sensitive=var_data.get("sensitive", False),
                default_value=var_data.get("default_value"),
            )

        return PlaybookResponse.model_validate(new_playbook)

    # ------------------------------------------------------------------ #
    # Variable Substitution                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def substitute_variables(
        text: str, variables: dict[str, str], max_depth: int = 5
    ) -> str:
        """Recursively substitute {{variable}} placeholders in text."""
        result = text
        for _ in range(max_depth):
            changed = False
            for key, value in variables.items():
                placeholder = "{{" + key + "}}"
                if placeholder in result:
                    result = result.replace(placeholder, value)
                    changed = True
            if not changed:
                break
        return result


automation_service = AutomationService()
