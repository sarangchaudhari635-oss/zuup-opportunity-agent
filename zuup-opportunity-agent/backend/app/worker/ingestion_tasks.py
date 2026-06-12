"""
Opportunity Ingestion Pipeline — Scrapers for all configured sources.
Each ingester fetches, normalizes, deduplicates, embeds and stores opportunities.
"""
import asyncio
import hashlib
from datetime import datetime, timezone

import feedparser
import httpx
import structlog
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import Eligibility, Opportunity, OpportunityType, FundingType
from app.services.embedding_service import (
    build_opportunity_embedding_text, generate_embedding,
)
from app.services.resume_parser import normalize_opportunity_description
from app.worker.celery_app import celery_app

logger = structlog.get_logger()

HEADERS = {"User-Agent": settings.scraper_user_agent}


# ─────────────────────────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────────────────────────

def compute_content_hash(title: str, organization: str, deadline: datetime | None) -> str:
    deadline_str = deadline.isoformat() if deadline else "no-deadline"
    raw = f"{title.lower().strip()}|{organization.lower().strip()}|{deadline_str}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def opportunity_exists(db, content_hash: str) -> bool:
    return db.query(Opportunity).filter(Opportunity.content_hash == content_hash).first() is not None


# ─────────────────────────────────────────────────────────────
# INGEST ONE OPPORTUNITY
# ─────────────────────────────────────────────────────────────

async def ingest_opportunity(
    db,
    title: str,
    organization: str,
    description: str,
    opp_type: OpportunityType,
    url: str,
    source_name: str,
    deadline: datetime | None = None,
    funding_type: FundingType | None = None,
    funding_amount: str | None = None,
    location: str | None = None,
    remote_eligible: bool = False,
    eligibility_data: dict | None = None,
) -> bool:
    """
    Full pipeline for a single opportunity:
    1. Quality check (description length, future deadline, valid URL)
    2. Deduplication
    3. LLM normalize description to 50 words
    4. Generate embedding
    5. Store in DB
    Returns True if saved, False if skipped.
    """
    # Quality filter: min 50 words description
    word_count = len(description.split())
    if word_count < settings.ingestion_min_description_words:
        return False

    # Quality filter: deadline must be in the future (if provided)
    now = datetime.now(timezone.utc)
    if deadline and deadline < now:
        return False

    # Quality filter: URL must look valid
    if not url.startswith("http"):
        return False

    # Deduplication
    content_hash = compute_content_hash(title, organization, deadline)
    if opportunity_exists(db, content_hash):
        # Update last_seen_at for existing opportunity
        existing = db.query(Opportunity).filter(Opportunity.content_hash == content_hash).first()
        if existing:
            existing.last_seen_at = now
            db.commit()
        return False

    # Normalize description
    try:
        short_desc = await normalize_opportunity_description(description)
    except Exception:
        short_desc = " ".join(description.split()[:50])

    # Generate embedding
    opp_data = {
        "title": title,
        "organization": organization,
        "type": opp_type.value,
        "description": description,
        "eligibility": eligibility_data or {},
    }
    try:
        embedding = await generate_embedding(build_opportunity_embedding_text(opp_data))
    except Exception:
        embedding = None

    # Store opportunity
    opp = Opportunity(
        title=title,
        type=opp_type,
        organization=organization,
        description=description,
        description_short=short_desc,
        deadline=deadline,
        funding_type=funding_type,
        funding_amount=funding_amount,
        location=location,
        remote_eligible=remote_eligible,
        url=url,
        source_name=source_name,
        content_hash=content_hash,
        embedding=embedding,
        embedding_updated_at=now if embedding else None,
        is_active=True,
        last_seen_at=now,
    )
    db.add(opp)
    db.flush()

    # Store eligibility
    if eligibility_data:
        elig = Eligibility(
            opportunity_id=opp.id,
            nationality=eligibility_data.get("nationality", []),
            gpa_min=eligibility_data.get("gpa_min"),
            enrollment_status=eligibility_data.get("enrollment_status", []),
            field_of_study=eligibility_data.get("field_of_study", []),
            age_min=eligibility_data.get("age_min"),
            age_max=eligibility_data.get("age_max"),
            raw_requirements=eligibility_data.get("raw_requirements"),
        )
        db.add(elig)

    db.commit()

    # Trigger matching for this new opportunity
    from app.worker.agent_tasks import run_matching_for_opportunity_task
    if hasattr(run_matching_for_opportunity_task, "delay"):
        run_matching_for_opportunity_task.delay(str(opp.id))

    return True


# ─────────────────────────────────────────────────────────────
# SOURCE-SPECIFIC SCRAPERS
# ─────────────────────────────────────────────────────────────

async def scrape_devpost() -> list[dict]:
    """Scrape Devpost hackathons via their public API."""
    opportunities = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
            resp = await client.get("https://devpost.com/api/hackathons?status=open&order_by=deadline")
            if resp.status_code != 200:
                return []
            data = resp.json()
            for h in data.get("hackathons", []):
                deadline = None
                if h.get("submission_period_dates"):
                    # Parse deadline from date range string (format varies)
                    pass
                opportunities.append({
                    "title": h.get("title", ""),
                    "organization": h.get("organization_name", "Devpost"),
                    "description": h.get("displayed_challenge_summary", h.get("tagline", "")),
                    "url": h.get("url", ""),
                    "location": h.get("location", ""),
                    "remote_eligible": h.get("online_only", False),
                    "deadline": deadline,
                    "source": "devpost",
                })
    except Exception as e:
        logger.error("scraper.devpost.failed", error=str(e))
    return opportunities


