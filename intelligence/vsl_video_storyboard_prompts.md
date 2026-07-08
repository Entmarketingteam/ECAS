# ContractMotion: 2-Minute VSL Storyboard & Veo 3.1/Sora 2 Prompts
## B2B Signal-Based Outbound Lead Gen — Video Production Blueprint
**Prepared by:** Gemini CLI & Creative Engine
**Status:** Ready for Generation | **Target Models:** Google Veo 3.1, OpenAI Sora 2, Kling 2.5

---

## Executive Production Brief
*   **Video Concept:** "The Obscure Intercept." A highly polished, technical, and high-contrast B2B presentation that exposes how standard Apollo/LinkedIn scraping is dead, and visualizes how ContractMotion uses public registries (UCC-1, SAFER, HHS, GIS) to capture active buyer intent before anyone else.
*   **Visual Style:** Brutalist tech-noir. Deep obsidian (#0D1117) backdrops, glowing neon-green (#00FF94) vector grids, crisp cinematic close-ups of code, and modern high-end data visualization dashboards.
*   **Vibe:** Confident, scientific, premium, and disruptive (Russell Brunson "Hook-Story-Offer" structure).

---

## 🎬 Storyboard & Visual Prompts

### Scene 1: The Hook (0:00 - 0:15)
*   **Voiceover:** "If you’re a commercial operator doing $3M+, your outbound lead generation is broken. Your team is spamming dry, outdated lists from Apollo—and your buyers are completely ignoring them."
*   **Visual Action:** A dark, moody, cinematic macro shot of a hand slamming closed an old leather-bound corporate ledger. In the background, a terminal screen flashes with rows of red "DECLINED" and "SPAM" text in glowing monospace.
*   **Veo 3.1 / Sora 2 Prompt:**
    ```text
    Cinematic macro shot of a sleek modern workspace. Extreme close-up on a dark mechanical keyboard being typed on, shallow depth of field. In the background, a high-contrast monitor flashes with dense green and red terminal data. Vibe is high-tech, cyber-brutalist, moody lighting with neon green rim lighting on black matte textures. Photorealistic, 8k resolution, 24fps.
    ```

---

### Scene 2: The Core Mechanism (0:15 - 0:45)
*   **Voiceover:** "To win contracts in 2026, you have to target high-intent triggers. We don't use standard lists. We built proprietary scrapers that monitor state environmental violations, FMCSA truck registries, and county GIS appraiser footprints."
*   **Visual Action:** A beautiful, 3D rotating holographic globe made of neon-green vector grids. Zoom in rapidly to reveal a glowing node mapping out a physical commercial warehouse, overlaying flat-roof metrics and active local building permits in real-time.
*   **Veo 3.1 / Sora 2 Prompt:**
    ```text
    3D motion graphics animation of a glowing neon-green topographic laser grid scanning a large commercial industrial warehouse. High-end financial-tech visualization style. Digital data callouts, percentages, and vector lines overlaying the building in real-time. Clean black background, deep contrast, ultra-sharp focus, smooth corporate presentation speed.
    ```

---

### Scene 3: The Data Intercept (0:45 - 1:15)
*   **Voiceover:** "We know which hospital, facility, or commercial plant is facing an audit, preparing to relocate, or expanding their fleet *before* they ever publish an RFP. And we put your estimators directly onto their calendars."
*   **Visual Action:** A close-up cinematic shot of an engineering screen showing a Python terminal parsing DOT carrier databases, with names and verified emails flowing down like data-waterfalls, matching with a "Walkthrough Scheduled" calendar notice.
*   **Veo 3.1 / Sora 2 Prompt:**
    ```text
    Extreme close-up of a code editor screen, glowing white monospace text scrolling rapidly on a deep navy background. A neon green calendar event box slides into frame with the text "Walkthrough Scheduled: 10:00 AM". High contrast, rich details, cyber-noir aesthetic, shallow depth of field.
    ```

---

### Scene 4: The Sledgehammer Offer (1:15 - 2:00)
*   **Voiceover:** "We are so confident in this mechanism that we completely eliminate your risk. We will book you 5 qualified commercial meetings in 30 days, or you pay us zero. You only pay for qualified booked meetings. Click below, tell us your region, and we’ll send you 15 free signal-leads."
*   **Visual Action:** A clean, high-contrast, modern B2B analytics dashboard showing progress charts climbing from Week 1 to Week 4, with a large, glowing shield badge displaying: "100% Performance Guaranteed: 5 Meetings Booked."
*   **Veo 3.1 / Sora 2 Prompt:**
    ```text
    Clean modern B2B SaaS dashboard UI. Elegant white and neon green line charts climbing upwards over a 30-day timeline. A glassmorphic card floats over the center with a glowing green security shield and bold, crisp typography reading "5 MEETINGS GUARANTEED". Extremely sharp 3D render, smooth camera pan, premium dark-mode aesthetic.
    ```

---

## 🛠️ How to Generate & Deploy on Replicate
If you have your `REPLICATE_API_TOKEN` configured, you can call **Veo 3.1** or **Sora 2** directly via curl or our local python client. Here is the exact, copyable python script to trigger the generation of Scene 2 (The Core Mechanism) using Veo:

```python
import replicate
import os

# Ensure Replicate token is set
token = os.getenv("REPLICATE_API_TOKEN")
if not token:
    raise ValueError("REPLICATE_API_TOKEN env variable is missing.")

print("🚀 Dispatching Veo 3.1 High-Fidelity Video Generation...")

prediction = replicate.predictions.create(
    version="google/veo-3.1", # Target Veo 3.1
    input={
        "prompt": "3D motion graphics animation of a glowing neon-green topographic laser grid scanning a large commercial industrial warehouse. High-end financial-tech visualization style. Clean black background, deep contrast, ultra-sharp focus, smooth camera pan.",
        "aspect_ratio": "16:9",
        "duration": 5, # 5 seconds high-fidelity render
        "fps": 24,
        "negative_prompt": "blurry, low quality, cartoon, cheap, stocks, watermark, text, signature"
    }
)

print(f"Prediction created successfully! ID: {prediction.id}")
print(f"Status: {prediction.status}")
print("Follow output stream on Replicate dashboard.")
```
