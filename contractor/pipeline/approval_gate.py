import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from contractor.pipeline.orchestrator import EnrichedContact

DEFAULT_SEND_APPROVAL = False

# Smartlead sequence preview (mapped by vertical)
SMARTLEAD_SEQUENCE_MAP = {
    "epc_power_grid": [
        {"day": 0, "subject": "[Grid Modernization] Why we're signaling your team"},
        {"day": 4, "subject": "[Infrastructure] Top 3 capacity risks in your territory"},
        {"day": 9, "subject": "[Re: Your FERC filing] How we complement your EPC play"},
    ]
}

def create_dry_run_packet(
    contact: EnrichedContact,
    source_signals: List[dict],
    verification_evidence: dict,
) -> Dict[str, Any]:
    return {
        "approval_id": f"APPROVE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "approved_for_send": contact.approved_for_send,
        "contact": {
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "title": contact.title,
        },
        "signals": source_signals,
        "verification": verification_evidence
    }

def apply_approval_gate(contact: EnrichedContact) -> EnrichedContact:
    contact.approved_for_send = DEFAULT_SEND_APPROVAL
    return contact

def should_enroll(contact: EnrichedContact) -> bool:
    if not contact.approved_for_send:
        return False
    return True

def approval_gate_pipeline_integration(
    contact: EnrichedContact,
    source_signals: List[dict]
) -> Optional[dict]:
    gated_contact = apply_approval_gate(contact)
    packet = create_dry_run_packet(
        gated_contact,
        source_signals,
        {"icp_score": contact.icp_score, "signal_score": contact.signal_score}
    )
    return packet
