# Veriscope

Due diligence platform for validating identities against bureau credit reports.

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) or `brew install python` |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) or `brew install node` |
| npm | 9+ | included with Node |

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/nelsond83/veriscope.git
cd veriscope
```

### 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # follow the prompts — these are your login credentials
cd ..
```

### 3. Frontend setup

```bash
cd frontend
npm install
cd ..
```

### 4. Run both servers

Open **two terminal tabs** from the `veriscope/` root.

**Terminal 1 — Django API (port 8000):**
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

**Terminal 2 — Quasar dev server (port 9000):**
```bash
cd frontend
npm run dev
```

Then open **http://localhost:9000** and log in with the superuser credentials you created.

---

## Loading test data

Sample PDFs and a reference CSV are included in `scripts/output/` (pre-generated).

### Import reference identities

1. Go to **Identities** → **Import CSV**
2. Upload `scripts/output/sample_reference_data.csv`

### Upload bureau reports

1. Go to **Upload Reports**
2. Select all 31 PDFs from `scripts/output/reports/`
3. The system will auto-match and run due diligence comparisons

### Expected results after import

| Identity | Result | Flag |
|----------|--------|------|
| Thornton | ✅ Clear | — |
| Nguyen | ✅ Clear | — |
| Subramaniam | ✅ Clear | — |
| Jackson | ✅ Clear | — |
| Kowalski | 🚩 Flagged | Name mismatch (maiden vs married) |
| Hartmann | 🚩 Flagged | DOB mismatch (1990 on reports vs 1991 on file) |
| Castellano | 🚩 Flagged | Address mismatch + extra bureau address |
| Okonkwo | 🚩 Flagged | DOB mismatch + unknown account + extra address |
| Williams | 🚩 Flagged | Name mismatch + unknown account |
| Reyes | 🚩 Flagged | Address mismatch + unknown account |

---

## Regenerating test data (optional)

If you want to regenerate the PDFs from scratch:

```bash
cd backend
source venv/bin/activate
cd ../scripts
python generate_fake_data.py
```

Output is written to `scripts/output/`.

---

## Project structure

```
veriscope/
├── backend/          Django REST API
│   ├── identities/   Identity + comparison models, DD engine
│   ├── reports/      PDF upload + parser
│   └── config/       Django settings + URLs
├── frontend/         Quasar (Vue 3) SPA
│   └── src/
│       ├── pages/    Dashboard, Identities, Upload, etc.
│       └── components/
└── scripts/          Fake data generator + output PDFs
```
