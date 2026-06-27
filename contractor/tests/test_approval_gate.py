from contractor.pipeline.approval_gate import (
    STOP_BEFORE_SEND,
    attach_approval_gate_to_lead,
    build_dry_run_approval_packet,
    should_enroll_in_smartlead,
)


def sample_lead():
    return {
        "id": "lead-123",
        "email": "ops@example-epc.com",
        "company_name": "Example EPC",
        "title": "VP Operations",
    }


def test_approval_packet_defaults_false_and_blocks_enrollment():
    packet = build_dry_run_approval_packet(
        lead=sample_lead(),
        source_signal={"source": "sam_gov", "contract": "Grid upgrade"},
        verifier_evidence={"entity_match": True, "email_valid": True, "signal_live": True},
        proposed_sequence={"campaign_id": "3005694", "sequence_name": "Power & Grid"},
        packet_id="approval-test-1",
    )

    assert packet.approved_for_send is False
    assert packet.stop_before_send == STOP_BEFORE_SEND
    assert should_enroll_in_smartlead(packet) is False
    payload = packet.to_dict()
    assert payload["lead"]["company_name"] == "Example EPC"
    assert payload["source_signal"]["source"] == "sam_gov"
    assert payload["verifier_evidence"]["signal_live"] is True
    assert payload["proposed_sequence"]["campaign_id"] == "3005694"


def test_only_explicit_true_approval_unlocks_enrollment():
    packet = build_dry_run_approval_packet(
        lead=sample_lead(),
        source_signal={},
        verifier_evidence={},
        proposed_sequence={},
    )
    payload = packet.to_dict()
    assert should_enroll_in_smartlead(payload) is False
    payload["approved_for_send"] = True
    assert should_enroll_in_smartlead(payload) is True


def test_attach_gate_to_lead_preserves_input_and_sets_human_gate():
    original = sample_lead()
    gated = attach_approval_gate_to_lead(original)

    assert original.get("approved_for_send") is None
    assert gated["approved_for_send"] is False
    assert gated["reviewer_gate"] == "human_approval_required"
    assert gated["email"] == original["email"]
