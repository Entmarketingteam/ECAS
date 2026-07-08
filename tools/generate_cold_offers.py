import os
import re
import glob

NICHES_DIR = "projects/ECAS/intelligence/niches"

def clean_markdown_headers(text):
    return re.sub(r'#+\s+', '', text).strip()

def extract_niche_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Get directory name as fallback for niche name
    dir_name = os.path.basename(os.path.dirname(file_path))
    niche_name = dir_name.replace("-", " ").title()

    # Try to extract the H1 title
    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1_match:
        niche_name = h1_match.group(1).split("—")[0].split(":")[0].strip()

    # Extract Average Project Value / Deal Size
    deal_size = "Unknown"
    deal_size_match = re.search(r'(?:Project Value|Average Project Value|Avg Project Value|deal size|contract value|LTV).*?(\$[0-9,]+K?(?:\s*-\s*\$[0-9,]+K?)?)', content, re.IGNORECASE)
    if deal_size_match:
        deal_size = deal_size_match.group(1)
    else:
        # Check table formats
        table_matches = re.findall(r'\|\s*(?:Typical Project Value|Avg Project Value|Typical Project Value \(Purge\)|Project Value|Average Project Value|Avg\. Project Value).*?\|\s*(\$[0-9,]+K?(?:\s*-\s*\$[0-9,]+K?)?)\s*\|', content, re.IGNORECASE)
        if table_matches:
            deal_size = table_matches[0].strip()
        else:
            # Look for general numbers
            table_matches_2 = re.findall(r'(\$[0-9,]+(?:\s*-\s*\$[0-9,]+)?(?:\s*per\s*study|K)?)', content)
            if table_matches_2:
                deal_size = table_matches_2[0].strip()

    # Extract Target Persona (ICP)
    target_persona = "Owner / CEO"
    persona_match = re.search(r'(?:Decision Maker|Target Persona|ICP|Stakeholders|CFO|COO|Facility Manager|Compliance Officer).*?([A-Z][a-zA-Z\s,]+(?:Director|Officer|Manager|CEO|Owner|CFO|COO|Estimator))', content, re.IGNORECASE)
    if persona_match:
        target_persona = persona_match.group(1).strip()
    else:
        # Search Part 2 or Part 11 for Stakeholders
        part2_match = re.search(r'## Part 2:.*?(?:Decision Maker|Stakeholder).*?([\s\S]*?)(?:## Part 3|## Part 10|\n\n\n)', content, re.IGNORECASE)
        if part2_match:
            lines = part2_match.group(1).split("\n")
            for line in lines:
                if "Decision Maker" in line or "COO" in line or "CFO" in line or "Manager" in line:
                    target_persona = line.replace("*", "").replace("-", "").strip()
                    break

    # Extract Jargon Terms (usually Part 7)
    jargon_terms = []
    part7_match = re.search(r'## Part 7:.*?(?:Vocabulary|Fluency).*?([\s\S]*?)(?:## Part 8|## Part 10|\n\n\n)', content, re.IGNORECASE)
    if part7_match:
        # Find terms in table format
        terms = re.findall(r'\|\s*\*\*?([a-zA-Z0-9\s\-/]+)\*\*?\s*\|', part7_match.group(1))
        if terms:
            jargon_terms = [t.strip() for t in terms[:4]]
    
    if not jargon_terms:
        # Fallback jargon search
        jargon_terms = ["Compliance", "Audit Trail", "Route Density", "LTV"]

    # Extract Core Pain Point (usually Part 10 or Executive Summary)
    pain_point = "Finding predictable new clients beyond referrals."
    part10_match = re.search(r'## Part 10:.*?(?:Pain Points).*?([\s\S]*?)(?:## Part 11|## Part 12|## Part 13|\n\n\n)', content, re.IGNORECASE)
    if part10_match:
        lines = [l.strip() for l in part10_match.group(1).split("\n") if l.strip() and (l.strip().startswith("-") or l.strip().startswith("*") or l.strip().startswith("1."))]
        if lines:
            pain_point = lines[0].replace("*", "").replace("-", "").strip()
            # Clean up numbering
            pain_point = re.sub(r'^\d+\.\s*', '', pain_point)
    else:
        # Check Exec Summary
        exec_match = re.search(r'## Executive Summary([\s\S]*?)(?:## Part 1|\n\n\n)', content, re.IGNORECASE)
        if exec_match:
            lines = [l.strip() for l in exec_match.group(1).split("\n") if "pain" in l.lower() or "fear" in l.lower() or "rely" in l.lower() or "relying" in l.lower()]
            if lines:
                pain_point = lines[0].strip()

    return {
        "file_path": file_path,
        "niche_name": niche_name,
        "deal_size": deal_size,
        "target_persona": target_persona,
        "jargon_terms": jargon_terms,
        "pain_point": pain_point
    }

