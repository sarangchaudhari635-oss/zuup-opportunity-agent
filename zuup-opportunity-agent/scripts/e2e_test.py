import requests
import uuid
import time
import os
from datetime import datetime

base_api = "http://127.0.0.1:8000"
base_fe = "http://127.0.0.1:3000"

# Generate a clean, unique user for this E2E run
test_id = uuid.uuid4().hex[:8]
email = f"e2e_tester_{test_id}@zuup.dev"
password = "E2EPassword@2026"
full_name = f"E2E Tester {test_id}"

results = []

def record_test(name, passed, detail="", status_code=None, response=None):
    results.append({
        "name": name,
        "passed": passed,
        "detail": detail,
        "status_code": status_code,
        "response": response
    })
    status_str = "PASS" if passed else "FAIL"
    code_str = f" [Status: {status_code}]" if status_code else ""
    print(f"[{status_str}] {name}{code_str} - {detail}")

print("=== STARTING E2E WEBSITE TEST ===")
print(f"Target API: {base_api}")
print(f"Target Frontend: {base_fe}")
print(f"Test Email: {email}\n")

# 1. Health Check
try:
    r = requests.get(f"{base_api}/health", timeout=5)
    if r.status_code == 200 and r.json().get("status") == "ok":
        record_test("Health Check", True, "API is online and healthy.", 200, r.json())
    else:
        record_test("Health Check", False, f"Unexpected response: {r.text}", r.status_code)
except Exception as e:
    record_test("Health Check", False, f"Connection failed: {str(e)}")

# 2. Registration
try:
    payload = {"email": email, "password": password, "full_name": full_name}
    r = requests.post(f"{base_api}/auth/register", json=payload, timeout=5)
    if r.status_code == 201:
        tokens = r.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        record_test("Register User", True, "Successfully registered new test user.", 201, tokens)
    else:
        record_test("Register User", False, f"Failed to register: {r.text}", r.status_code)
        access_token = None
        refresh_token = None
except Exception as e:
    record_test("Register User", False, f"Registration failed: {str(e)}")
    access_token = None
    refresh_token = None

# 3. Duplicate Registration (Conflict)
try:
    payload = {"email": email, "password": password, "full_name": full_name}
    r = requests.post(f"{base_api}/auth/register", json=payload, timeout=5)
    if r.status_code == 409:
        record_test("Register Duplicate User", True, "Successfully blocked duplicate email registration.", 409, r.json())
    else:
        record_test("Register Duplicate User", False, f"Expected 409 Conflict, got: {r.status_code}", r.status_code)
except Exception as e:
    record_test("Register Duplicate User", False, f"Request failed: {str(e)}")

# 4. Correct Login
try:
    payload = {"email": email, "password": password}
    r = requests.post(f"{base_api}/auth/login", json=payload, timeout=5)
    if r.status_code == 200:
        login_tokens = r.json()
        access_token = login_tokens.get("access_token")
        record_test("Login (Valid)", True, "Successfully logged in and received access token.", 200, login_tokens)
    else:
        record_test("Login (Valid)", False, f"Login failed: {r.text}", r.status_code)
except Exception as e:
    record_test("Login (Valid)", False, f"Login request failed: {str(e)}")

# 5. Bad Login
try:
    payload = {"email": email, "password": "WrongPassword123"}
    r = requests.post(f"{base_api}/auth/login", json=payload, timeout=5)
    if r.status_code == 401:
        record_test("Login (Invalid Password)", True, "Incorrect password correctly rejected.", 401, r.json())
    else:
        record_test("Login (Invalid Password)", False, f"Expected 401 Unauthorized, got: {r.status_code}", r.status_code)
except Exception as e:
    record_test("Login (Invalid Password)", False, f"Request failed: {str(e)}")

# 6. Unauthenticated Profile Access
try:
    r = requests.get(f"{base_api}/profile/me", timeout=5)
    if r.status_code in (401, 403):
        record_test("Unauthenticated Access Blocked", True, f"Unauthenticated profile access correctly blocked with status {r.status_code}.", r.status_code, r.json())
    else:
        record_test("Unauthenticated Access Blocked", False, f"Expected 401 or 403, got: {r.status_code}", r.status_code)
except Exception as e:
    record_test("Unauthenticated Access Blocked", False, f"Request failed: {str(e)}")

