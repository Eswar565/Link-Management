import os

from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

from extensions import db
from models import Link

# Load variables from .env
load_dotenv()


CATEGORIES = [
    "Meetings",
    "YouTube",
    "Study",
    "Work",
    "News",
    "Tools",
    "Social",
    "Other",
]


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "smart-link-tracker-secret-key-2024"

    # PostgreSQL database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

    # SQLAlchemy connection pool settings
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize database
    db.init_app(app)

    # Create tables if they don't already exist
    with app.app_context():
        db.create_all()

    # ── Routes ──────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        """Home dashboard – list all links, filterable by category."""

        selected_category = request.args.get("category", "")
        search_query = request.args.get("q", "").strip()

        query = Link.query

        # Filter by category
        if selected_category:
            query = query.filter_by(category=selected_category)

        # Search by title or URL
        if search_query:
            query = query.filter(
                Link.title.ilike(f"%{search_query}%")
                | Link.url.ilike(f"%{search_query}%")
            )

        links = query.order_by(Link.created_at.desc()).all()

        # Count links in each category
        category_counts = {
            cat: Link.query.filter_by(category=cat).count()
            for cat in CATEGORIES
        }

        return render_template(
            "index.html",
            links=links,
            categories=CATEGORIES,
            category_counts=category_counts,
            selected_category=selected_category,
            search_query=search_query,
            total=Link.query.count(),
        )

    # ── Add Link ────────────────────────────────────────────────────────────

    @app.route("/add", methods=["GET", "POST"])
    def add_link():
        """Create a new link."""

        if request.method == "POST":

            title = request.form.get("title", "").strip()

            url = request.form.get("url", "").strip()

            category = request.form.get("category", "Other").strip()

            # Validate title and URL
            if not title or not url:
                flash("Title and URL are required.", "danger")

                return render_template("add.html", categories=CATEGORIES)

            # Add https:// if no scheme is provided
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            # Create link
            new_link = Link(title=title, url=url, category=category)

            db.session.add(new_link)
            db.session.commit()

            flash(f'"{title}" has been added successfully!', "success")

            return redirect(url_for("index"))

        return render_template("add.html", categories=CATEGORIES)

    # ── Edit Link ───────────────────────────────────────────────────────────

    @app.route("/edit/<int:link_id>", methods=["GET", "POST"])
    def edit_link(link_id):
        """Update an existing link."""

        link = Link.query.get_or_404(link_id)

        if request.method == "POST":

            title = request.form.get("title", "").strip()

            url = request.form.get("url", "").strip()

            category = request.form.get("category", link.category).strip()

            # Validate title and URL
            if not title or not url:
                flash("Title and URL are required.", "danger")

                return render_template(
                    "edit.html",
                    link=link,
                    categories=CATEGORIES,
                )

            # Add https:// if no scheme is provided
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            # Update link
            link.title = title
            link.url = url
            link.category = category

            db.session.commit()

            flash(
                f'"{title}" has been updated successfully!',
                "success",
            )

            return redirect(url_for("index"))

        return render_template("edit.html", link=link, categories=CATEGORIES)

    # ── Delete Link ─────────────────────────────────────────────────────────

    @app.route("/delete/<int:link_id>", methods=["POST"])
    def delete_link(link_id):
        """Delete a link by ID."""

        link = Link.query.get_or_404(link_id)

        title = link.title

        db.session.delete(link)
        db.session.commit()

        flash(f'"{title}" has been deleted.', "info")

        return redirect(url_for("index"))

    return app


# Create Flask application
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
