# 🚀 Zuup Opportunity Agent — How to Use the App
### *Written simply — even a kid can follow this!* 🧒👧

---

## 📋 Table of Contents
1. [What is Zuup?](#what-is-zuup)
2. [Starting the App](#starting-the-app)
3. [Login Credentials](#login-credentials)
4. [Step-by-Step: How to Use](#step-by-step-how-to-use)
   - [Step 1 — Create Your Account](#step-1--create-your-account)
   - [Step 2 — Set Up Your Profile](#step-2--set-up-your-profile)
   - [Step 3 — Browse Opportunities](#step-3--browse-opportunities)
   - [Step 4 — Save & Track Applications](#step-4--save--track-applications)
5. [All the Pages Explained](#all-the-pages-explained)
6. [For Developer (Sarang)](#-for-sarang-developer-guide)
7. [Troubleshooting](#troubleshooting)

---

## 🤔 What is Zuup?

Imagine you had a **super smart robot friend** 🤖 who spends all day searching the whole internet to find:
- 🎓 **Scholarships** — free money for your studies!
- 💼 **Internships** — work experience at cool companies
- 🏆 **Fellowships** — special programs for talented students
- 💻 **Hackathons** — coding competitions with prizes
- ✈️ **Exchange programs** — study in another country!

That's Zuup! It finds all of these for YOU, sorted by how well they match your skills and interests.

---

## 🖥️ Starting the App

> **Think of this like turning on your gaming console before playing!**

Open a **PowerShell or Terminal** window, go into the project folder, and type:

```powershell
docker compose up -d
```

Then open your browser and go to:

| What | Link |
|---|---|
| 🌐 **Website (the app)** | http://localhost:3000 |
| 🔧 **API Docs (for developers)** | http://localhost:8000/docs |
| ❤️ **Health Check** | http://localhost:8000/health |

To **stop the app**:
```powershell
docker compose down
```

To **see what's happening** (logs):
```powershell
docker compose logs -f
```

---

## 🔑 Login Credentials

### 👨‍💻 Demo Account (Ready to Use!)

| Field | Value |
|---|---|
| **Email** | `demo@zuup.dev` |
| **Password** | `Zuup@1234` |

### 👤 Sarang's Account (Owner)

| Field | Value |
|---|---|
| **Email** | `sarangchaudhari635@gmail.com` |
| **Password** | *(the one you set when you registered on the site)* |

### 🆕 Create Your Own Account
You can also make a **brand new account** at:
👉 http://localhost:3000/register

Just type your name, email, and a password. That's it! 🎉

> 💡 **Password rules:** At least 8 characters, include a number and a symbol (like `@` or `!`)

---

## 📖 Step-by-Step: How to Use

### Step 1 — Create Your Account

1. Open http://localhost:3000
2. You'll be taken to the **Login page** 🔐
3. If you're new → click **"Register"** or go to http://localhost:3000/register
4. Fill in:
   - Your **full name** (e.g., "Sarang Chaudhari")
   - Your **email** (e.g., "you@example.com")
   - A **password** (e.g., "MyPass@123")
5. Click the **Register** button ✅
6. You're in! The app will log you in automatically.

---

### Step 2 — Set Up Your Profile

> **Think of your profile like your report card + résumé combined!**
> The better you fill it, the better opportunities Zuup finds for you! 🎯

1. Go to the **Profile page**: http://localhost:3000/profile
2. Fill in these sections:

   | Section | What to write |
   |---|---|
   | **Full Name** | Your real name |
   | **Location** | Your city and country (e.g., "Mumbai, India") |
   | **Field of Study** | What you're studying (e.g., "Computer Science") |
   | **Status** | Currently Enrolled / Recent Graduate / Graduated |
   | **GPA** | Your grades (optional, e.g., 3.7) |
   | **Skills** | Things you know: Python, Design, Writing, etc. |
   | **Interests** | Things you love: AI, Music, Sports, etc. |
   | **Languages** | Languages you speak: English, Hindi, etc. |
   | **Career Goals** | What you want to do in life (write a few sentences) |

3. Click **"Save Changes"** 💾
4. Watch the **Profile Strength bar** go up! Try to get it above 80% for the best matches.

---

### Step 3 — Browse Opportunities

> **This is like scrolling through a special Instagram — but every post is a chance to win something amazing!** 📱✨

1. Go to the **Dashboard**: http://localhost:3000/dashboard
2. You'll see a **feed of opportunities** matched for you!
3. Each card shows:
   - 🟣 **Type badge** — Scholarship, Internship, Fellowship, etc.
   - ⏰ **Deadline chip** — how many days left
   - 🌐 **Remote** tag — if you can do it from home
   - 💰 **Fully Funded** tag — if they pay ALL your expenses
   - **Match score ring** (the circle) — how well it fits YOU (green = great match!)

4. **Filter your feed:**
   - 🔍 **Search box** — type keywords like "AI" or "Europe"
   - **Type buttons** — click Scholarship, Internship etc. to filter
   - 🌐 **Remote Only** — see only work-from-home opportunities
   - **Min score slider** — show only high-match opportunities

5. **On each card:**
   - Click **"Save"** → adds it to your tracker 🔖
   - Click **"View →"** → opens the official opportunity website

---

### Step 4 — Save & Track Applications

> **Think of this like a Kanban board at school — moving sticky notes across columns!** 📋

1. Go to the **Tracker**: http://localhost:3000/tracker
2. See all your saved opportunities in **5 columns**:

   | Column | What it means |
   |---|---|
   | 🔖 **Saved** | You bookmarked it, not applied yet |
   | 📤 **Applied** | You sent in your application |
   | 👀 **Under Review** | They are looking at your application |
   | ⭐ **Shortlisted** | You made the short list! Great job! |
   | 🏆 **Outcome** | Final result (accepted or rejected) |

3. **Move a card** between columns by clicking the small arrow buttons on each card
4. **Click any card** → a panel slides in from the right where you can:
   - ✏️ Add **personal notes** about the application
   - 🔗 Open the application link directly
5. Click **"↓ Export CSV"** to download all your applications as a spreadsheet!

---

## 📄 All the Pages Explained

| Page | URL | What It Does |
|---|---|---|
| 🏠 **Login** | `/login` | Sign into your account |
| 📝 **Register** | `/register` | Make a new account |
| 🎯 **Onboarding** | `/onboarding` | First-time setup wizard |
| 📊 **Dashboard** | `/dashboard` | Browse all matched opportunities |
| 👤 **Profile** | `/profile` | Edit your details and skills |
| 📋 **Tracker** | `/tracker` | Track your applications (Kanban board) |
| 🔀 **Opportunities** | `/opportunities` | Same as dashboard (auto-redirects) |
| 🔀 **Applications** | `/applications` | Same as tracker (auto-redirects) |

---

## 🧑‍💻 For Sarang (Developer Guide)

### Running the App

```powershell
# Start everything (first time or after code changes)
docker compose up --build -d

# Start without rebuilding (faster)
docker compose up -d

# Stop everything
docker compose down

# View live logs
docker compose logs -f

# View only backend logs
docker compose logs -f backend

# Restart just the frontend (after UI changes)
docker compose restart frontend
```

### Database Management

```powershell
# Run migrations (needed after schema changes)
docker compose exec backend alembic upgrade head

# Generate a new migration after changing models
docker compose exec backend alembic revision --autogenerate -m "your_change_name"

# Check migration status
docker compose exec backend alembic history

# Connect to the database directly
docker compose exec postgres psql -U zuup_user -d zuup_db
```

### API Testing (PowerShell)

```powershell
# Health check
Invoke-RestMethod "http://localhost:8000/health"

# Register a user
$body = '{"email":"test@zuup.dev","password":"Test@1234","full_name":"Test User"}'
Invoke-RestMethod "http://localhost:8000/auth/register" -Method POST -ContentType "application/json" -Body $body

# Login and get token
$login = "username=test@zuup.dev&password=Test@1234&grant_type=password"
$r = Invoke-RestMethod "http://localhost:8000/auth/login" -Method POST -ContentType "application/x-www-form-urlencoded" -Body $login
$token = $r.access_token

# Use the token
Invoke-RestMethod "http://localhost:8000/profile/me" -Headers @{Authorization="Bearer $token"}
```

### Environment Variables (`.env`)

| Variable | What it does | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection | `localhost:5435/zuup_db` |
| `REDIS_URL` | Redis for background jobs | `localhost:6379` |
| `JWT_SECRET_KEY` | Signs login tokens | `zuup-super-secret-dev-key...` |
| `ANTHROPIC_API_KEY` | AI resume parsing (optional) | *(empty = mock mode)* |
| `OPENAI_API_KEY` | Semantic matching (optional) | *(empty = mock embeddings)* |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long login lasts | `15` minutes |

### Ports

| Service | Port |
|---|---|
| Frontend (Next.js) | `3000` |
| Backend (FastAPI) | `8000` |
| PostgreSQL | `5435` |
| Redis | `6379` |

### Project Structure

```
zuup-opportunity-agent/
├── backend/               ← Python FastAPI server
│   ├── app/
│   │   ├── api/           ← Route handlers (auth, profile, opportunities...)
│   │   ├── core/          ← Config, auth, rate limiting
│   │   ├── models/        ← Database models
│   │   └── worker/        ← Celery background jobs
│   ├── migrations/        ← Alembic DB migrations
│   └── requirements.txt   ← Python packages
├── zuup-frontend/         ← Next.js React frontend
│   └── app/
│       ├── (auth)/        ← Login and Register pages
│       └── (app)/         ← Dashboard, Profile, Tracker pages
├── docker-compose.yml     ← Starts all services
└── .env                   ← Your secret keys and config
```

---

## 🔧 Troubleshooting

### I can't log in!
- Make sure the app is running (`docker compose up -d`)
- Check your email and password are correct
- Try resetting: go to Register and make a new account

### Dashboard shows no opportunities
- Your agent is still searching! It takes a few minutes after first run
- Make sure your Profile is filled in — better profile = better matches
- The AI needs API keys to work fully (see `.env` file)

### Page shows an error or blank screen
- Try refreshing the browser (F5)
- Open browser DevTools (F12) → Console tab to see error details
- Check backend logs: `docker compose logs backend`

### Docker won't start
- Make sure Docker Desktop is open and running
- Try: `docker compose down` then `docker compose up --build -d`

### Database errors
```powershell
docker compose exec backend alembic upgrade head
```

---

## 🎉 Quick Cheat Sheet

```
START APP   →  docker compose up -d
OPEN APP    →  http://localhost:3000
LOGIN       →  demo@zuup.dev  /  Zuup@1234
FIND OPPS   →  /dashboard
MY PROFILE  →  /profile
TRACK APPS  →  /tracker
API DOCS    →  http://localhost:8000/docs
STOP APP    →  docker compose down
```

---

*Made with love by Sarang Chaudhari — Zuup Opportunity Agent*
