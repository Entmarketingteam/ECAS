import json
import time
import os
from datetime import datetime

# Add this import
try:
    from contractor.pipeline.approval_gate import approval_gate_pipeline_integration
    APPROVAL_GATE_AVAILABLE = True
except ImportError:
    APPROVAL_GATE_AVAILABLE = False
    print("Warning: Approval gate not available")

class SimplifiedOrchestrator:
    """
    Simplified version demonstrating the approval gate integration pattern
    """
    
    def __init__(self):
        self.approval_gate_enabled = APPROVAL_GATE_AVAILABLE
    
    def process_lead(self, lead_data):
        """Process a lead through the pipeline"""
        # For demo purposes - in real implementation this would be a full EnrichedContact
        mock_contact = type('MockContact', (), {
            'approved_for_send': None,
            'email': lead_data.get('email', 'test@example.com'),
            'first_name': lead_data.get('first_name', 'John'),
            'last_name': lead_data.get('last_name', 'Doe'),
            'title': lead_data.get('title', 'CEO'),
            'company_name': lead_data.get('company_name', 'Test Corp'),
            'vertical': lead_data.get('vertical', 'epc_power_grid'),
            'email_verified': True
        })()
        
        mock_signals = [{'type': 'test_signal', 'source': 'demo'}]
        
        if self.approval_gate_enabled:
            print(f"Using approval gate for: {mock_contact.email}")
            result = approval_gate_pipeline_integration(mock_contact, mock_signals)
            
            if result:
                print(f"APPROVAL PACKET CREATED: {result.get('approval_id')}")
                return result
            else:
                print("Lead auto-enrolled (no approval needed)")
                return {"status": "enrolled", "email": mock_contact.email}
        else:
            # Fallback behavior without approval gate
            print("Bypassing approval gate (not available)")
            return {"status": "bypassed", "email": mock_contact.email}

    def demo_run(self):
        """Demo the pipeline functionality"""
        test_leads = [
            {'email': 'demo1@example.com', 'first_name': 'Demo1'},
            {'email': 'demo2@example.com', 'first_name': 'Demo2'}
        ]
        
        results = []
        for lead in test_leads:
            result = self.process_lead(lead)
            results.append(result)
            time.sleep(0.5)  # Small delay
        
        return results

if __name__ == "__main__":
    orchestrator = SimplifiedOrchestrator()
    print("Demo run starting...")
    results = orchestrator.demo_run()
    
    print("\n" + "="*50)
    print("DEMO RESULTS:")
    for i, result in enumerate(results):
        print(f"Lead {i+1}: {result}")
    print("="*50)
    
    print(f"Approval gate available: {APPROVAL_GATE_AVAILABLE}")
    print("Demo completed.")