from flask import Flask, render_template, request, redirect, url_for, flash
from extensions import db
from models import Link

CATEGORIES = ["Meetings", "YouTube", "Study", "Work", "News", "Tools", "Social", "Other"]


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "smart-link-tracker-secret-key-2024"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///links.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ── Routes ──────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        """Home dashboard – list all links, filterable by category."""
        selected_category = request.args.get("category", "")
        search_query = request.args.get("q", "").strip()

        query = Link.query

        if selected_category:
            query = query.filter_by(category=selected_category)

        if search_query:
            query = query.filter(
                Link.title.ilike(f"%{search_query}%")
                | Link.url.ilike(f"%{search_query}%")
            )

        links = query.order_by(Link.created_at.desc()).all()

        # Count per category for sidebar badges
        category_counts = {
            cat: Link.query.filter_by(category=cat).count() for cat in CATEGORIES
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

    @app.route("/add", methods=["GET", "POST"])
    def add_link():
        """Create a new link."""
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            url = request.form.get("url", "").strip()
            category = request.form.get("category", "Other").strip()

            if not title or not url:
                flash("Title and URL are required.", "danger")
                return render_template("add.html", categories=CATEGORIES)

            # Ensure URL has a scheme
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            new_link = Link(title=title, url=url, category=category)
            db.session.add(new_link)
            db.session.commit()
            flash(f'"{title}" has been added successfully!', "success")
            return redirect(url_for("index"))

        return render_template("add.html", categories=CATEGORIES)

    @app.route("/edit/<int:link_id>", methods=["GET", "POST"])
    def edit_link(link_id):
        """Update an existing link."""
        link = Link.query.get_or_404(link_id)

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            url = request.form.get("url", "").strip()
            category = request.form.get("category", link.category).strip()

            if not title or not url:
                flash("Title and URL are required.", "danger")
                return render_template("edit.html", link=link, categories=CATEGORIES)

            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            link.title = title
            link.url = url
            link.category = category
            db.session.commit()
            flash(f'"{title}" has been updated successfully!', "success")
            return redirect(url_for("index"))

        return render_template("edit.html", link=link, categories=CATEGORIES)

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


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
