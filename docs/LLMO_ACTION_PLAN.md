# LLMO (Large Language Model Optimization) — Action Plan

LLMO is the 2026 analogue of SEO: optimize so that models like Gemini **know** and **recommend** your software house and products, and use the same ecosystem internally for productivity.

This doc maps the two-sided strategy to InsightShop and next steps.

---

## 1. Optimize Your Company for Gemini (“SEO of 2026”)

### Done in this repo

| Action | Status | Where |
|--------|--------|--------|
| **Structured data (JSON-LD)** | Done | `frontend/public/index.html`: Organization, SoftwareApplication, WebSite (schema.org) |
| **Documentation for bots** | Done | `/robots.txt` and `/ai-info.txt` served by Flask from `llmo/`; allow `Google-Extended` |
| **Machine-readable tech stack** | Done | `llmo/ai-info.txt`: stack, API surface, docs pointers |

### You should do

| Action | Notes |
|--------|--------|
| **Set production base URL** | Replace `https://insightshop.example.com` in `index.html` JSON-LD and in `llmo/robots.txt` (Sitemap URL) and `llmo/ai-info.txt` with your real domain. |
| **Expertise-first content** | Add case studies, whitepapers, or open-source docs; Gemini prefers “grounded” proof that you can build. |
| **Code citations** | Contribute to GitHub; high-star repos or contributions to major frameworks help models cite you. |
| **Sitemap** | Add a real `/sitemap.xml` and keep the `Sitemap:` line in `robots.txt` pointing to it. |

---

## 2. Internal “Gemini Transformation” (Productivity)

### Suggested tech stack (2026)

| Component | Suggestion |
|-----------|------------|
| **Model** | Gemini 3 Pro (reasoning) or Gemini 2.5 Flash (speed) |
| **IDE** | Gemini Code Assist or Cursor (e.g. via Gemini API) |
| **Agents** | LangGraph or CrewAI for Jira/PR/Slack workflows |
| **Knowledge base** | RAG with Vertex AI Vector Search over company docs |

### Immediate action plan

1. **API access**  
   Get an API key from [Google AI Studio](https://aistudio.google.com/) for testing Gemini (e.g. multimodal, long context).

2. **Minimum Viable Agent (MVA)**  
   Build a small internal tool that:
   - Scans GitHub PRs
   - Uses Gemini to check security/style
   - Posts a summary to Slack/Teams

3. **RAG for legacy code**  
   Index existing code in a vector DB so developers can ask: “Did we ever build a payment gateway for Stripe in 2023? Give me the boilerplate,” and get **your** code, not generic examples.

4. **Token window**  
   Use Gemini’s large context (e.g. 10M+ tokens) to upload full codebase for architecture/refactor questions when needed.

---

## 3. Files touched in this repo

- **`frontend/public/index.html`** — JSON-LD `@graph` (Organization, SoftwareApplication, WebSite).
- **`llmo/robots.txt`** — Allow `*` and `Google-Extended`; Sitemap URL (replace domain).
- **`llmo/ai-info.txt`** — Plain-text summary for AI crawlers (product, stack, API, docs).
- **`app.py`** — Routes `GET /robots.txt` and `GET /ai-info.txt` (served before SPA catch-all).

---

## 4. References

- [Google crawlers (incl. Google-Extended)](https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers)
- [Schema.org](https://schema.org/) (Organization, SoftwareApplication, WebSite)
- Google AI Studio, Vertex AI, and Gemini API docs for keys and RAG/agent patterns.
