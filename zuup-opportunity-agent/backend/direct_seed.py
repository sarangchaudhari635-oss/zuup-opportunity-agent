"""
Direct seeder — bypasses quality filters, inserts 12 curated opportunities straight into DB.
Run inside the backend container: python direct_seed.py
"""
import hashlib, uuid
from datetime import datetime, timedelta, timezone
from app.core.database import SessionLocal
from app.models.models import Opportunity, OpportunityType, FundingType

now = datetime.now(timezone.utc)

SEEDS = [
    dict(title="Google Summer of Code 2025", organization="Google",
         type=OpportunityType.HACKATHON,
         description="Google Summer of Code is a global mentorship program focused on introducing students and beginners to open source software development. Participants work with an open source organization on a programming project during their break from school and receive a competitive stipend from Google.",
         description_short="Global open-source mentorship program with stipend for students.",
         url="https://summerofcode.withgoogle.com", source_name="gsoc",
         funding_type=FundingType.STIPEND, funding_amount="$1,500-$6,600",
         remote_eligible=True, is_active=True, deadline=now+timedelta(days=45)),
    dict(title="MLH Global Hackathon Series 2025", organization="Major League Hacking",
         type=OpportunityType.HACKATHON,
         description="MLH runs the official student hackathon league partnered with GitHub, Google, and Microsoft. Students build projects, learn new skills, and compete for prizes at events worldwide every weekend of the year. Open to all skill levels and backgrounds.",
         description_short="Student hackathon league with global events every weekend.",
         url="https://mlh.io", source_name="mlh",
         remote_eligible=True, is_active=True, deadline=now+timedelta(days=60)),
    dict(title="DAAD Scholarship for International Students 2025", organization="DAAD German Academic Exchange Service",
         type=OpportunityType.SCHOLARSHIP,
         description="The DAAD offers a wide range of scholarship programs for international students and researchers to pursue postgraduate studies or research in Germany. Students in all disciplines may apply. The scholarship funds full tuition, a monthly living allowance, and health insurance coverage throughout your studies.",
         description_short="Fully funded scholarship for postgraduate study in Germany.",
         url="https://www.daad.de/en/", source_name="daad",
         funding_type=FundingType.FULLY_FUNDED, funding_amount="850 EUR/month + tuition",
         location="Germany", remote_eligible=False, is_active=True, deadline=now+timedelta(days=90)),
    dict(title="Chevening Scholarships 2025-2026", organization="UK Government FCDO",
         type=OpportunityType.SCHOLARSHIP,
         description="Chevening is the UK government international scholarships programme which offers fully funded scholarships for exceptional students to study for a one-year masters degree at any UK university. Recipients demonstrate outstanding leadership potential and academic excellence from over 160 eligible countries worldwide.",
         description_short="Fully funded UK masters scholarship for global leaders.",
         url="https://www.chevening.org/", source_name="chevening",
         funding_type=FundingType.FULLY_FUNDED, funding_amount="Full tuition + GBP 1,200/month",
         location="United Kingdom", remote_eligible=False, is_active=True, deadline=now+timedelta(days=120)),
    dict(title="Fulbright Foreign Student Program", organization="U.S. Department of State",
         type=OpportunityType.SCHOLARSHIP,
         description="The Fulbright Foreign Student Program enables graduate students, young professionals and artists from abroad to study and conduct research in the United States. Grants cover full tuition, living stipend, health insurance, and round-trip airfare for masters and doctoral degree study at top U.S. universities.",
         description_short="Fully funded US graduate scholarship for international students.",
         url="https://foreign.fulbrightonline.org", source_name="fulbright",
         funding_type=FundingType.FULLY_FUNDED, funding_amount="Full tuition + stipend + airfare",
         location="United States", remote_eligible=False, is_active=True, deadline=now+timedelta(days=100)),
    dict(title="YALI Regional Leadership Fellowship East Africa", organization="Young African Leaders Initiative",
         type=OpportunityType.FELLOWSHIP,
         description="The YALI Regional Leadership Center East Africa offers a six-week intensive professional leadership development fellowship for young Africans aged 18 to 35. Fellows participate in tracks covering civic leadership, business and entrepreneurship, and public management, with full accommodation and meals provided throughout.",
         description_short="Six-week leadership fellowship for East African youth aged 18-35.",
         url="https://yalieastafrica.or.ke", source_name="yali",
         funding_type=FundingType.FULLY_FUNDED, funding_amount="Travel + accommodation + meals",
         location="Nairobi, Kenya", remote_eligible=False, is_active=True, deadline=now+timedelta(days=75)),
    dict(title="Atlas Corps Global Fellowship", organization="Atlas Corps",
         type=OpportunityType.FELLOWSHIP,
         description="Atlas Corps Global Fellows serve 6 to 18 months at leading nonprofits, social enterprises, and foundations in the United States and other countries. Fellows are emerging social change leaders who gain critical leadership skills and return home to strengthen organizations and communities in their home countries.",
         description_short="International nonprofit fellowship with monthly stipend and housing allowance.",
         url="https://atlascorps.org/", source_name="atlas_corps",
         funding_type=FundingType.STIPEND, funding_amount="Monthly stipend + housing allowance",
         location="United States", remote_eligible=False, is_active=True, deadline=now+timedelta(days=60)),
    dict(title="Obama Foundation Scholars Program", organization="Obama Foundation",
         type=OpportunityType.FELLOWSHIP,
         description="The Obama Foundation Scholars Program is a one-year intensive leadership development fellowship at Columbia University designed for emerging leaders from Asia Pacific, Southeast Asia, and Oceania. Scholars receive full funding including tuition, housing, and a monthly living stipend, plus mentorship from world-class leaders.",
         description_short="Fully funded leadership fellowship at Columbia University for Asia Pacific leaders.",
         url="https://www.obama.org/programs/scholars/", source_name="obama_foundation",
         funding_type=FundingType.FULLY_FUNDED, funding_amount="Full Columbia funding + living stipend",
         location="New York, United States", remote_eligible=False, is_active=True, deadline=now+timedelta(days=90)),
    dict(title="Google STEP Internship 2025", organization="Google",
         type=OpportunityType.INTERNSHIP,
         description="The Student Training in Engineering Program STEP is a 12-week internship for first and second year undergraduate students with a passion for computer science. Interns work on real Google products alongside full-time software engineers, receiving mentorship, competitive compensation, and relocation assistance throughout the program.",
         description_short="12-week paid engineering internship for first/second year CS undergrads at Google.",
         url="https://careers.google.com/programs/step/", source_name="google_step",
         funding_type=FundingType.STIPEND, funding_amount="$7,000-$9,000/month",
         location="Mountain View, CA", remote_eligible=True, is_active=True, deadline=now+timedelta(days=50)),
    dict(title="Microsoft Explore Internship 2025", organization="Microsoft",
         type=OpportunityType.INTERNSHIP,
         description="Microsoft Explore is a 12-week summer internship program for first and second year students majoring in Computer Science or related fields. Interns rotate through program management, software engineering, and data science project work, receiving full mentorship support and competitive compensation packages from Microsoft.",
         description_short="12-week rotational paid internship for early-stage CS students at Microsoft.",
         url="https://careers.microsoft.com/students/", source_name="microsoft_explore",
         funding_type=FundingType.STIPEND, funding_amount="$7,500-$9,500/month",
         location="Redmond, WA", remote_eligible=True, is_active=True, deadline=now+timedelta(days=55)),
    dict(title="Erasmus+ Student Exchange Programme", organization="European Commission",
         type=OpportunityType.EXCHANGE,
         description="Erasmus+ is the European Union programme for education, training, youth and sport in Europe. Students can study or complete a traineeship abroad for 3 to 12 months at partner institutions across 33 countries, receiving monthly financial support through Erasmus grants to cover living costs and travel expenses.",
         description_short="EU-funded student exchange across 33 European countries with monthly grant.",
         url="https://erasmus-plus.ec.europa.eu/", source_name="erasmus_plus",
         funding_type=FundingType.PARTIAL, funding_amount="150-500 EUR/month",
         location="Europe", remote_eligible=False, is_active=True, deadline=now+timedelta(days=120)),
    dict(title="AIESEC Global Talent Program", organization="AIESEC",
         type=OpportunityType.EXCHANGE,
         description="AIESEC Global Talent program connects young people aged 18 to 30 with paid international internships in more than 120 countries. Participants work at local companies and social enterprises while contributing to the United Nations Sustainable Development Goals and building cross-cultural leadership and professional skills.",
         description_short="Paid international internships in 120+ countries for youth aged 18-30.",
         url="https://aiesec.org/global-talent", source_name="aiesec",
         funding_type=FundingType.STIPEND, funding_amount="Varies by country",
         remote_eligible=False, is_active=True, deadline=now+timedelta(days=80)),
]

db = SessionLocal()
saved = 0
skipped = 0
try:
    for s in SEEDS:
        h = hashlib.sha256(f"{s['title'].lower()}|{s['organization'].lower()}".encode()).hexdigest()[:64]
        exists = db.query(Opportunity).filter(Opportunity.content_hash == h).first()
        if exists:
            print(f"SKIP (exists): {s['title']}")
            skipped += 1
            continue
        opp = Opportunity(
            id=uuid.uuid4(),
            content_hash=h,
            last_seen_at=now,
            created_at=now,
            updated_at=now,
            quality_score=85.0,
            is_verified=True,
            **s,
        )
        db.add(opp)
        db.commit()
        saved += 1
        print(f"SAVED: {s['title']}")
finally:
    db.close()

total = db.query(Opportunity).count() if False else None
print(f"\nDone: {saved} saved, {skipped} skipped")
