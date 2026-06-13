# E2E Test Report — Zuup Opportunity Agent
Generated on: 2026-06-13 11:43:42
Test User: `e2e_tester_6b68a880@zuup.dev`

## Summary
| Test Case | Status | Details |
|---|---|---|
| **Health Check** | ✅ PASS | API is online and healthy. (`200`) |
| **Register User** | ✅ PASS | Successfully registered new test user. (`201`) |
| **Register Duplicate User** | ✅ PASS | Successfully blocked duplicate email registration. (`409`) |
| **Login (Valid)** | ✅ PASS | Successfully logged in and received access token. (`200`) |
| **Login (Invalid Password)** | ✅ PASS | Incorrect password correctly rejected. (`401`) |
| **Unauthenticated Access Blocked** | ✅ PASS | Unauthenticated profile access correctly blocked with status 403. (`403`) |
| **Get Initial Profile** | ✅ PASS | Retrieved profile. Completeness score: 0%. (`200`) |
| **Update Profile Details** | ✅ PASS | Profile updated. Completeness score increased to: 65%. (`200`) |
| **Get Opportunities Feed** | ✅ PASS | Found 12 opportunities (total: 12). First ID: 5726f845-cbb6-4383-8c4b-20a248012a9d (`200`) |
| **Filter Opportunities (Scholarship)** | ✅ PASS | Returned 3 items. All are scholarships. (`200`) |
| **Save Opportunity** | ✅ PASS | Created tracker application. ID: 33811823-dbc5-4278-ab0e-65e8a3256fc7, Status: saved (`201`) |
| **Get Applications List** | ✅ PASS | Found active tracker count: 1. (`200`) |
| **Move Application Status** | ✅ PASS | Updated application status to: applied. (`200`) |
| **Get Notifications** | ✅ PASS | Successfully queried notifications list. Found 0 entries. (`200`) |
| **Export CSV** | ✅ PASS | Successfully exported tracker CSV. Size: 206 bytes. (`200`) |
| **Frontend Routes** | ✅ PASS | All routes loaded or redirected correctly: /dashboard (200), /profile (200), /tracker (200), /login (200), /register (200), /opportunities (307), /applications (307), /onboarding/upload (200), /onboarding/review (200) |

## Detailed API Response Payload Outputs
### Health Check
```json
{
  "status": "ok",
  "version": "1.0.0",
  "env": "development"
}
```

### Register User
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MGY0YzY4Ni0xZTg5LTQ3ZDctODBjZC1kYmRlODM1MjQxNDMiLCJleHAiOjE3ODEzMzIxMTgsInR5cGUiOiJhY2Nlc3MifQ.KPM07UubvRpQvT5CVJ0ltLUF_4jGUBT1-d-EN6nxgiA",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MGY0YzY4Ni0xZTg5LTQ3ZDctODBjZC1kYmRlODM1MjQxNDMiLCJleHAiOjE3ODE5MzYwMTgsInR5cGUiOiJyZWZyZXNoIn0.5Aro7BqjQbTo8r1yzgXi_Hk8DEPmjrzHEHyMkAnxzGk",
  "token_type": "bearer"
}
```

### Register Duplicate User
```json
{
  "detail": "An account with this email already exists."
}
```

### Login (Valid)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MGY0YzY4Ni0xZTg5LTQ3ZDctODBjZC1kYmRlODM1MjQxNDMiLCJleHAiOjE3ODEzMzIxMTgsInR5cGUiOiJhY2Nlc3MifQ.KPM07UubvRpQvT5CVJ0ltLUF_4jGUBT1-d-EN6nxgiA",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MGY0YzY4Ni0xZTg5LTQ3ZDctODBjZC1kYmRlODM1MjQxNDMiLCJleHAiOjE3ODE5MzYwMTgsInR5cGUiOiJyZWZyZXNoIn0.5Aro7BqjQbTo8r1yzgXi_Hk8DEPmjrzHEHyMkAnxzGk",
  "token_type": "bearer"
}
```

### Login (Invalid Password)
```json
{
  "detail": "Invalid email or password."
}
```

### Unauthenticated Access Blocked
```json
{
  "detail": "Not authenticated"
}
```

