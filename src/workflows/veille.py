"""Briefing quotidien sur Vallourec, Coface, Bolloré et Safran."""

import html
import re
from datetime import date
from typing import Dict, List

import httpx
from pydantic import BaseModel, Field

import mistralai.workflows as workflows

DEFAULT_COMPANIES = ["Vallourec", "Coface", "Bolloré", "Safran"]
MAX_HEADLINES_PER_COMPANY = 12
BRIEFING_MODEL = "mistral-small-latest"


class BriefingInput(BaseModel):
    companies: List[str] = Field(default_factory=lambda: list(DEFAULT_COMPANIES))


def _extract(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", text, re.S)
    if not match:
        return ""
    return html.unescape(match.group(1)).strip()


@workflows.activity(name="fetch-company-news")
async def fetch_company_news(company: str) -> List[Dict[str, str]]:
    """Récupère les dernières actualités d'une société via Google News RSS (édition France)."""
    params = {"q": company, "hl": "fr", "gl": "FR", "ceid": "FR:fr"}
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get("https://news.google.com/rss/search", params=params)
            resp.raise_for_status()
            xml = resp.text
    except Exception as exc:  # noqa: BLE001
        return [{"company": company, "title": f"Erreur de récupération : {exc}"}]

    headlines: List[Dict[str, str]] = []
    for item in re.findall(r"<item>(.*?)</item>", xml, re.S)[:MAX_HEADLINES_PER_COMPANY]:
        headlines.append(
            {
                "company": company,
                "title": _extract(item, "title"),
                "source": _extract(item, "source"),
                "published": _extract(item, "pubDate"),
                "link": _extract(item, "link"),
            }
        )
    return headlines


@workflows.activity(name="generate-briefing")
async def generate_briefing(all_news: Dict[str, List[Dict[str, str]]]) -> str:
    """Synthétise les titres collectés en un briefing structuré en français."""
    today = date.today().isoformat()
    raw_lines: List[str] = []
    for company, headlines in all_news.items():
        raw_lines.append(f"## {company}")
        for h in headlines:
            meta = f" ({h.get('source')}, {h.get('published')})" if h.get("source") else ""
            raw_lines.append(f"- {h.get('title')}{meta}")
        raw_lines.append("")

    raw_news = "\n".join(raw_lines)
    system_prompt = (
        "Tu es un analyste financier. Rédige un briefing quotidien en français, "
        "en Markdown, structuré par société. Pour chaque société : les faits "
        "marquants (résultats financiers, contrats, actualités réglementaires ou "
        "politiques, mouvements d'action et événements à venir), puis une ligne "
        "de synthèse. Ne mentionne que des informations présentes dans les "
        "titres fournis, sans rien inventer. Termine par une courte section "
        "« À surveiller ». Garde le briefing factuel et concis."
    )
    user_prompt = f"Date du briefing : {today}.\n\nTitres d'actualités récents :\n\n{raw_news}"

    try:
        from mistralai.client import Mistral

        client = Mistral()
        resp = client.chat.complete(
            model=BRIEFING_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content or raw_news
    except Exception:  # noqa: BLE001 — repli : retourner les titres bruts
        return (
            f"# Briefing du {today} (titres bruts, synthèse indisponible)\n\n"
            + raw_news
        )


@workflows.workflow.define(
    name="veille-bourse-briefing",
    workflow_display_name="Briefing bourse quotidien",
    workflow_description=(
        "Génère un briefing quotidien des informations importantes sur "
        "Vallourec, Coface, Bolloré et Safran."
    ),
)
class BriefingWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: BriefingInput) -> str:
        all_news: Dict[str, List[Dict[str, str]]] = {}
        for company in input.companies:
            all_news[company] = await fetch_company_news(company)
        return await generate_briefing(all_news)
