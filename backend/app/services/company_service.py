"""
Mission Control Company Service

Business logic layer for Company entities.
Sprint 2.9 - Multi-Tenant & Multi-Site Platform.
"""

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.company_repository import CompanyRepository
from app.schemas.company import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)

logger = logging.getLogger(__name__)


class CompanyService:
    """Business logic for company management."""

    @staticmethod
    def get_all(db: Session) -> CompanyListResponse:
        """Return all companies with stats."""
        companies = CompanyRepository.get_all(db)
        all_stats = CompanyRepository.get_all_company_stats(db)
        items = []
        for company in companies:
            stats = all_stats.get(company.id, {"site_count": 0, "agent_count": 0, "integration_count": 0})
            items.append(
                CompanyResponse(
                    id=company.id,
                    uuid=company.uuid,
                    name=company.name,
                    display_name=company.display_name,
                    status=company.status,
                    license_type=company.license_type,
                    max_sites=company.max_sites,
                    max_agents=company.max_agents,
                    max_users=company.max_users,
                    primary_contact=company.primary_contact,
                    contact_email=company.contact_email,
                    contact_phone=company.contact_phone,
                    timezone=company.timezone,
                    logo_url=company.logo_url,
                    theme=company.theme,
                    notes=company.notes,
                    enabled=company.enabled,
                    is_global=company.is_global,
                    site_count=stats["site_count"],
                    agent_count=stats["agent_count"],
                    integration_count=stats["integration_count"],
                    created_at=company.created_at,
                    updated_at=company.updated_at,
                )
            )
        return CompanyListResponse(count=len(items), items=items)

    @staticmethod
    def get_by_id(db: Session, company_id: int) -> CompanyResponse | None:
        """Return a single company by ID with stats."""
        company = CompanyRepository.get_by_id(db, company_id)
        if company is None:
            return None
        stats = CompanyRepository.get_company_stats(db, company.id)
        return CompanyResponse(
            id=company.id,
            uuid=company.uuid,
            name=company.name,
            display_name=company.display_name,
            status=company.status,
            license_type=company.license_type,
            max_sites=company.max_sites,
            max_agents=company.max_agents,
            max_users=company.max_users,
            primary_contact=company.primary_contact,
            contact_email=company.contact_email,
            contact_phone=company.contact_phone,
            timezone=company.timezone,
            logo_url=company.logo_url,
            theme=company.theme,
            notes=company.notes,
            enabled=company.enabled,
            is_global=company.is_global,
            site_count=stats["site_count"],
            agent_count=stats["agent_count"],
            integration_count=stats["integration_count"],
            created_at=company.created_at,
            updated_at=company.updated_at,
        )

    @staticmethod
    def get_by_uuid(db: Session, company_uuid: str) -> CompanyResponse | None:
        """Return a single company by UUID."""
        company = CompanyRepository.get_by_uuid(db, company_uuid)
        if company is None:
            return None
        stats = CompanyRepository.get_company_stats(db, company.id)
        return CompanyResponse(
            id=company.id,
            uuid=company.uuid,
            name=company.name,
            display_name=company.display_name,
            status=company.status,
            license_type=company.license_type,
            max_sites=company.max_sites,
            max_agents=company.max_agents,
            max_users=company.max_users,
            primary_contact=company.primary_contact,
            contact_email=company.contact_email,
            contact_phone=company.contact_phone,
            timezone=company.timezone,
            logo_url=company.logo_url,
            theme=company.theme,
            notes=company.notes,
            enabled=company.enabled,
            is_global=company.is_global,
            site_count=stats["site_count"],
            agent_count=stats["agent_count"],
            integration_count=stats["integration_count"],
            created_at=company.created_at,
            updated_at=company.updated_at,
        )

    @staticmethod
    def create(db: Session, request: CompanyCreate) -> CompanyResponse:
        """Create a new company."""
        existing = CompanyRepository.get_by_name(db, request.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Company with name '{request.name}' already exists",
            )
        company = CompanyRepository.create(
            db,
            uuid=str(uuid.uuid4()),
            name=request.name,
            display_name=request.display_name,
            status=request.status,
            license_type=request.license_type,
            max_sites=request.max_sites,
            max_agents=request.max_agents,
            max_users=request.max_users,
            primary_contact=request.primary_contact,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            timezone=request.timezone,
            logo_url=request.logo_url,
            theme=request.theme,
            notes=request.notes,
            enabled=request.enabled,
        )
        stats = CompanyRepository.get_company_stats(db, company.id)
        return CompanyResponse(
            id=company.id,
            uuid=company.uuid,
            name=company.name,
            display_name=company.display_name,
            status=company.status,
            license_type=company.license_type,
            max_sites=company.max_sites,
            max_agents=company.max_agents,
            max_users=company.max_users,
            primary_contact=company.primary_contact,
            contact_email=company.contact_email,
            contact_phone=company.contact_phone,
            timezone=company.timezone,
            logo_url=company.logo_url,
            theme=company.theme,
            notes=company.notes,
            enabled=company.enabled,
            is_global=company.is_global,
            site_count=stats["site_count"],
            agent_count=stats["agent_count"],
            integration_count=stats["integration_count"],
            created_at=company.created_at,
            updated_at=company.updated_at,
        )

    @staticmethod
    def update(
        db: Session, company_id: int, request: CompanyUpdate
    ) -> CompanyResponse | None:
        """Update an existing company."""
        company = CompanyRepository.update(
            db,
            company_id,
            name=request.name,
            display_name=request.display_name,
            status=request.status,
            license_type=request.license_type,
            max_sites=request.max_sites,
            max_agents=request.max_agents,
            max_users=request.max_users,
            primary_contact=request.primary_contact,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            timezone=request.timezone,
            logo_url=request.logo_url,
            theme=request.theme,
            notes=request.notes,
            enabled=request.enabled,
        )
        if company is None:
            return None
        stats = CompanyRepository.get_company_stats(db, company.id)
        return CompanyResponse(
            id=company.id,
            uuid=company.uuid,
            name=company.name,
            display_name=company.display_name,
            status=company.status,
            license_type=company.license_type,
            max_sites=company.max_sites,
            max_agents=company.max_agents,
            max_users=company.max_users,
            primary_contact=company.primary_contact,
            contact_email=company.contact_email,
            contact_phone=company.contact_phone,
            timezone=company.timezone,
            logo_url=company.logo_url,
            theme=company.theme,
            notes=company.notes,
            enabled=company.enabled,
            is_global=company.is_global,
            site_count=stats["site_count"],
            agent_count=stats["agent_count"],
            integration_count=stats["integration_count"],
            created_at=company.created_at,
            updated_at=company.updated_at,
        )

    @staticmethod
    def delete(db: Session, company_id: int) -> bool:
        """Delete a company."""
        return CompanyRepository.delete(db, company_id)

    @staticmethod
    def get_all_summary(db: Session) -> list[dict]:
        """Return lightweight company list for selector dropdowns."""
        companies = CompanyRepository.get_enabled(db)
        return [
            {
                "id": c.id,
                "uuid": c.uuid,
                "name": c.name,
                "display_name": c.display_name,
                "status": c.status,
                "enabled": c.enabled,
            }
            for c in companies
        ]