async def scrape_mlh_rss() -> list[dict]:
    """Parse MLH hackathon RSS feed."""
    opportunities = []
    try:
        feed = feedparser.parse("https://mlh.io/seasons/2025/events.rss")
        for entry in feed.entries[:20]:
            opportunities.append({
                "title": entry.get("title", ""),
                "organization": "MLH",
                "description": entry.get("summary", entry.get("title", "")),
                "url": entry.get("link", ""),
                "location": "",
                "remote_eligible": True,
                "deadline": None,
                "source": "mlh",
            })
    except Exception as e:
        logger.error("scraper.mlh.failed", error=str(e))
    return opportunities


async def scrape_opportunity_desk() -> list[dict]:
    """Scrape Opportunity Desk scholarships/fellowships."""
    opportunities = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
            resp = await client.get("https://opportunitydesk.org/feed/")
            if resp.status_code != 200:
                return []
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:30]:
                opportunities.append({
                    "title": entry.get("title", ""),
                    "organization": "Opportunity Desk",
                    "description": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "location": "",
                    "remote_eligible": False,
                    "deadline": None,
                    "source": "opportunity_desk",
                })
    except Exception as e:
        logger.error("scraper.opportunity_desk.failed", error=str(e))
    return opportunities


# ─────────────────────────────────────────────────────────────
# CELERY INGESTION TASKS
# ─────────────────────────────────────────────────────────────

@celery_app.task(name="app.worker.ingestion_tasks.ingest_all_hackathons")
def ingest_all_hackathons():
    """Ingest from Devpost + MLH. Runs every 4 hours."""
    db = SessionLocal()
    saved = 0
    try:
        sources = [scrape_devpost(), scrape_mlh_rss()]
        all_opps = []
        for coro in sources:
            all_opps.extend(asyncio.run(coro))

        for raw in all_opps:
            if not raw.get("title") or not raw.get("url"):
                continue
            desc = raw.get("description", "")
            if len(desc.split()) < 10:
                desc = f"{raw['title']} — an exciting hackathon opportunity open to students worldwide."

            result = asyncio.run(ingest_opportunity(
                db=db,
                title=raw["title"],
                organization=raw.get("organization", ""),
                description=desc,
                opp_type=OpportunityType.HACKATHON,
                url=raw["url"],
                source_name=raw.get("source", "hackathon"),
                deadline=raw.get("deadline"),
                remote_eligible=raw.get("remote_eligible", True),
                location=raw.get("location"),
            ))
            if result:
                saved += 1

        logger.info("ingest.hackathons.complete", saved=saved, total=len(all_opps))
    finally:
        db.close()
    return {"saved": saved}


@celery_app.task(name="app.worker.ingestion_tasks.ingest_all_scholarships")
def ingest_all_scholarships():
    """Ingest scholarships from Opportunity Desk + other sources. Runs daily."""
    db = SessionLocal()
    saved = 0
    try:
        raw_list = asyncio.run(scrape_opportunity_desk())
        for raw in raw_list:
            if not raw.get("title") or not raw.get("url"):
                continue
            desc = raw.get("description", "")
            if not desc or len(desc.split()) < 10:
                desc = f"{raw['title']} — a scholarship or fellowship opportunity for students."

            result = asyncio.run(ingest_opportunity(
                db=db,
                title=raw["title"],
                organization=raw.get("organization", ""),
                description=desc,
                opp_type=OpportunityType.SCHOLARSHIP,
                url=raw["url"],
                source_name=raw.get("source", "scholarship"),
                deadline=raw.get("deadline"),
                funding_type=FundingType.FULLY_FUNDED,
            ))
            if result:
                saved += 1

        logger.info("ingest.scholarships.complete", saved=saved)
    finally:
        db.close()
    return {"saved": saved}


@celery_app.task(name="app.worker.ingestion_tasks.ingest_all_fellowships")
def ingest_all_fellowships():
    logger.info("ingest.fellowships.started")
    # Add fellowship scrapers (YALI, Atlas Corps, Fulbright) here
    return {"saved": 0}


@celery_app.task(name="app.worker.ingestion_tasks.ingest_all_internships")
def ingest_all_internships():
    logger.info("ingest.internships.started")
    # Add internship scrapers (GSoC, Internshala) here
    return {"saved": 0}


@celery_app.task(name="app.worker.ingestion_tasks.ingest_all_exchanges")
def ingest_all_exchanges():
    logger.info("ingest.exchanges.started")
    # Add exchange scrapers (Erasmus+, AIESEC) here
    return {"saved": 0}


# ─────────────────────────────────────────────────────────────
# MATCHING TRIGGER (new opportunity → match all students)
# ─────────────────────────────────────────────────────────────

@celery_app.task(name="app.worker.agent_tasks.run_matching_for_opportunity_task")
def run_matching_for_opportunity_task(opportunity_id: str):
    from uuid import UUID
    from app.services.matching_engine import run_matching_for_opportunity
    db = SessionLocal()
    try:
        count = run_matching_for_opportunity(db, UUID(opportunity_id))
        logger.info("matching.opportunity.complete", opportunity_id=opportunity_id, matched=count)
    finally:
        db.close()
