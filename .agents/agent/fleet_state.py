"""Mission Control Agent - Fleet state tracking and transitions."""

import logging
import time
from collections import deque
from typing import Any

logger = logging.getLogger("mc-agent")

AGENT_STATES = {
    "online": {"color": "green", "description": "Agent is online and healthy"},
    "offline": {"color": "red", "description": "Agent is not responding"},
    "starting": {"color": "yellow", "description": "Agent is starting up"},
    "busy": {"color": "blue", "description": "Agent is executing a command"},
    "idle": {"color": "green", "description": "Agent is online but idle"},
    "updating": {"color": "yellow", "description": "Agent is updating"},
    "maintenance": {"color": "orange", "description": "Agent is in maintenance mode"},
    "warning": {"color": "yellow", "description": "Agent has warnings"},
    "error": {"color": "red", "description": "Agent has errors"},
    "unknown": {"color": "gray", "description": "Agent state is unknown"},
}

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "online": [
        "offline",
        "busy",
        "idle",
        "updating",
        "maintenance",
        "warning",
        "error",
    ],
    "offline": ["online", "starting", "warning", "error", "unknown"],
    "starting": ["online", "offline", "error"],
    "busy": ["online", "idle", "warning", "error", "offline"],
    "idle": [
        "online",
        "busy",
        "updating",
        "maintenance",
        "warning",
        "error",
        "offline",
    ],
    "updating": ["online", "offline", "error", "warning"],
    "maintenance": ["online", "offline", "warning", "error"],
    "warning": [
        "online",
        "offline",
        "error",
        "idle",
        "busy",
        "maintenance",
        "updating",
    ],
    "error": ["online", "offline", "starting", "warning", "idle"],
    "unknown": ["online", "offline", "starting", "warning", "error"],
}

MAX_TRANSITIONS = 100


class FleetState:
    """Fleet state tracking and transitions."""

    def __init__(self) -> None:
        self._states: dict[int, dict[str, Any]] = {}
        self._transitions: deque[dict[str, Any]] = deque(maxlen=MAX_TRANSITIONS)

    def update_state(
        self,
        agent_id: int,
        new_state: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update state, detect transitions."""
        if new_state not in AGENT_STATES:
            raise ValueError(f"Invalid state: {new_state}")

        current = self._states.get(agent_id)
        current_state = current["state"] if current else "unknown"

        if not self._should_transition(current_state, new_state):
            logger.debug(
                "Transition %s -> %s not allowed for agent %d, forcing",
                current_state,
                new_state,
                agent_id,
            )

        transition = {
            "agent_id": agent_id,
            "from_state": current_state,
            "to_state": new_state,
            "timestamp": time.time(),
            "details": details or {},
        }

        self._transitions.append(transition)

        self._states[agent_id] = {
            "agent_id": agent_id,
            "state": new_state,
            "last_updated": time.time(),
            "details": details or {},
        }

        if current_state != new_state:
            logger.info(
                "Agent %d: %s -> %s",
                agent_id,
                current_state,
                new_state,
            )

        return self._states[agent_id]

    def get_state(self, agent_id: int) -> dict[str, Any]:
        """Get current state for an agent."""
        if agent_id not in self._states:
            return {
                "agent_id": agent_id,
                "state": "unknown",
                "last_updated": 0.0,
                "details": {},
            }
        return self._states[agent_id]

    def get_all_states(self) -> dict[int, dict[str, Any]]:
        """Get all agent states."""
        return dict(self._states)

    def detect_offline_agents(self, timeout_seconds: int = 120) -> list[int]:
        """Return IDs of agents that haven't sent heartbeat within timeout."""
        now = time.time()
        offline = []
        for agent_id, state in self._states.items():
            age = now - state["last_updated"]
            if age > timeout_seconds and state["state"] not in ("offline", "unknown"):
                offline.append(agent_id)
        return offline

    def detect_transitions(self) -> list[dict[str, Any]]:
        """Return list of recent state transitions."""
        return list(self._transitions)

    def get_fleet_summary(self) -> dict[str, Any]:
        """Return aggregate statistics."""
        state_counts: dict[str, int] = {}
        total = 0

        for state_info in self._states.values():
            state = state_info["state"]
            state_counts[state] = state_counts.get(state, 0) + 1
            total += 1

        return {
            "total_agents": total,
            "state_counts": state_counts,
            "states": {
                s: {
                    "count": state_counts.get(s, 0),
                    "color": info["color"],
                    "description": info["description"],
                }
                for s, info in AGENT_STATES.items()
            },
            "recent_transitions": len(self._transitions),
        }

    def _should_transition(self, current: str, new: str) -> bool:
        """Validate state transition is allowed."""
        if current == new:
            return True

        allowed = ALLOWED_TRANSITIONS.get(current, [])
        return new in allowed
