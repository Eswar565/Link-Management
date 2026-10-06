# 🔗 Link Management System (LMS)

A lightweight **web-based Link Manager** built with Flask and SQLite. Organize, search, and manage your web links across customizable categories — all from a clean browser interface.

---

## ✨ Features

- **Add Links** — Save any URL with a title and category
- **Edit Links** — Update title, URL, or category at any time
- **Delete Links** — Remove links with a single click
- **Category Filtering** — Browse links by category with per-category counts in the sidebar
- **Search** — Live search across link titles and URLs
- **Auto URL Scheme** — Automatically prepends `https://` if missing
- **Persistent Storage** — SQLite database via Flask-SQLAlchemy

---

## 📁 Project Structure

```
LMS/
├── app.py              # Flask application factory & route definitions
├── extensions.py       # SQLAlchemy instance (avoids circular imports)
├── models.py           # Link database model
├── requirements.txt    # Python dependencies
├── instance/
│   └── links.db        # SQLite database (auto-created on first run)
└── templates/
    ├── base.html       # Shared base layout
    ├── index.html      # Home dashboard (list, filter, search)
    ├── add.html        # Add new link form
    └── edit.html       # Edit existing link form
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
- pip

### Installation

1. **Clone or download the repository:**
   ```bash
   git clone <repo-url>
   cd LMS
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Open your browser and navigate to:**
   ```
   http://127.0.0.1:5000
   ```

The SQLite database (`instance/links.db`) is created automatically on first run.

---

## 🛠️ Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Backend    | Python 3, Flask 3.0.3   |
| ORM        | Flask-SQLAlchemy 3.1.1  |
| Database   | SQLite                  |
| Frontend   | HTML / Jinja2 Templates |

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
SQLAlchemy==2.0.36
```

---

## 📝 License

This project is open-source and free to use for personal or educational purposes.