def generate_fazio_offer(niche):
    name = niche["niche_name"]
    persona = niche["target_persona"]
    deal = niche["deal_size"]
    pain = niche["pain_point"]
    jargon = niche["jargon_terms"]

    # Clean up persona format
    persona_clean = "Business Owners"
    if "CFO" in persona or "C-Suite" in persona:
        persona_clean = "CFOs & Controllers"
    elif "Facility" in persona or "Plant" in persona or "Maintenance" in persona:
        persona_clean = "Facility Directors & Plant Integrity Engineers"
    elif "Compliance" in persona:
        persona_clean = "Compliance Officers & COOs"
    elif "Commercial" in persona:
        persona_clean = "Commercial Property Managers"
    elif "CEO" in persona or "Owner" in persona:
        persona_clean = f"{name} Owners"

    # Specific offers tailored per niche
    if "Shredding" in name or "Destruction" in name:
        dream_outcome = f"intercept 3-5 multi-site hospital or financial document destruction contracts ({deal}) before the national companies (Iron Mountain/Stericycle) even hear about the RFP."
        offer_angle = f"We will build your localized healthcare compliance data moat and warm outreach sequence. If you don't book at least 3 qualified discovery calls with compliance directors in 45 days, you pay zero."
        lead_magnet = f"A customized list of 15 local healthcare facilities with upcoming Certificate of Need filings or rolling service contract renewals."
    elif "Roofing" in name:
        dream_outcome = f"add $150k+ in commercial roof restoration or recurring maintenance contracts without competing on low-margin public bids or storm chasing."
        offer_angle = f"We build a targeted outbound campaign mapping high-intent warehouse property portfolios in your state. You only pay a flat fee per qualified meeting booked with a property manager."
        lead_magnet = f"A pre-screened list of 20 industrial park facilities with roofs older than 15 years and active business licenses in your area."
    elif "Pest Control" in name:
        dream_outcome = f"secure 5-10 high-value commercial accounts (restaurants, warehouses, multi-family) worth $5k-$30k/yr on recurring contracts."
        offer_angle = f"We launch Google Ads & direct local ABM targeting facility managers. Pay on performance — only $150 per commercial lead that requests a property walkthrough."
        lead_magnet = f"An audit of your top 3 local competitors' active search keywords and a custom commercial pitch deck template."
    elif "NDT" in name or "Inspection" in name:
        dream_outcome = f"get your firm on the preferred contractor list for scheduled turnaround schedules at refineries and chemical plants."
        offer_angle = f"We target Plant Reliability Engineers & Turnaround Planners using specific technical language ({', '.join(jargon[:2])}). We guarantee 3 qualified facility walkthrough bookings in 60 days or a 100% refund."
        lead_magnet = f"A localized database of 12 regional industrial plants with scheduled shutdowns or regulatory compliance audits in the next 6 months."
    elif "Tax Credit" in name:
        dream_outcome = f"add $50k-$200k in high-contingency-fee R&D tax credit studies beyond your current CPA referral network."
        offer_angle = f"We run an outbound email campaign targeting CFOs at $10M+ tech and manufacturing companies. Pay-per-performance: $350 per qualified discovery call booked, no monthly retainer."
        lead_magnet = f"A custom list of 40 regional software & advanced manufacturing companies with active engineering hiring listings (strong indicator of R&D)."
    else:
        # General B2B Daniel Fazio offer builder
        dream_outcome = f"add $100k+ in high-margin contract value by booking direct discovery calls with {persona_clean} who need your specialized services."
        offer_angle = f"We set up your outbound infrastructure, warm the inboxes, and write the scripts using {jargon[0] if jargon else 'compliance'} trust triggers. We'll book you 5 qualified meetings in your first 30 days or you don't pay a dime."
        lead_magnet = f"A curated list of 15 high-intent local accounts that meet your exact qualification criteria, complete with verified contact info."

    return {
        "dream_outcome": dream_outcome,
        "offer_angle": offer_angle,
        "lead_magnet": lead_magnet,
        "persona_clean": persona_clean
    }

