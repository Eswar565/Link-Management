# 🔗 Link Management System (LMS)

A lightweight **web-based Link Manager** built with Flask and PostgreSQL. Organize, search, and manage your web links across customizable categories — all from a clean browser interface.

---

## ✨ Features

- **Add Links** — Save any URL with a title and category
- **Edit Links** — Update title, URL, or category at any time
- **Delete Links** — Remove links with a single click
- **Category Filtering** — Browse links by category with per-category counts in the sidebar
- **Search** — Live search across link titles and URLs
- **Auto URL Scheme** — Automatically prepends `https://` if missing
- **Persistent Storage** — PostgreSQL database via Flask-SQLAlchemy

---

## 📁 Project Structure

```
LMS/
├── app.py                  # Main Flask application, routes, and error handlers
├── extensions.py           # SQLAlchemy & LoginManager instances
├── models.py               # User & Link database models
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # Documentation
├── static/
│   └── img/
│       ├── favicon.svg     # Favicon icon
│       └── logo.svg        # Brand logo
└── templates/
    ├── base.html           # Authenticated base layout (navbar, user dropdown, toasts)
    ├── index.html          # User workspace (links table, categories, search, pins/stars)
    ├── landing.html        # Public landing page with interactive auth modal
    ├── login.html          # Standalone login page
    ├── register.html       # Standalone registration page
    ├── add.html            # Add new link form
    ├── edit.html           # Edit link form
    ├── admin/              # Administrator portal
    │   ├── base.html       # Admin layout with sidebar navigation
    │   ├── dashboard.html  # Platform metrics & category distribution
    │   ├── links.html      # Global links management table
    │   ├── users.html      # User accounts & role management
    │   └── user_form.html  # Create & edit user form
    └── errors/
        ├── 403.html        # 403 Forbidden page
        └── 404.html        # 404 Not Found page
```

---

## 🗂️ Categories

Links are organized into 8 built-in categories:

| Category  | Description                  |
|-----------|------------------------------|
| Meetings  | Meeting links & invites      |
| YouTube   | Video & media links          |
| Study     | Educational resources        |
| Work      | Work-related links           |
| News      | News articles & feeds        |
| Tools     | Utilities & developer tools  |
| Social    | Social media links           |
| Other     | Everything else              |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ installed and running locally
- pip

### Installation & Setup

1. **Clone or download the repository:**
   ```bash
   git clone <repo-url>
   cd LMS
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv

   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   # or Windows (CMD)
   .venv\Scripts\activate.bat

   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database:**
   In your PostgreSQL shell (`psql`) or pgAdmin:
   ```sql
   CREATE DATABASE link_management;
   ```

5. **Configure environment variables:**
   Copy `.env.example` to `.env`:
   ```bash
   # Windows (PowerShell)
   Copy-Item .env.example .env

   # macOS / Linux / Git Bash
   cp .env.example .env
   ```
   Open `.env` and set your local PostgreSQL credentials:
   ```env
   DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/link_management
   ```

6. **Run the application:**
   ```bash
   python app.py
   ```

7. **Open your browser and navigate to:**
   ```
   http://127.0.0.1:5000
   ```

The database tables are automatically initialized on startup when the app connects to PostgreSQL.

---

## 🛠️ Tech Stack

| Layer      | Technology               |
|------------|--------------------------|
| Backend    | Python 3, Flask 3.0.3    |
| ORM        | Flask-SQLAlchemy 3.1.1   |
| Database   | PostgreSQL (via psycopg) |
| Frontend   | HTML / Jinja2 Templates  |

---

## 📡 API Routes

| Method | Route              | Description              |
|--------|--------------------|--------------------------|
| GET    | `/`                | Home dashboard           |
| GET    | `/?category=<cat>` | Filter by category       |
| GET    | `/?q=<query>`      | Search links             |
| GET    | `/add`             | Show add-link form       |
| POST   | `/add`             | Submit new link          |
| GET    | `/edit/<id>`       | Show edit-link form      |
| POST   | `/edit/<id>`       | Submit link update       |
| POST   | `/delete/<id>`     | Delete a link            |

---

## 🗄️ Database Model

**Table:** `links`

| Column       | Type         | Description                        |
|--------------|--------------|------------------------------------|
| `id`         | Integer (PK) | Auto-incrementing primary key      |
| `title`      | String(200)  | Display name for the link          |
| `url`        | String(2048) | Full URL of the link               |
| `category`   | String(100)  | Category label                     |
| `created_at` | DateTime     | UTC timestamp of creation (auto)   |

---

## 📦 Dependencies

```
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
SQLAlchemy==2.0.36
psycopg==3.3.6
python-dotenv==1.2.4
```

---

## 📝 License

This project is open-source and free to use for personal or educational purposes.
