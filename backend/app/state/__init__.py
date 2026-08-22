"""
Mission Control Agent State Engine

Centralized state management for all agents.
Single source of truth for agent status, health, and activity.

States:
    online       - Agent is connected and responding to heartbeats
    offline      - Agent has not sent a heartbeat within threshold
    warning      - Agent reports warning health
    healthy      - Agent reports healthy status
    unhealthy    - Agent reports critical health
    updating     - Agent is performing self-update
    pending      - Agent has queued commands waiting
    executing    - Agent is currently executing a command
    disabled     - Agent has been administratively disabled
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy.orm import Session

from app.events import Event, EventType, event_bus
from app.models.db.agent import Agent
from app.repositories.agent_repository import AgentRepository

logger = logging.getLogger(__name__)

# Agent is considered offline if no heartbeat for this long
OFFLINE_THRESHOLD_SECONDS = 120


class AgentState(StrEnum):
    """Possible states for an agent."""

    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UPDATING = "updating"
    PENDING = "pending"
    EXECUTING = "executing"
    DISABLED = "disabled"


class AgentStateEngine:
    """Centralized agent state management."""

    def __init__(self) -> None:
        self._state_cache: dict[int, AgentState] = {}
        self._publish_tasks: set[asyncio.Task] = set()

    def get_state(self, agent: Agent) -> AgentState:
        """Determine the current state of an agent from its model."""
        if not agent.enabled:
            return AgentState.DISABLED

        if agent.status == "offline":
            return AgentState.OFFLINE

        # Check if heartbeat is stale
        if agent.last_heartbeat:
            elapsed = (datetime.now(UTC) - agent.last_heartbeat).total_seconds()
            if elapsed > OFFLINE_THRESHOLD_SECONDS:
                return AgentState.OFFLINE

        # Check health status
        if agent.health == "critical":
            return AgentState.UNHEALTHY
        if agent.health == "warning":
            return AgentState.WARNING

        return AgentState.ONLINE

    def update_state(self, db: Session, agent_id: int, state: AgentState) -> None:
        """Update an agent's state and publish event if changed."""
        old_state = self._state_cache.get(agent_id)
        self._state_cache[agent_id] = state

        if old_state != state:
            logger.info(
                "Agent %d state: %s -> %s",
                agent_id,
                old_state.value if old_state else "unknown",
                state.value,
            )
            # Publish state change event
            try:
                loop = asyncio.get_running_loop()
                task = loop.create_task(
                    event_bus.publish(
                        Event(
                            type=EventType.AGENT_HEALTH_CHANGED,
                            data={
                                "agent_id": agent_id,
                                "old_state": old_state.value if old_state else None,
                                "new_state": state.value,
                            },
                            source="state_engine",
                        )
                    )
                )
                self._publish_tasks.add(task)
                task.add_done_callback(self._publish_tasks.discard)
            except RuntimeError:
                # No event loop running (e.g., during testing)
                pass

    def refresh_all(self, db: Session) -> dict[int, AgentState]:
        """Refresh state for all agents and return current states."""
        agents = AgentRepository.get_all(db)
        for agent in agents:
            state = self.get_state(agent)
            self.update_state(db, agent.id, state)
        return dict(self._state_cache)

    def get_state_summary(self, db: Session) -> dict[str, int]:
        """Return a count of agents in each state."""
        self.refresh_all(db)
        summary: dict[str, int] = {s.value: 0 for s in AgentState}
        for state in self._state_cache.values():
            summary[state.value] += 1
        return summary


# Global singleton
agent_state_engine = AgentStateEngine()
