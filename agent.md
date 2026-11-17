# API Endpoints & Architecture Specification for Autonomous Agents

**Project:** Dax Prajapati Personal Portfolio & Quotation Control Center  
**Base URL (Local):** `http://localhost:5000`  
**Production URL:** `https://prajapatidax.co.in`  
**Framework:** Python Flask (Unified Server Architecture)  
**Database:** Neon PostgreSQL (with SQLite local fallback)  
**Object Storage:** Neon Object Storage (AWS S3-compatible, bucket: `photos`)  

---

## 1. Authentication & Security Architecture

### A. Admin Authentication
- **Session Cookie:** `prajapati_session` (`HttpOnly`, `SameSite=Lax`, `Secure` in production).
- **Protected URLs:** Guarded by `@admin_required` decorator. Unauthenticated requests to HTML routes redirect to `/admin/login/version/101`; unauthenticated requests to `/api/` or JSON endpoints return `401 Unauthorized`.
- **Obscured Login URL:** `/admin/login/version/101` is the **only** valid login endpoint.
- **Honeypot Decoys:** Generic admin routes (`/admin`, `/admin/`, `/admin/login`, `/admin/login/`, `/login/admin`, `/login/admin/`) strictly return `404 Not Found` to prevent discovery.

### B. CSRF Protection
- **Header:** `X-CSRF-Token` or `X-CSRFToken`
- **Form Body:** `csrf_token`
- **Validation:** Enforced on mutation requests (`POST`) across public forms, API submissions, and administrative controls.

### C. Rate Limiting (Sliding Window per IP)
- **Login attempts:** 5 attempts per 10 minutes (`rate_limit("admin_login", max_attempts=5, window_seconds=600)`).
- **Quotation submissions:** 15 attempts per hour (`rate_limit("quotation_submit", max_attempts=15, window_seconds=3600)`).
- **Exceeded response:** HTTP `429 Too Many Requests` with retry cooldown headers.

---

## 2. Public REST APIs