### Get Initial Profile
```json
{
  "id": "e1a56d22-2c87-490c-8348-210af7904c3f",
  "user_id": "80f4c686-1e89-47d7-80cd-dbde83524143",
  "name": null,
  "location": null,
  "nationality": null,
  "citizenship": [],
  "enrollment_status": null,
  "field_of_study": null,
  "skills": [],
  "languages": [],
  "interests": [],
  "career_goals": null,
  "career_goal_tags": [],
  "gpa": null,
  "completeness_score": 0,
  "resume_parsed_at": null,
  "education": [],
  "experience": [],
  "updated_at": "2026-06-13T06:13:38.347148Z"
}
```

### Update Profile Details
```json
{
  "id": "e1a56d22-2c87-490c-8348-210af7904c3f",
  "user_id": "80f4c686-1e89-47d7-80cd-dbde83524143",
  "name": "E2E Tester 6b68a880",
  "location": "San Francisco, CA",
  "nationality": null,
  "citizenship": [],
  "enrollment_status": "enrolled",
  "field_of_study": "Computer Science",
  "skills": [
    "Python",
    "FastAPI",
    "React",
    "Docker"
  ],
  "languages": [
    "English",
    "Spanish"
  ],
  "interests": [
    "Machine Learning",
    "Software Engineering"
  ],
  "career_goals": "I want to build highly-scalable AI models and developer platforms.",
  "career_goal_tags": [],
  "gpa": null,
  "completeness_score": 65,
  "resume_parsed_at": null,
  "education": [],
  "experience": [],
  "updated_at": "2026-06-13T06:13:38.864171Z"
}
```