def main():
    print("Scanning niches...")
    pattern = os.path.join(NICHES_DIR, "**", "*report.md")
    report_files = glob.glob(pattern, recursive=True)
    
    # Also find files matching *Report.md
    pattern_caps = os.path.join(NICHES_DIR, "**", "*Report.md")
    report_files.extend(glob.glob(pattern_caps, recursive=True))
    
    # Deduplicate paths
    report_files = list(set(report_files))
    
    print(f"Found {len(report_files)} niche files.")
    
    gpt_inputs_content = """# Custom GPT Niche Information Packages (Daniel Fazio Offer Ideator)
This file is generated by Gemini CLI as a structured "copy-paste" cheat sheet. Use these pre-packaged niche context files to feed directly into the Custom GPT [Daniel Fazio - Offer Ideator](https://chatgpt.com/g/g-690c9b47a98c819180ffcc6332db2372-daniel-fazio-offer-ideator).

## How to use this file
1. Open this file in your editor.
2. Scroll to the niche you want to generate offers for.
3. Copy the markdown block labeled **[COPY-PASTE GPT CONTEXT]**.
4. Paste it directly into the ChatGPT chat bar.
5. The Custom GPT will instantly produce ultra-specific Daniel Fazio style offers, email scripts, and handles.

---
"""

    fazio_offers_content = """# Daniel Fazio Style Cold Traffic Offers — Complete ECAS Niches Database
Generated autonomously by Gemini CLI. Built using the core "Cold Email Wizard" offer framework: High-Specificity + Risk-Reversal + Perceived Likelihood of Achievement + Low Friction.

## The Daniel Fazio Offer Framework:
1. **Target Specificity:** Do not target "B2B." Target exact personas (e.g., "Plant Reliability Engineers during turnaround planning").
2. **Dream Outcome:** Focus on high-value contracts or ROI (e.g., "Add $150k in warehouse re-roofing projects").
3. **Risk Reversal:** Move the risk entirely to your agency ("Pay per qualified meeting," "Zero monthly retainer," "5 meetings in 30 days or 100% refund").
4. **Low-Friction Hook (The "Bribe"):** Lead with high-value assets ("Can I send you a custom list of 15 regional facilities with active HVAC permits?").

---
"""

    summary_table = """## Quick Reference Offer Matrix (Best Cold Traffic Niches)

| Niche Name | Target Persona | Dream Outcome | Risk-Reversed Offer Angle | Low-Friction Bribe |
| :--- | :--- | :--- | :--- | :--- |
"""

    for file_path in sorted(report_files):
        try:
            niche = extract_niche_data(file_path)
            offer = generate_fazio_offer(niche)
            
            # Append to Custom GPT context
            jargon_str = ", ".join(niche["jargon_terms"]) if niche["jargon_terms"] else "Compliance, Audit-Trail"
            
            gpt_inputs_content += f"""
### Niche: {niche["niche_name"]}
```markdown
[COPY-PASTE GPT CONTEXT]
Niche Name: {niche["niche_name"]}
Ideal Customer Profile (ICP): {offer["persona_clean"]}
Average Deal Size / LTV: {niche["deal_size"]}
Core Pain Point: {niche["pain_point"]}
Key Industry Jargon/Trust Badges: {jargon_str}
Core Offer Goal: Generate predictable booked appointments using cold traffic.
Fazio Style Directives: Create 3 high-converting cold email offers with extreme risk-reversal (e.g., pay per booked meeting, performance-based pilot, or 100% money-back guarantee).
```
---
"""

            # Append to Fazio local offers database
            fazio_offers_content += f"""
### 🎯 Niche: {niche["niche_name"]}
*   **Target Persona:** {offer["persona_clean"]}
*   **Average Project Size/LTV:** {niche["deal_size"]}
*   **Core Pain Point:** *"{niche["pain_point"]}"*
*   **Industry Vocabulary:** `{jargon_str}`

#### Daniel Fazio Style No-Brainer Offers:

1. **The Performance-Based Lead Generator (Highest Cold Response)**
   *   **Offer Hook:** "We will book you 5 qualified discovery calls with {offer["persona_clean"]} who need immediate help with {niche["jargon_terms"][0] if niche["jargon_terms"] else 'compliance'} or we don't charge you a single penny."
   *   **Email Pitch:** "We've built an active pipeline of local accounts. We handle the entire cold email setup, scraping, and copywriting. You only pay $300-$500 per qualified meeting booked. No retainer."

2. **The "High-Intent Bribe" Outreach Angle (Instant Trust)**
   *   **Offer Hook:** "Hey [First Name], we mapped out {offer["lead_magnet"][:-1].lower()}. Can I send you the list for free?"
   *   **Next Step:** When they reply "yes," send them the list along with a brief Loom video explaining how you target their specific needs using `{niche["jargon_terms"][1] if len(niche["jargon_terms"]) > 1 else 'compliance log'}`.

3. **The Risk-Free Pilot Offer**
   *   **Offer Hook:** "{offer["offer_angle"]}"
   *   **Outcome:** Intercepts {offer["dream_outcome"]}

---
"""

            summary_table += f"""| **{niche["niche_name"]}** | {offer["persona_clean"]} | {offer["dream_outcome"][:80]}... | {offer["offer_angle"][:70]}... | {offer["lead_magnet"][:50]}... |
"""
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    # Write the files
    with open("projects/ECAS/intelligence/niches_gpt_inputs.md", "w", encoding="utf-8") as f:
        f.write(gpt_inputs_content)
        
    with open("projects/ECAS/intelligence/daniel_fazio_offers.md", "w", encoding="utf-8") as f:
        f.write(fazio_offers_content + "\n\n" + summary_table)

    print("Success! Generated files.")

if __name__ == "__main__":
    main()