# Authorized tests
if access_token:
    headers = {"Authorization": f"Bearer {access_token}"}

    # 7. Get Profile (New User)
    try:
        r = requests.get(f"{base_api}/profile/me", headers=headers, timeout=5)
        if r.status_code == 200:
            profile = r.json()
            initial_score = profile.get("completeness_score", 0)
            record_test("Get Initial Profile", True, f"Retrieved profile. Completeness score: {initial_score}%.", 200, profile)
        else:
            record_test("Get Initial Profile", False, f"Failed to get profile: {r.text}", r.status_code)
    except Exception as e:
        record_test("Get Initial Profile", False, f"Request failed: {str(e)}")

    # 8. Update Profile
    try:
        payload = {
            "name": full_name,
            "location": "San Francisco, CA",
            "field_of_study": "Computer Science",
            "enrollment_status": "enrolled",
            "skills": ["Python", "FastAPI", "React", "Docker"],
            "interests": ["Machine Learning", "Software Engineering"],
            "languages": ["English", "Spanish"],
            "career_goals": "I want to build highly-scalable AI models and developer platforms."
        }
        r = requests.patch(f"{base_api}/profile/me", json=payload, headers=headers, timeout=5)
        if r.status_code == 200:
            updated_profile = r.json()
            updated_score = updated_profile.get("completeness_score", 0)
            record_test("Update Profile Details", True, f"Profile updated. Completeness score increased to: {updated_score}%.", 200, updated_profile)
        else:
            record_test("Update Profile Details", False, f"Update failed: {r.text}", r.status_code)
    except Exception as e:
        record_test("Update Profile Details", False, f"Request failed: {str(e)}")

    # 9. Get Opportunities Feed
    opp_id = None
    try:
        r = requests.get(f"{base_api}/opportunities?page=1&page_size=12", headers=headers, timeout=5)
        if r.status_code == 200:
            feed = r.json()
            items = feed.get("items", [])
            total = feed.get("total", 0)
            if items:
                opp_id = items[0].get("id")
                record_test("Get Opportunities Feed", True, f"Found {len(items)} opportunities (total: {total}). First ID: {opp_id}", 200, feed)
            else:
                record_test("Get Opportunities Feed", True, "Opportunities feed empty but returned 200 OK.", 200, feed)
        else:
            record_test("Get Opportunities Feed", False, f"Failed to get feed: {r.text}", r.status_code)
    except Exception as e:
        record_test("Get Opportunities Feed", False, f"Request failed: {str(e)}")

    # 10. Filter Opportunities by Type
    try:
        r = requests.get(f"{base_api}/opportunities?page=1&page_size=12&type=scholarship", headers=headers, timeout=5)
        if r.status_code == 200:
            feed = r.json()
            items = feed.get("items", [])
            non_scholarship = [o for o in items if o.get("type") != "scholarship"]
            if non_scholarship:
                record_test("Filter Opportunities (Scholarship)", False, f"Found non-scholarship opportunities in filtered list: {non_scholarship}", 200)
            else:
                record_test("Filter Opportunities (Scholarship)", True, f"Returned {len(items)} items. All are scholarships.", 200, feed)
        else:
            record_test("Filter Opportunities (Scholarship)", False, f"Filter request failed: {r.text}", r.status_code)
    except Exception as e:
        record_test("Filter Opportunities (Scholarship)", False, f"Request failed: {str(e)}")

    # 11. Save Opportunity (Create Application)
    app_id = None
    if opp_id:
        try:
            payload = {"opportunity_id": opp_id, "status": "saved", "notes": "E2E testing notes"}
            r = requests.post(f"{base_api}/applications", json=payload, headers=headers, timeout=5)
            if r.status_code == 201:
                app = r.json()
                app_id = app.get("id")
                record_test("Save Opportunity", True, f"Created tracker application. ID: {app_id}, Status: {app.get('status')}", 201, app)
            else:
                record_test("Save Opportunity", False, f"Failed to save: {r.text}", r.status_code)
        except Exception as e:
            record_test("Save Opportunity", False, f"Request failed: {str(e)}")
    else:
        record_test("Save Opportunity", False, "Skipped. No opportunity ID available.")

    # 12. Get Tracked Applications
    if app_id:
        try:
            r = requests.get(f"{base_api}/applications", headers=headers, timeout=5)
            if r.status_code == 200:
                apps = r.json()
                found = any(a.get("id") == app_id for a in apps)
                if found:
                    record_test("Get Applications List", True, f"Found active tracker count: {len(apps)}.", 200, apps)
                else:
                    record_test("Get Applications List", False, f"Saved application ID {app_id} was not in returned tracker list.", 200, apps)
            else:
                record_test("Get Applications List", False, f"Failed to get applications: {r.text}", r.status_code)
        except Exception as e:
            record_test("Get Applications List", False, f"Request failed: {str(e)}")
    else:
        record_test("Get Applications List", False, "Skipped. No saved application.")

    # 13. Update Application Status (Move Status)
    if app_id:
        try:
            payload = {"status": "applied", "notes": "Applied today via online portal."}
            r = requests.patch(f"{base_api}/applications/{app_id}", json=payload, headers=headers, timeout=5)
            if r.status_code == 200:
                updated_app = r.json()
                record_test("Move Application Status", True, f"Updated application status to: {updated_app.get('status')}.", 200, updated_app)
            else:
                record_test("Move Application Status", False, f"Update failed: {r.text}", r.status_code)
        except Exception as e:
            record_test("Move Application Status", False, f"Request failed: {str(e)}")
    else:
        record_test("Move Application Status", False, "Skipped. No saved application.")

    # 14. Notifications
    try:
        r = requests.get(f"{base_api}/notifications", headers=headers, timeout=5)
        if r.status_code == 200:
            notifs = r.json()
            record_test("Get Notifications", True, f"Successfully queried notifications list. Found {len(notifs)} entries.", 200, notifs)
        else:
            record_test("Get Notifications", False, f"Failed to get notifications: {r.text}", r.status_code)
    except Exception as e:
        record_test("Get Notifications", False, f"Request failed: {str(e)}")

    # 15. CSV Export
    try:
        r = requests.get(f"{base_api}/applications/export/csv", headers=headers, timeout=5)
        if r.status_code == 200 and "text/csv" in r.headers.get("content-type", ""):
            csv_len = len(r.text)
            record_test("Export CSV", True, f"Successfully exported tracker CSV. Size: {csv_len} bytes.", 200)
        else:
            record_test("Export CSV", False, f"Expected 200 and text/csv, got: {r.status_code}, {r.headers.get('content-type')}", r.status_code)
    except Exception as e:
        record_test("Export CSV", False, f"Request failed: {str(e)}")