### 1. Health Check
- **Endpoint:** `GET /api/health`
- **Auth:** None
- **Description:** Verifies service uptime and live database connectivity.
- **Response `200 OK`:**
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "timestamp": "2026-11-17T18:00:00.000000+00:00",
    "version": "2.0.0"
  }
  ```

### 2. Cookie Consent Management
- **Endpoint:** `POST /api/cookie-consent`
- **Auth:** None (records hashed IP + client consent preferences)
- **Content-Type:** `application/json`
- **Caller:** `static/js/cookie-consent.js`
- **Request Body:**
  ```json
  {
    "consent_uuid": "optional-uuid-string",
    "analytics": true,
    "marketing": false,
    "version": "1.0"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "status": "success",
    "consent_uuid": "b3e34b79-3739-4ab5-9e11-73626fa5248a",
    "preferences": {
      "essential": true,
      "analytics": true,
      "marketing": false
    }
  }
  ```

### 3. Public Design Catalog
- **Endpoint:** `GET /api/designs`
- **Auth:** None
- **Description:** Fetches all published UI showcase design templates and active categories.
- **Caller:** `static/js/showcase.js`, `static/js/quotation-wizard.js`
- **Response `200 OK`:**
  ```json
  {
    "status": "success",
    "categories": [
      {
        "id": 1,
        "name": "Minimal & Clean",
        "slug": "minimal-clean",
        "description": "Streamlined layouts...",
        "display_order": 1
      }
    ],
    "designs": [
      {
        "id": 1,
        "design_id": "DSGN-MIN-01",
        "slug": "zenith-minimal",
        "name": "Zenith Minimalist Editorial",
        "category_id": 1,
        "primary_color": "#2563EB",
        "theme_mode": "light",
        "is_published": true
      }
    ]
  }
  ```

### 4. Contact Message API Submission
- **Endpoint:** `POST /api/contact`
- **Auth:** CSRF Token (`X-CSRF-Token` header or `csrf_token` field)
- **Content-Type:** `application/json` or `application/x-www-form-urlencoded`
- **Caller:** `static/js/main.js`, public contact form
- **Request Body:**
  ```json
  {
    "csrf_token": "token-string",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "subject": "Web Development Consultation",
    "message": "Interested in building a high-performance web platform."
  }
  ```
- **Response `201 Created`:**
  ```json
  {
    "status": "success",
    "message": "Message sent successfully! Dax will get back to you shortly.",
    "id": 42
  }
  ```
- **Response `422 Unprocessable Entity`:**
  ```json
  {
    "status": "error",
    "errors": {
      "email": "Please provide a valid email address"
    }
  }
  ```

---

## 3. Quotation Engine APIs

### 1. Submit Project Quotation Request
- **Endpoint:** `POST /api/quotation`
- **Rate Limit:** 15 requests / hour
- **Auth:** Optional CSRF header; payload sanitized server-side
- **Content-Type:** `application/json`
- **Caller:** `static/js/quotation-wizard.js`
- **Validation Rules:**
  - `project_type`: Must be one of `["Personal Website", "Business Website", "Portfolio Website", "Landing Page", "E-commerce Website", "SaaS Platform", "Web Application", "Admin Dashboard", "Other"]`
  - `budget_range`: Must be one of `["Under ₹5,000", "₹5,000–₹10,000", "₹10,000–₹25,000", "₹25,000–₹50,000", "₹50,000+", "Not decided yet"]`
  - `timeline`: Free text string (e.g. `"2-3 Weeks"`)
  - `customer_name`: 2 to 100 characters
  - `customer_email`: Valid email format
  - `customer_phone`: Optional phone/WhatsApp string
  - `project_name`: 2 to 150 characters
  - `project_description`: 10 to 5,000 characters
  - `selected_designs`: Array of template IDs or slugs (e.g. `["DSGN-MIN-01"]`)
  - `customization`: Object containing `primary_color`, `secondary_color`, `theme_mode`, `typography_preference`, `animation_preference`, `layout_preference`, `platform_preference`
  - `features`: Array of string feature labels
- **Request Body Example:**
  ```json
  {
    "project_type": "SaaS Platform",
    "budget_range": "₹25,000–₹50,000",
    "timeline": "2-3 Weeks",
    "customer_name": "Alex Mercer",
    "customer_email": "alex.mercer@example.com",
    "customer_phone": "+91 9876543210",
    "project_name": "CloudFleet Telemetry",
    "project_description": "We need an ultra-modern SaaS telemetry dashboard with dark mode and real-time graphs.",
    "reference_website": "https://example.com",
    "selected_designs": ["DSGN-MIN-01", "DSGN-DRK-03"],
    "customization": {
      "primary_color": "#06B6D4",
      "secondary_color": "#030712",
      "theme_mode": "dark",
      "typography_preference": "Plus Jakarta Sans + Inter",
      "animation_preference": "Smooth & Subtle",
      "layout_preference": "Modern Grid",
      "platform_preference": "desktop-first"
    },
    "features": [
      "Responsive design",
      "Admin dashboard",
      "API integration",
      "Search functionality"
    ]
  }
  ```
- **Response `201 Created`:**
  ```json
  {
    "status": "success",
    "message": "Thank you for your interest! Your project request has been successfully submitted. I will review your requirements and get back to you.",
    "reference_id": "QT-9B4F1A",
    "data": {
      "reference_id": "QT-9B4F1A",
      "customer_name": "Alex Mercer",
      "project_name": "CloudFleet Telemetry",
      "project_type": "SaaS Platform",
      "budget_range": "₹25,000–₹50,000",
      "timeline": "2-3 Weeks",
      "status": "new",
      "created_at": "2026-11-17 18:30 UTC"
    }
  }
  ```

### 2. Query Quotation Public Status
- **Endpoint:** `GET /api/quotation/<reference_id>`
- **Auth:** None (public tracking by reference ID)
- **Response `200 OK`:**
  ```json
  {
    "status": "success",
    "reference_id": "QT-9B4F1A",
    "project_name": "CloudFleet Telemetry",
    "project_type": "SaaS Platform",
    "quotation_status": "under_review",
    "proposed_amount": "₹45,000",
    "estimated_delivery": "14 business days",
    "created_at": "2026-11-17"
  }
  ```
- **Response `404 Not Found`:**
  ```json
  {
    "status": "error",
    "message": "Quotation reference not found",
    "error_code": 404
  }
  ```

---

## 4. UI Design Showcase & Storage Endpoints

### 1. Design Showcase Hub
- **Endpoint:** `GET /design-showcase` (or `/design-showcase/`)
- **Query Params:** `?category=<slug>` (filters templates by category)
- **Response:** Renders `templates/design-showcase.html`

### 2. Design Reference Detail Page
- **Endpoint:** `GET /design-showcase/preview/<slug>`
- **Description:** Renders responsive desktop, tablet, and mobile design reference mockups for template `<slug>`.
- **Response:** Renders `templates/design-preview.html`

### 3. Interactive Design Mockup Frame
- **Endpoint:** `GET /design-showcase/frame/<slug>`
- **Description:** Renders responsive iframe container with live CSS/HTML component previews.
- **Response:** Renders `templates/showcase-frame.html`

### 4. Neon Object Storage Proxy Redirect
- **Endpoint:** `GET /storage/preview/<path:object_key>`
- **Description:** Secure proxy for private Neon Object Storage (`photos` bucket). Issues an HTTP `307 Temporary Redirect` to a short-lived S3 pre-signed URL with `Cache-Control: public, max-age=3600`.
- **Fallback:** Returns default `static/assets/photo.png` on missing assets or S3 connectivity issues.

---

## 5. Admin Control Center Endpoints

> **All routes below require active admin authentication (`prajapati_session` cookie) except the login page.**

### A. Authentication
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET, POST` | `/admin/login/version/101` | Secret administrative login page. Authenticates email and password. |
| `GET, POST` | `/admin/logout` | Clears admin session and redirects to homepage. |
| `GET` | `/admin`, `/admin/login`, `/login/admin` | Honeypot traps: strictly return `404 Not Found`. |

