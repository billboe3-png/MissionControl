"""
Mission Control Approval Workflow Repository

All database access for ApprovalWorkflow and ApprovalRequest entities.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.approval_workflow import ApprovalWorkflow
from app.models.db.approval_request import ApprovalRequest


class ApprovalWorkflowRepository:
    """Data access layer for approval workflow records."""

    @staticmethod
    def get_by_playbook(
        db: Session, playbook_id: int
    ) -> list[ApprovalWorkflow]:
        stmt = (
            select(ApprovalWorkflow)
            .where(ApprovalWorkflow.playbook_id == playbook_id)
            .order_by(ApprovalWorkflow.created_at)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, workflow_id: int
    ) -> ApprovalWorkflow | None:
        stmt = select(ApprovalWorkflow).where(
            ApprovalWorkflow.id == workflow_id
        )
        return db.scalar(stmt)

    @staticmethod
    def create(
        db: Session,
        playbook_id: int,
        name: str,
        required_approvers: int = 1,
        approver_roles: str | None = None,
        auto_approve_on_timeout: bool = False,
        timeout_minutes: int = 60,
        enabled: bool = True,
    ) -> ApprovalWorkflow:
        entity = ApprovalWorkflow(
            playbook_id=playbook_id,
            name=name,
            required_approvers=required_approvers,
            approver_roles=approver_roles,
            auto_approve_on_timeout=auto_approve_on_timeout,
            timeout_minutes=timeout_minutes,
            enabled=enabled,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        entity: ApprovalWorkflow,
        **kwargs,
    ) -> ApprovalWorkflow:
        for key, value in kwargs.items():
            if value is not None:
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, entity: ApprovalWorkflow) -> None:
        db.delete(entity)
        db.commit()


class ApprovalRequestRepository:
    """Data access layer for approval request records."""

    @staticmethod
    def get_by_execution(
        db: Session, execution_id: int
    ) -> list[ApprovalRequest]:
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.execution_id == execution_id)
            .order_by(ApprovalRequest.requested_at)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_pending(db: Session) -> list[ApprovalRequest]:
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.status == "pending")
            .order_by(ApprovalRequest.requested_at)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(
        db: Session, request_id: int
    ) -> ApprovalRequest | None:
        stmt = select(ApprovalRequest).where(
            ApprovalRequest.id == request_id
        )
        return db.scalar(stmt)

    @staticmethod
    def create(
        db: Session,
        execution_id: int,
        workflow_id: int,
        requested_by: str | None = None,
    ) -> ApprovalRequest:
        entity = ApprovalRequest(
            execution_id=execution_id,
            workflow_id=workflow_id,
            requested_by=requested_by,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(
        db: Session,
        entity: ApprovalRequest,
        **kwargs,
    ) -> ApprovalRequest:
        for key, value in kwargs.items():
            if value is not None:
                setattr(entity, key, value)
        db.commit()
        db.refresh(entity)
        return entity