else:
    print("SKIPPING AUTHORIZED ENDPOINT TESTS (Login failed)")
    for name in ["Get Initial Profile", "Update Profile Details", "Get Opportunities Feed", "Filter Opportunities (Scholarship)", "Save Opportunity", "Get Applications List", "Move Application Status", "Get Notifications", "Export CSV"]:
        record_test(name, False, "Skipped due to login failure.")

# 16. Frontend Routes Verification
routes = [
    "/dashboard", "/profile", "/tracker", "/login", "/register", "/opportunities", "/applications", "/onboarding/upload", "/onboarding/review"
]
fe_passed_routes = []
fe_failed_routes = []

for rt in routes:
    try:
        # Avoid following redirects automatically to inspect raw status codes
        r = requests.get(f"{base_fe}{rt}", allow_redirects=False, timeout=5)
        if r.status_code in (200, 301, 302, 307, 308):
            fe_passed_routes.append(f"{rt} ({r.status_code})")
        else:
            fe_failed_routes.append(f"{rt} ({r.status_code})")
    except Exception as e:
        fe_failed_routes.append(f"{rt} (Failed: {str(e)})")

if not fe_failed_routes:
    record_test("Frontend Routes", True, f"All routes loaded or redirected correctly: {', '.join(fe_passed_routes)}")
else:
    record_test("Frontend Routes", False, f"Failed: {', '.join(fe_failed_routes)} | Passed: {', '.join(fe_passed_routes)}")


# Compile Test Report MD
report_path = "test_report.md"
report_content = f"""# E2E Test Report — Zuup Opportunity Agent
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Test User: `{email}`

## Summary
| Test Case | Status | Details |
|---|---|---|
"""
for r in results:
    status_emoji = "✅ PASS" if r["passed"] else "❌ FAIL"
    code_part = f" (`{r['status_code']}`)" if r["status_code"] else ""
    report_content += f"| **{r['name']}** | {status_emoji} | {r['detail']}{code_part} |\n"

report_content += "\n## Detailed API Response Payload Outputs\n"
for r in results:
    if r["response"]:
        report_content += f"### {r['name']}\n"
        report_content += "```json\n"
        import json
        report_content += json.dumps(r["response"], indent=2)
        report_content += "\n```\n\n"

with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_content)

print(f"\nReport written to: {os.path.abspath(report_path)}")
print("=== E2E TESTING COMPLETE ===")