### Get Opportunities Feed
```json
{
  "items": [
    {
      "id": "5726f845-cbb6-4383-8c4b-20a248012a9d",
      "title": "Google Summer of Code 2025",
      "type": "hackathon",
      "organization": "Google",
      "description_short": "Global open-source mentorship program with stipend for students.",
      "deadline": "2026-07-28T05:38:26.399624Z",
      "funding_type": "stipend",
      "location": null,
      "remote_eligible": true,
      "url": "https://summerofcode.withgoogle.com",
      "source_name": "gsoc",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "9469875a-b907-4a02-8c55-e30fcf6752b6",
      "title": "Google STEP Internship 2025",
      "type": "internship",
      "organization": "Google",
      "description_short": "12-week paid engineering internship for first/second year CS undergrads at Google.",
      "deadline": "2026-08-02T05:38:26.399624Z",
      "funding_type": "stipend",
      "location": "Mountain View, CA",
      "remote_eligible": true,
      "url": "https://careers.google.com/programs/step/",
      "source_name": "google_step",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "182fbbaf-df5a-49fb-bbe8-09f8d430ad7e",
      "title": "Microsoft Explore Internship 2025",
      "type": "internship",
      "organization": "Microsoft",
      "description_short": "12-week rotational paid internship for early-stage CS students at Microsoft.",
      "deadline": "2026-08-07T05:38:26.399624Z",
      "funding_type": "stipend",
      "location": "Redmond, WA",
      "remote_eligible": true,
      "url": "https://careers.microsoft.com/students/",
      "source_name": "microsoft_explore",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "a7b0195d-246f-4da7-9d94-d2999dcf5d50",
      "title": "Atlas Corps Global Fellowship",
      "type": "fellowship",
      "organization": "Atlas Corps",
      "description_short": "International nonprofit fellowship with monthly stipend and housing allowance.",
      "deadline": "2026-08-12T05:38:26.399624Z",
      "funding_type": "stipend",
      "location": "United States",
      "remote_eligible": false,
      "url": "https://atlascorps.org/",
      "source_name": "atlas_corps",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "26b80f47-a8f4-452f-aee3-05650e5b00f8",
      "title": "MLH Global Hackathon Series 2025",
      "type": "hackathon",
      "organization": "Major League Hacking",
      "description_short": "Student hackathon league with global events every weekend.",
      "deadline": "2026-08-12T05:38:26.399624Z",
      "funding_type": null,
      "location": null,
      "remote_eligible": true,
      "url": "https://mlh.io",
      "source_name": "mlh",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "04b3212c-3bba-437b-b630-48ec531c4244",
      "title": "YALI Regional Leadership Fellowship East Africa",
      "type": "fellowship",
      "organization": "Young African Leaders Initiative",
      "description_short": "Six-week leadership fellowship for East African youth aged 18-35.",
      "deadline": "2026-08-27T05:38:26.399624Z",
      "funding_type": "fully_funded",
      "location": "Nairobi, Kenya",
      "remote_eligible": false,
      "url": "https://yalieastafrica.or.ke",
      "source_name": "yali",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "883139b9-2337-4fbd-a760-409fa6f3d7c9",
      "title": "AIESEC Global Talent Program",
      "type": "exchange",
      "organization": "AIESEC",
      "description_short": "Paid international internships in 120+ countries for youth aged 18-30.",
      "deadline": "2026-09-01T05:38:26.399624Z",
      "funding_type": "stipend",
      "location": null,
      "remote_eligible": false,
      "url": "https://aiesec.org/global-talent",
      "source_name": "aiesec",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "a51616e7-0177-4d30-a960-4ddc7a7c3ff9",
      "title": "Obama Foundation Scholars Program",
      "type": "fellowship",
      "organization": "Obama Foundation",
      "description_short": "Fully funded leadership fellowship at Columbia University for Asia Pacific leaders.",
      "deadline": "2026-09-11T05:38:26.399624Z",
      "funding_type": "fully_funded",
      "location": "New York, United States",
      "remote_eligible": false,
      "url": "https://www.obama.org/programs/scholars/",
      "source_name": "obama_foundation",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "0c3bb1ee-124b-4c4b-b58a-e1dd8f2b0b10",
      "title": "DAAD Scholarship for International Students 2025",
      "type": "scholarship",
      "organization": "DAAD German Academic Exchange Service",
      "description_short": "Fully funded scholarship for postgraduate study in Germany.",
      "deadline": "2026-09-11T05:38:26.399624Z",
      "funding_type": "fully_funded",
      "location": "Germany",
      "remote_eligible": false,
      "url": "https://www.daad.de/en/",
      "source_name": "daad",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "b8eb492e-204a-480b-9f91-de12270655e3",
      "title": "Fulbright Foreign Student Program",
      "type": "scholarship",
      "organization": "U.S. Department of State",
      "description_short": "Fully funded US graduate scholarship for international students.",
      "deadline": "2026-09-21T05:38:26.399624Z",
      "funding_type": "fully_funded",
      "location": "United States",
      "remote_eligible": false,
      "url": "https://foreign.fulbrightonline.org",
      "source_name": "fulbright",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "e5c66243-b1ca-47a9-98bc-a616c3a1b8ca",
      "title": "Chevening Scholarships 2025-2026",
      "type": "scholarship",
      "organization": "UK Government FCDO",
      "description_short": "Fully funded UK masters scholarship for global leaders.",
      "deadline": "2026-10-11T05:38:26.399624Z",
      "funding_type": "fully_funded",
      "location": "United Kingdom",
      "remote_eligible": false,
      "url": "https://www.chevening.org/",
      "source_name": "chevening",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "03d8ddb9-f41c-4633-9f88-92c9030ee9a3",
      "title": "Erasmus+ Student Exchange Programme",
      "type": "exchange",
      "organization": "European Commission",
      "description_short": "EU-funded student exchange across 33 European countries with monthly grant.",
      "deadline": "2026-10-11T05:38:26.399624Z",
      "funding_type": "partial",
      "location": "Europe",
      "remote_eligible": false,
      "url": "https://erasmus-plus.ec.europa.eu/",
      "source_name": "erasmus_plus",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 12,
  "has_next": false
}
```

### Filter Opportunities (Scholarship)
```json
{
  "items": [
    {
      "id": "0c3bb1ee-124b-4c4b-b58a-e1dd8f2b0b10",
      "title": "DAAD Scholarship for International Students 2025",
      "type": "scholarship",
      "organization": "DAAD German Academic Exchange Service",
      "description_short": "Fully funded scholarship for postgraduate study in Germany.",
      "deadline": "2026-09-11T05:38:26.399624Z",
      "funding_type": "fully_funded",
      "location": "Germany",
      "remote_eligible": false,
      "url": "https://www.daad.de/en/",
      "source_name": "daad",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "b8eb492e-204a-480b-9f91-de12270655e3",
      "title": "Fulbright Foreign Student Program",
      "type": "scholarship",
      "organization": "U.S. Department of State",
      "description_short": "Fully funded US graduate scholarship for international students.",
      "deadline": "2026-09-21T05:38:26.399624Z",
      "funding_type": "fully_funded",
      "location": "United States",
      "remote_eligible": false,
      "url": "https://foreign.fulbrightonline.org",
      "source_name": "fulbright",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    {
      "id": "e5c66243-b1ca-47a9-98bc-a616c3a1b8ca",
      "title": "Chevening Scholarships 2025-2026",
      "type": "scholarship",
      "organization": "UK Government FCDO",
      "description_short": "Fully funded UK masters scholarship for global leaders.",
      "deadline": "2026-10-11T05:38:26.399624Z",
      "funding_type": "fully_funded",
      "location": "United Kingdom",
      "remote_eligible": false,
      "url": "https://www.chevening.org/",
      "source_name": "chevening",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 12,
  "has_next": false
}
```

