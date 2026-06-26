import { DatabaseService } from './database.service';
import { OpenaiService } from './openai.service';

interface VerificationRule {
  type: 'icp_match' | 'intent_signal' | 'contact_validation' | 'domain_verification';
  oracle: string;
  confidenceThreshold: number;
  required: boolean;
}

export class LeadVerificationService {
  private readonly rules: VerificationRule[] = [
    {
      type: 'icp_match',
      oracle: 'Gemini ICP Match Analysis',
      confidenceThreshold: 70,
      required: true
    },
    {
      type: 'intent_signal',
      oracle: 'Recent Purchase Intent Signals',
      confidenceThreshold: 60,
      required: false
    },
    {
      type: 'contact_validation',
      oracle: 'Contact Information Validation',
      confidenceThreshold: 80,
      required: true
    },
    {
      type: 'domain_verification',
      oracle: 'Email Domain Verification',
      confidenceThreshold: 85,
      required: true
    }
  ];

  constructor(
    private readonly db: DatabaseService,
    private readonly openai: OpenaiService
  ) {}

  async verifyLead(leadId: string): Promise<void> {
    // Get the raw lead
    const lead = await this.db.getLeadById(leadId);
    if (!lead) {
      throw new Error(`Lead ${leadId} not found`);
    }

    // Run through verification pipeline
    const evidence: any[] = [];
    let isVerified = true;
    let needsReview = false;
    let verificationReason = '';

    for (const rule of this.rules) {
      try {
        const evidenceResult = await this.runOracle(lead, rule);
        evidence.push(evidenceResult);
        
        // Save evidence to database
        await this.db.createLeadEvidence({
          leadId: lead.id,
          oracleType: rule.type,
          evidenceData: evidenceResult.evidence,
          confidenceScore: evidenceResult.confidence,
          isVerifiable: evidenceResult.isVerifiable,
          verifiedAt: new Date()
        });

        // Check if rule passes
        if (rule.required && evidenceResult.confidence < rule.confidenceThreshold) {
          isVerified = false;
          verificationReason += `Failed ${rule.type} (confidence: ${evidenceResult.confidence}% < ${rule.confidenceThreshold}%), `;
        }
        
        if (evidenceResult.needsReview) {
          needsReview = true;
        }
      } catch (error) {
        console.error(`Oracle ${rule.oracle} failed for lead ${leadId}:`, error);
        evidence.push({
          oracleType: rule.type,
          error: error.message,
          confidence: 0,
          isVerifiable: false
        });
      }
    }

    // Create verification verdict
    const verdict = await this.db.createLeadVerdict({
      leadId: lead.id,
      isVerified,
      verificationReason: verificationReason || 'All verification checks passed',
      evidenceSummary: evidence,
      needsReview
    });

    // Queue for publication if verified
    if (isVerified && !needsReview) {
      await this.db.addToPublicationQueue({
        leadId: lead.id,
        verdictId: verdict.id
      });
    }

    console.log(`Lead ${leadId} verification complete: ${isVerified ? 'Verified' : 'Failed'}`);
  }

  private async runOracle(lead: any, rule: VerificationRule): Promise<any> {
    // Simplified oracle logic - in real implementation this would call specific verification methods
    const prompt = `Analyze this lead for ${rule.oracle}:
Lead: ${JSON.stringify(lead, null, 2)}
Provide structured JSON output including evidence, confidence score (0-100), and whether manual review is needed.`;

    try {
      const result = await this.openai.completion({
        model: 'gpt-4',
        prompt,
        temperature: 0.3,
        max_tokens: 500,
        stop: ['###']
      });

      // Parse and validate the response
      const parsed = JSON.parse(result.choices[0].text);
      return {
        oracleType: rule.type,
        evidence: parsed.evidence,
        confidence: parsed.confidence,
        isVerifiable: parsed.confidence >= rule.confidenceThreshold,
        needsReview: parsed.needsReview || false
      };
    } catch (error) {
      console.error(`Oracle ${rule.oracle} failed:`, error);
      return {
        oracleType: rule.type,
        evidence: {},
        confidence: 0,
        isVerifiable: false,
        needsReview: true
      };
    }
  }

  async processPublicationQueue(): Promise<void> {
    const pendingLeads = await this.db.getPendingPublicationQueue();
    
    for (const pending of pendingLeads) {
      // In real implementation: publish to CRM, marketing automation, etc.
      console.log(`Publishing verified lead ${pending.lead_id}`);
      
      // Mark as published
      await this.db.markPublished(pending.lead_id);
    }
  }
}