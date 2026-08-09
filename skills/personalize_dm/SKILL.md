---
name: personalize_dm
description: Generate a personalized Instagram or TikTok DM for a creator prospect using live data
---

# Personalize DM

## Inputs required
- prospect handle
- platform (instagram or tiktok)
- recent post description or caption
- follower count
- niche
- proposed partnership angle

## Output
A short DM (under 120 words) that:
1. Opens with a specific reference to their recent content or style
2. Names ENT Agency briefly
3. States the value proposition (access to brand deals in their niche)
4. Single clear CTA ("Would you be open to a quick call?")

## Do not
- Use emojis unless the creator's style uses them heavily
- Mention commission rates
- Make income guarantees
- Use their full name (handle only)
- Send if consent_log shows opted_out or do_not_contact

## Token rule
- Use Haiku first
- If VerifierAgent returns CONFIDENCE < 70, escalate to Sonnet
- Max 2 Sonnet attempts before human escalation
