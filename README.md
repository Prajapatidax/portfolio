# ⚡ Dax Prajapati — Portfolio & UI Showcase Engine

> Production-ready personal portfolio, interactive UI Design Showcase, Quotation Wizard CRM, and Admin Control Center built with Python Flask, Jinja2, Vanilla JavaScript, Neon PostgreSQL, and Neon Object Storage (AWS S3-compatible).
>
> **🌐 Production URL:** [https://prajapatidax.co.in](https://prajapatidax.co.in)  
> **🛡️ Admin Login:** `/admin/login/version/101`

---

## 🚀 Running Locally (Standard Flask)

### 1. Prerequisites
- Python 3.12+ (or 3.11+)
- Virtual environment (`venv` or `conda`)

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/daxp1707/portfolio.git
cd portfolio

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
```

### 3. Run the Application
```bash
python app.py
```
Or via the Flask CLI:
```bash
flask --app app run --port 5000
```
Open **`http://localhost:5000`** in your browser.

---

## ☁️ Deploying & Running on Vercel

The application is pre-configured for seamless serverless deployment on [Vercel](https://vercel.com) via `api/index.py` and `vercel.json`.

### Option A: Deploy via Vercel Dashboard (GitHub Integration)
1. Push your repository to GitHub.
2. In the [Vercel Dashboard](https://vercel.com/dashboard), click **Add New... > Project**.
3. Import your `portfolio` repository.
4. Set **Framework Preset** to **Other** (Vercel automatically detects Python and `vercel.json`).
5. Under **Environment Variables**, add the variables listed below.
6. Click **Deploy**.

### Option B: Deploy via Vercel CLI
```bash
# Install Vercel CLI globally
npm i -g vercel

# Test locally with Vercel serverless environment
vercel dev

# Deploy to production
vercel --prod
```

---

## 🔐 Required Environment Variables (Vercel & Production)

Configure these in the **Vercel Project Settings > Environment Variables**:

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `SECRET_KEY` | Flask session cryptographic key | `your-cryptographically-random-secret-key` |
| `DATABASE_URL` | Neon PostgreSQL pooled connection string | `postgresql+psycopg://user:pass@ep-...pooler...neon.tech/neondb?sslmode=require` |
| `ADMIN_NAME` | Admin initial account display name | `Dax Prajapati` |
| `ADMIN_EMAIL` | Admin account login email | `admin@prajapatidax.co.in` |
| `ADMIN_PASSWORD` | Admin initial password | `YourSecurePassword2026!` |
| `NEON_STORAGE_BUCKET` | Neon Object Storage bucket name | `photos` |
| `AWS_ACCESS_KEY_ID` | Neon S3 access key ID | `your-s3-access-key` |
| `AWS_SECRET_ACCESS_KEY` | Neon S3 secret access key | `your-s3-secret-key` |
| `AWS_ENDPOINT_URL_S3` | Neon S3 endpoint URL | `https://s3.ap-southeast-1.amazonaws.com` |
| `AWS_REGION` | Neon S3 region | `ap-southeast-1` |
| `SKIP_DB_INIT` | *(Optional)* Set to `1` on Vercel for faster cold-starts | `1` |

---

## 📁 Project Architecture

```text
portfolio/
├── api/
│   └── index.py            # Vercel Serverless Function entry point
├── app.py                  # Standard Flask local entry point (python app.py)
├── config.py               # Application configuration (Neon Postgres + S3)
├── vercel.json             # Vercel rewrites & template/static inclusion
├── .vercelignore           # Optimized build exclusion list
├── .python-version         # Pinned Python version (3.12)
├── backend/
│   ├── __init__.py         # Flask app factory with ProxyFix & security headers
│   ├── models/             # SQLAlchemy ORM models (Admins, Quotations, Designs, CRM)
│   ├── routes/             # Blueprints (Main, Showcase, Quotations, Admin, API)
│   ├── services/           # Business logic (Auth, S3 Storage, Designs)
│   └── utils/              # Security decorators, CSRF, rate limiters
├── templates/              # Jinja2 HTML templates
│   ├── index.html          # Portfolio homepage
│   ├── design-showcase.html# UI Design Showcase catalog
│   ├── quotation-wizard.html# 6-step project quotation wizard
│   ├── admin/              # Admin Control Center (CRM, Media, Settings)
│   └── 404.html            # Custom error pages
├── static/                 # CSS, JavaScript, and static assets
│   ├── css/custom.css      # Showcase and portfolio styling
│   ├── js/                 # Client controllers (wizard, showcase, admin, consent)
│   └── assets/             # Resume.pdf, headshot, project logos
├── tests/                  # Automated pytest suite (45 tests)
├── requirements.txt        # Python dependencies
└── agent.md                # Comprehensive API & architecture specification
```

---

## 🧪 Running Automated Tests

Run the full pytest suite (45 automated test cases):
```bash
python -m pytest
```

---

## 📬 Contact & Links

- **Website:** [https://prajapatidax.co.in](https://prajapatidax.co.in)
- **LinkedIn:** [linkedin.com/in/dax-prajapati1707](https://www.linkedin.com/in/dax-prajapati1707)
- **Email:** [admin@prajapatidax.co.in](mailto:admin@prajapatidax.co.in)