### B. Dashboard & Analytics
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/admin/dashboard` | Central command hub displaying total enquiries, new requests, reviewing, quotation status breakdown, and recent activities. |

### C. Quotation Management CRM
| Method | Endpoint | Request Payload / Format | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/admin/quotations` | Query: `?status=...&priority=...&q=...&sort=...&page=...` | Paginated, filtered, searchable quotation requests table. |
| `GET` | `/admin/quotations/<int:quote_id>` | Header: `Accept: application/json` or HTML | Returns full quotation details (customer info, selected templates, device preview links, custom specs, status history, admin notes). |
| `POST` | `/admin/quotations/<int:quote_id>/status` | `status`, `proposed_amount`, `estimated_delivery`, `comments` | Transitions quotation status across all 10 stages (`new`, `reviewing`, `requirements_clarification`, `quotation_prepared`, `quotation_sent`, `negotiation`, `accepted`, `rejected`, `completed`, `archived`). |
| `POST` | `/admin/quotations/<int:quote_id>/priority` | `priority` (`low`, `normal`, `high`, `urgent`) | Updates priority level. |
| `POST` | `/admin/quotations/<int:quote_id>/note` | `note_text` | Adds a private timestamped administrative note. |
| `POST` | `/admin/quotations/<int:quote_id>/archive` | None (CSRF only) | Toggles quotation archived state. |
| `POST` | `/admin/quotations/<int:quote_id>/delete` | None (CSRF only) | Permanently deletes quotation and cascaded relations with confirmation. |

### D. Design Showcase & Template Management
| Method | Endpoint | Request Payload / Format | Description |
| :--- | :--- | :--- | :--- |
| `GET, POST` | `/admin/designs` | Form fields: `name`, `slug`, `category_id`, `description`, `primary_color`, `theme_mode` | Lists all templates; POST creates a new showcase template. |
| `GET, POST` | `/admin/designs/<int:design_id>` | Form fields: updated template metadata | Edit template specifications. |
| `POST` | `/admin/designs/<int:design_id>/toggle-status` | None | Toggles publication status (`is_published`). |
| `POST` | `/admin/designs/<int:design_id>/upload-asset` | `multipart/form-data`: `file`, `device_type` (`desktop`, `tablet`, `mobile`) | Uploads template preview image directly to Neon S3 (`photos` bucket) and links asset record. |
| `POST` | `/admin/designs/<int:design_id>/delete` | None | Archives/deletes design template. |
| `GET, POST` | `/admin/categories` | Form fields: `name`, `slug`, `description`, `display_order` | Category manager; POST adds a category. |
| `POST` | `/admin/categories/<int:cat_id>/edit` | Updated category form fields | Modifies existing category. |
| `POST` | `/admin/categories/<int:cat_id>/delete` | None | Deletes category (sets template FK to null). |

### E. Media Library (Neon Object Storage `photos` Bucket)
| Method | Endpoint | Request Payload / Format | Description |
| :--- | :--- | :--- | :--- |
| `GET, POST` | `/admin/media` | `multipart/form-data`: `media_file`, `folder` | Lists S3 bucket objects and uploaded assets; POST uploads new asset with WebP optimization. |
| `POST` | `/admin/media/<int:asset_id>/delete` | None | Deletes media asset record from database and Neon S3 storage. |

