# Tests for approval gate functionality
import pytest
from contractor.pipeline.approval_gate import apply_approval_gate, should_enroll

class MockContact:
    def __init__(self):
        self.approved_for_send = None
        self.email_verified = True


def test_approval_defaults():
    contact = MockContact()
    gated = apply_approval_gate(contact)
    assert gated.approved_for_send == False, "Should default to False"

def test_enrollment_blocking():
    contact = MockContact()
    contact.approved_for_send = False
    assert should_enroll(contact) == False, "Should block enrollment"

def test_enrollment_allowed():
    contact = MockContact()
    contact.approved_for_send = True
    assert should_enroll(contact) == True, "Should allow enrollment"

print("Basic tests defined")
