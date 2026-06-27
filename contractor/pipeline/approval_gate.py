"""Dry-run approval gate before Smartlead enrollment.

This module is intentionally pure: no Smartlead calls, no Airtable writes, no
network. It builds the packet a human reviews before any lead can be enrolled.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Mapping

STOP_BEFORE_SEND = "STOP BEFORE SEND: human approval is required before Smartlead enrollment."


@dataclass(frozen=True)
class ApprovalPacket:
    packet_id: str
    approved_for_send: bool
    stop_before_send: str
    lead: dict[str, Any]
    source_signal: dict[str, Any]
    verifier_evidence: dict[str, Any]
    proposed_sequence: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def approval_default() -> bool:
    """All approval packets default to not approved for send."""
    return False


def should_enroll_in_smartlead(packet: ApprovalPacket | Mapping[str, Any]) -> bool:
    """Only an explicit true approval unlocks downstream enrollment code."""
    if isinstance(packet, ApprovalPacket):
        return packet.approved_for_send is True
    return packet.get("approved_for_send") is True


def build_dry_run_approval_packet(
    *,
    lead: Mapping[str, Any],
    source_signal: Mapping[str, Any],
    verifier_evidence: Mapping[str, Any],
    proposed_sequence: Mapping[str, Any],
    packet_id: str | None = None,
) -> ApprovalPacket:
    lead_id = str(lead.get("id") or lead.get("email") or lead.get("company_name") or "unknown")
    generated_id = packet_id or f"approval-{lead_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    return ApprovalPacket(
        packet_id=generated_id,
        approved_for_send=approval_default(),
        stop_before_send=STOP_BEFORE_SEND,
        lead=dict(lead),
        source_signal=dict(source_signal),
        verifier_evidence=dict(verifier_evidence),
        proposed_sequence=dict(proposed_sequence),
    )


def attach_approval_gate_to_lead(lead: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of a lead with explicit send approval locked false."""
    gated = dict(lead)
    gated["approved_for_send"] = False
    gated["reviewer_gate"] = "human_approval_required"
    return gated
