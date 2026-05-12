#!/usr/bin/env python3
"""Workflow State v2 — shared module for step gate state management.

Provides WorkflowState class for reading/writing workflow-state.yaml files
with schema_version 2.0, including SHA256 hash tracking and resume pointers.
"""

import hashlib
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import yaml


def compute_file_hash(filepath: str) -> Optional[str]:
    """Compute SHA256 hash of a file. Returns 'sha256:<hex>' or None if missing."""
    if not os.path.isfile(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _generate_run_id() -> str:
    """Generate run_id in YYYYMMDD-HHMMSS format."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _iso_now() -> str:
    """Current ISO 8601 timestamp with timezone."""
    return datetime.now(timezone.utc).isoformat()


class WorkflowState:
    """Workflow State v2 reader/writer.

    Manages the authoritative workflow-state.yaml file that tracks:
    - Which steps have been completed (with output file hashes)
    - Which steps are blocked (with missing prerequisites)
    - Current step and resume pointer
    - Artifact registry with tamper-detection hashes
    """

    SCHEMA_VERSION = "2.0"

    def __init__(self, state_path: str, workflow: str, tool_version: str):
        self.state_path = state_path
        self.workflow = workflow
        self.tool_version = tool_version
        self.data = self._load_or_create()

    def _load_or_create(self) -> dict:
        """Load existing state file or create a new one."""
        if os.path.isfile(self.state_path):
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data and data.get("schema_version") == self.SCHEMA_VERSION:
                return data
        return self._new_state()

    def _new_state(self) -> dict:
        """Create a fresh state structure."""
        return {
            "schema_version": self.SCHEMA_VERSION,
            "workflow": self.workflow,
            "run_id": _generate_run_id(),
            "tool_version": self.tool_version,
            "current_step": None,
            "current_stage": None,
            "status": "in_progress",
            "completed_steps": [],
            "blocked_steps": [],
            "artifacts": {},
            "human_checkpoints": {},
            "resume": {"next_step": None, "next_action": None},
        }

    # --- Reading ---

    def get_current_step(self) -> Optional[str]:
        return self.data.get("current_step")

    def get_status(self) -> str:
        return self.data.get("status", "in_progress")

    def get_completed_step_ids(self) -> List[str]:
        return [s["step"] for s in self.data.get("completed_steps", [])]

    def get_resume(self) -> Dict:
        return self.data.get("resume", {})

    def is_step_completed(self, step_id: str) -> bool:
        return step_id in self.get_completed_step_ids()

    def get_stage(self) -> Optional[str]:
        return self.data.get("current_stage")

    def get_human_checkpoint(self, name: str) -> dict:
        # Support both plural (code standard) and singular (legacy/docs)
        checkpoints = self.data.get("human_checkpoints") or self.data.get("human_checkpoint") or {}
        return checkpoints.get(name, {})

    # --- Writing ---

    def mark_step_started(self, step_id: str, label: str = ""):
        """Set current_step and status=in_progress."""
        self.data["current_step"] = step_id
        self.data["status"] = "in_progress"
        # Remove from blocked_steps if present
        self.data["blocked_steps"] = [
            b for b in self.data.get("blocked_steps", []) if b.get("step") != step_id
        ]

    def mark_step_passed(
        self,
        step_id: str,
        label: str,
        output_files: List[str],
        root_dir: str = ".",
    ):
        """Record a step as completed with output file hashes."""
        # Remove any existing entry for this step (idempotent update)
        self.data["completed_steps"] = [
            s for s in self.data.get("completed_steps", []) if s.get("step") != step_id
        ]

        # Build output_files with hashes
        hashed_outputs = []
        for rel_path in output_files:
            abs_path = os.path.join(root_dir, rel_path)
            file_hash = compute_file_hash(abs_path)
            entry = {"path": rel_path}
            if file_hash:
                entry["hash"] = file_hash
            hashed_outputs.append(entry)

        # Add completed step entry
        self.data["completed_steps"].append(
            {
                "step": step_id,
                "label": label,
                "completed_at": _iso_now(),
                "output_files": hashed_outputs,
                "gate_status": "passed",
            }
        )

        # Register artifacts
        for rel_path in output_files:
            abs_path = os.path.join(root_dir, rel_path)
            file_hash = compute_file_hash(abs_path)
            size = os.path.getsize(abs_path) if os.path.isfile(abs_path) else 0
            self.data["artifacts"][rel_path] = {
                "produced_by": step_id,
                "hash": file_hash,
                "size": size,
            }

        # Remove from blocked_steps
        self.data["blocked_steps"] = [
            b for b in self.data.get("blocked_steps", []) if b.get("step") != step_id
        ]

        # Update current_step and status
        self.data["current_step"] = step_id
        self.data["status"] = "in_progress"

    def mark_step_blocked(
        self,
        step_id: str,
        label: str,
        missing_files: List[str],
    ):
        """Record a step as blocked with missing prerequisites."""
        # Remove any existing blocked entry for this step
        self.data["blocked_steps"] = [
            b for b in self.data.get("blocked_steps", []) if b.get("step") != step_id
        ]

        self.data["blocked_steps"].append(
            {
                "step": step_id,
                "label": label,
                "reason": "missing prerequisites",
                "missing_files": missing_files,
            }
        )

        self.data["current_step"] = step_id
        self.data["status"] = "blocked"

    def set_resume(self, next_step: str, next_action: str):
        """Set the resume pointer for the next step."""
        self.data["resume"] = {
            "next_step": next_step,
            "next_action": next_action,
        }

    def set_stage(self, stage: str):
        """Set the current workflow stage (e.g. spec/report/plan)."""
        self.data["current_stage"] = stage

    def set_human_checkpoint(self, name: str, status: str, details: Optional[Dict] = None):
        """Record a human checkpoint (e.g. report_review, mode_selection)."""
        if "human_checkpoints" not in self.data:
            self.data["human_checkpoints"] = {}
        entry = {"status": status, "confirmed_at": _iso_now()}
        if details:
            entry.update(details)
        self.data["human_checkpoints"][name] = entry

    def mark_workflow_completed(self):
        """Mark the entire workflow as completed."""
        self.data["status"] = "completed"
        self.data["current_stage"] = "completed"

    # --- Persistence ---

    def save(self):
        """Write state to YAML file, creating parent directories as needed."""
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