### Save Opportunity
```json
{
  "id": "33811823-dbc5-4278-ab0e-65e8a3256fc7",
  "user_id": "80f4c686-1e89-47d7-80cd-dbde83524143",
  "opportunity_id": "5726f845-cbb6-4383-8c4b-20a248012a9d",
  "opportunity": {
    "id": "5726f845-cbb6-4383-8c4b-20a248012a9d",
    "title": "Google Summer of Code 2025",
    "type": "hackathon",
    "organization": "Google",
    "description_short": "Global open-source mentorship program with stipend for students.",
    "deadline": "2026-07-28T05:38:26.399624Z",
    "funding_type": "stipend",
    "location": null,
    "remote_eligible": true,
    "url": "https://summerofcode.withgoogle.com",
    "source_name": "gsoc",
    "match_score": null,
    "created_at": "2026-06-13T05:38:26.399624Z"
  },
  "status": "saved",
  "notes": "E2E testing notes",
  "requirements_checklist": [],
  "applied_at": null,
  "outcome_at": null,
  "outcome_result": null,
  "created_at": "2026-06-13T06:13:38.946099Z",
  "updated_at": "2026-06-13T06:13:38.946101Z"
}
```

### Get Applications List
```json
[
  {
    "id": "33811823-dbc5-4278-ab0e-65e8a3256fc7",
    "user_id": "80f4c686-1e89-47d7-80cd-dbde83524143",
    "opportunity_id": "5726f845-cbb6-4383-8c4b-20a248012a9d",
    "opportunity": {
      "id": "5726f845-cbb6-4383-8c4b-20a248012a9d",
      "title": "Google Summer of Code 2025",
      "type": "hackathon",
      "organization": "Google",
      "description_short": "Global open-source mentorship program with stipend for students.",
      "deadline": "2026-07-28T05:38:26.399624Z",
      "funding_type": "stipend",
      "location": null,
      "remote_eligible": true,
      "url": "https://summerofcode.withgoogle.com",
      "source_name": "gsoc",
      "match_score": null,
      "created_at": "2026-06-13T05:38:26.399624Z"
    },
    "status": "saved",
    "notes": "E2E testing notes",
    "requirements_checklist": [],
    "applied_at": null,
    "outcome_at": null,
    "outcome_result": null,
    "created_at": "2026-06-13T06:13:38.946099Z",
    "updated_at": "2026-06-13T06:13:38.946101Z"
  }
]
```

### Move Application Status
```json
{
  "id": "33811823-dbc5-4278-ab0e-65e8a3256fc7",
  "user_id": "80f4c686-1e89-47d7-80cd-dbde83524143",
  "opportunity_id": "5726f845-cbb6-4383-8c4b-20a248012a9d",
  "opportunity": {
    "id": "5726f845-cbb6-4383-8c4b-20a248012a9d",
    "title": "Google Summer of Code 2025",
    "type": "hackathon",
    "organization": "Google",
    "description_short": "Global open-source mentorship program with stipend for students.",
    "deadline": "2026-07-28T05:38:26.399624Z",
    "funding_type": "stipend",
    "location": null,
    "remote_eligible": true,
    "url": "https://summerofcode.withgoogle.com",
    "source_name": "gsoc",
    "match_score": null,
    "created_at": "2026-06-13T05:38:26.399624Z"
  },
  "status": "applied",
  "notes": "Applied today via online portal.",
  "requirements_checklist": [],
  "applied_at": "2026-06-13T06:13:38.995690Z",
  "outcome_at": null,
  "outcome_result": null,
  "created_at": "2026-06-13T06:13:38.946099Z",
  "updated_at": "2026-06-13T06:13:38.995988Z"
}
```

