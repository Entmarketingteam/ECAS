import subprocess
from firecrawl import FirecrawlApp
from firecrawl.v2.types import ScrapeOptions

api_key = subprocess.run(
    ["doppler", "secrets", "get", "FIRECRAWL_API_KEY", "--project", "ent-agency-automation", "--config", "dev", "--plain"],
    capture_output=True, text=True
).stdout.strip()

app = FirecrawlApp(api_key=api_key)

print("Starting crawl of https://help.smartlead.ai/ (up to 200 pages)...")

result = app.crawl(
    "https://help.smartlead.ai/",
    limit=200,
    scrape_options=ScrapeOptions(formats=["markdown"]),
    poll_interval=5
)

pages = result.data if hasattr(result, 'data') else []

print(f"Crawled {len(pages)} pages. Writing markdown...")

output_lines = []
output_lines.append("# Smartlead Help Documentation\n")
output_lines.append("*Scraped on: 2026-02-11*\n")
output_lines.append("*Source: https://help.smartlead.ai/*\n\n")
output_lines.append("---\n\n")

for i, page in enumerate(pages):
    title = f"Page {i+1}"
    url = ""
    md = ""

    if hasattr(page, 'metadata') and page.metadata:
        meta = page.metadata
        if isinstance(meta, dict):
            title = meta.get("title", meta.get("ogTitle", title))
            url = meta.get("sourceURL", meta.get("url", ""))
        else:
            title = getattr(meta, 'title', None) or getattr(meta, 'ogTitle', None) or title
            url = getattr(meta, 'sourceURL', None) or getattr(meta, 'url', "") or ""

    if hasattr(page, 'markdown') and page.markdown:
        md = page.markdown
    elif isinstance(page, dict):
        md = page.get("markdown", "")

    output_lines.append(f"## {title}\n")
    if url:
        output_lines.append(f"**URL:** {url}\n\n")
    if md:
        output_lines.append(md)
    output_lines.append("\n\n---\n\n")

output = "\n".join(output_lines)

with open("/Users/ethanatchley/Desktop/smartlead_help_docs.md", "w", encoding="utf-8") as f:
    f.write(output)

print(f"Done! {len(pages)} pages saved to ~/Desktop/smartlead_help_docs.md")