### F. Contact Inquiries & CRM
| Method | Endpoint | Request Payload / Format | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/admin/contact-messages` | Query: `?status=...&q=...&page=...` | Lists public inquiries. |
| `GET` | `/admin/contact-messages/<int:msg_id>` | JSON response | Returns message details and auto-marks message as `read`. |
| `POST` | `/admin/contact-messages/<int:msg_id>/reply` | `reply_message` | Records administrative follow-up note in database and sets status to `replied` (no email dispatched). |
| `POST` | `/admin/contact-messages/<int:msg_id>/status` | `status` (`unread`, `read`, `replied`, `archived`) | Updates inquiry status. |
| `POST` | `/admin/contact-messages/<int:msg_id>/delete` | None | Permanently deletes inquiry. |

### G. In-App Notifications API
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/admin/api/notifications` | Returns JSON of recent administrative notifications and unread count. |
| `POST` | `/admin/api/notifications/<int:notif_id>/read` | Marks single notification as read. |
| `POST` | `/admin/api/notifications/read-all` | Marks all admin notifications as read. |

### H. Audit Trail & Settings
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/admin/activity` | Searchable, paginated audit log of admin operations, login history, and quotation changes. |
| `GET, POST` | `/admin/settings` | Manages admin credentials (password change), portfolio public settings, and displays live Neon Storage status. |

---

## 6. Public Pages & SEO Endpoints

| Method | Endpoint | Template / Handler | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/` or `/index.html` | `templates/index.html` | Hero portfolio homepage. |
| `GET` | `/about` or `/about.html` | `templates/about.html` | Background, education, experience, skills, and engineering philosophy. |
| `GET` | `/projects` or `/projects.html` | `templates/projects.html` | Software project catalog (Devvault, Mindmate, Sortify, Earth Vision). |
| `GET` | `/contact` or `/contact.html` | `templates/contact.html` | Public contact inquiry form. |
| `GET` | `/quotation` | `templates/quotation-wizard.html` | Interactive 6-step project quotation wizard. |
| `GET` | `/Resume.pdf` or `/resume` | `send_from_directory('static/assets', 'Resume.pdf')` | Direct download of Dax Prajapati's resume. |
| `GET` | `/assets/<path:filename>` | `send_from_directory('static/assets', filename)` | Legacy path compatibility handler. |
| `GET` | `/robots.txt` | Direct plain-text | Dynamic robots directives with sitemap reference. |
| `GET` | `/sitemap.xml` | Direct XML | Search engine sitemap indexing static routes and published templates. |
| `404` | `<any invalid path>` | `templates/404.html` | Custom styled 404 error page. |

---

## 7. Frontend Client Script to Endpoint Mapping

| Client Script File | Endpoints Invoked | Method | Payload / Trigger |
| :--- | :--- | :--- | :--- |
| `static/js/quotation-wizard.js` | `/api/quotation` | `POST` | Submits complete quotation payload. |
| `static/js/cookie-consent.js` | `/api/cookie-consent` | `POST` | Submits cookie consent preferences. |
| `static/js/main.js` | `/api/contact` | `POST` | Submits AJAX contact form. |
| `static/js/showcase.js` | `/api/designs` | `GET` | Fetches templates and category filters dynamically. |
| `static/js/admin.js` | `/admin/api/notifications` | `GET` | Polls unread notifications badge count. |
| `static/js/admin.js` | `/admin/api/notifications/<id>/read` | `POST` | Marks notification as read. |
| `static/js/admin.js` | `/admin/api/notifications/read-all` | `POST` | Marks all notifications as read. |
| `templates/admin/contact/list.html` | `/admin/contact-messages/<id>` | `GET` | Loads message details into modal. |
| `templates/admin/contact/list.html` | `/admin/contact-messages/<id>/reply` | `POST` | Saves administrative follow-up note. |
| `templates/admin/quotations/detail.html` | `/admin/quotations/<id>/status` | `POST` | Updates quotation status and proposed amount. |
| `templates/admin/quotations/detail.html` | `/admin/quotations/<id>/priority` | `POST` | Sets priority (`low`, `normal`, `high`, `urgent`). |
| `templates/admin/quotations/detail.html` | `/admin/quotations/<id>/note` | `POST` | Saves private internal note. |

---

## 8. Inactive & Deprecated Endpoints Notice

As per requirements, **all outgoing/incoming email services (SMTP, Resend API, Flask-Mail) have been completely removed**.

Agents and scripts must **never** call or expect the following removed endpoints:
- `POST /admin/quotations/<id>/preview-email` &rarr; Returns `404 Not Found`
- `POST /admin/quotations/<id>/send-email` &rarr; Returns `404 Not Found`
- `POST /admin/quotations/<id>/resend-acknowledgement` &rarr; Returns `404 Not Found`
- Any SMTP / Resend background worker tasks &rarr; **None exist**.
