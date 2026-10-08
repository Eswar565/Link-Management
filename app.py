"""
LinkVault – Main application factory.
Handles auth, user workspace, and admin panel routes.
"""
import os
import functools

from flask import (
    Flask, render_template, request, redirect, url_for, flash, abort, jsonify,
)
from flask_login import (
    login_user, logout_user, login_required, current_user,
)
from dotenv import load_dotenv

from extensions import db, login_manager
from models import User, Link, Team, TeamMember

# Load .env early so os.getenv works at module level too
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

CATEGORIES = [
    "Meetings", "YouTube", "Study", "Work",
    "News", "Tools", "Social", "Other",
]


# ── Role guard decorator ──────────────────────────────────────────────────────

def admin_required(f):
    """Protect a route so only authenticated admins can access it."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Application factory ───────────────────────────────────────────────────────

def create_app():
    load_dotenv(os.path.join(basedir, ".env"))

    app = Flask(
        __name__,
        template_folder=os.path.join(basedir, "templates"),
        static_folder=os.path.join(basedir, "static"),
    )

    # ── Config ───────────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY", "linkvault-dev-secret-change-in-production"
    )

    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not database_url or not database_url.strip():
        raise RuntimeError(
            "\n" + "=" * 70 + "\n"
            "CRITICAL: DATABASE_URL is missing!\n\n"
            "Local development:\n"
            "  Set DATABASE_URL in your .env file:\n"
            "  DATABASE_URL=postgresql+psycopg://postgres:PASSWORD@localhost:5432/link-management\n\n"
            "Vercel deployment:\n"
            "  Add DATABASE_URL (or connect Vercel Postgres / Neon) in your\n"
            "  Vercel Project Settings > Environment Variables.\n"
            + "=" * 70
        )

    database_url = database_url.strip()
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    # If connecting to remote cloud database without explicit sslmode, ensure SSL is enabled
    if any(h in database_url for h in ("render.com", "neon.tech", "supabase.co")) and "sslmode=" not in database_url:
        sep = "&" if "?" in database_url else "?"
        database_url += f"{sep}sslmode=require"

    # Serverless tuning (Vercel sets VERCEL=1)
    is_serverless = os.getenv("VERCEL") == "1"
    pool_size = 5 if is_serverless else 10
    max_overflow = 10 if is_serverless else 20

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please sign in to access your workspace."
    login_manager.login_message_category = "info"

    # Lazy database initialization helper (handles Render/Neon cold starts)
    db_initialized = False

    def _ensure_db_ready():
        nonlocal db_initialized
        if db_initialized:
            return True
        try:
            db.create_all()
            _migrate_schema()
            _seed_admin()
            db_initialized = True
            app.logger.info("[LinkVault] ✓ Database tables and schema verified.")
            return True
        except Exception as e:
            app.logger.warning(f"[LinkVault] Database setup attempt note: {e}")
            return False

    with app.app_context():
        _ensure_db_ready()

    @app.before_request
    def check_db_ready():
        if not db_initialized:
            _ensure_db_ready()

    # ═══════════════════════════════════════════════════════════════════════════
    # AUTH ROUTES
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Sign-in page with both HTML and AJAX support."""
        if current_user.is_authenticated:
            dest = url_for("admin_dashboard") if current_user.is_admin else url_for("index")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                return jsonify({"success": True, "redirect": dest})
            return redirect(dest)

        if request.method == "POST":
            data = request.get_json(silent=True) or request.form
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            remember = bool(data.get("remember"))

            try:
                if not db_initialized:
                    _ensure_db_ready()
                user = User.query.filter_by(email=email).first()
            except Exception as e:
                app.logger.error(f"[LinkVault Login Error] Database query failed: {e}")
                err_msg = "Database connection error. Please verify your Render DATABASE_URL."
                if is_ajax:
                    return jsonify({"success": False, "error": err_msg}), 500
                flash(err_msg, "danger")
                return render_template("login.html", email=email), 500

            if not user or not user.check_password(password):
                if is_ajax:
                    return jsonify({"success": False, "error": "Invalid email or password. Please try again."}), 400
                flash("Invalid email or password. Please try again.", "danger")
                return render_template("login.html", email=email)

            if not user.is_active:
                msg = "Your account has been deactivated. Contact your administrator."
                if is_ajax:
                    return jsonify({"success": False, "error": msg}), 403
                flash(msg, "danger")
                return render_template("login.html", email=email)

            login_user(user, remember=remember)

            next_page = request.args.get("next")
            dest = next_page or (url_for("admin_dashboard") if user.is_admin else url_for("index"))
            if is_ajax:
                return jsonify({"success": True, "redirect": dest})
            return redirect(dest)

        return render_template("login.html", email="")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been signed out successfully.", "info")
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """Self-service account registration with both HTML and AJAX support."""
        if current_user.is_authenticated:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                return jsonify({"success": True, "redirect": url_for("index")})
            return redirect(url_for("index"))

        if request.method == "POST":
            data = request.get_json(silent=True) or request.form
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
            name     = data.get("name", "").strip()
            email    = data.get("email", "").strip().lower()
            password = data.get("password", "")
            confirm  = data.get("confirm_password", "")

            errors = []
            if not name:
                errors.append("Full name is required.")
            if not email:
                errors.append("Email address is required.")
            if not password:
                errors.append("Password is required.")
            elif len(password) < 8:
                errors.append("Password must be at least 8 characters.")
            elif password != confirm:
                errors.append("Passwords do not match.")
            try:
                if not db_initialized:
                    _ensure_db_ready()
                if email and User.query.filter_by(email=email).first():
                    errors.append("An account with that email already exists.")
            except Exception as e:
                app.logger.error(f"[LinkVault Register Error] Database check failed: {e}")
                err_msg = "Database connection error. Please verify your Render DATABASE_URL."
                if is_ajax:
                    return jsonify({"success": False, "error": err_msg}), 500
                flash(err_msg, "danger")
                return render_template("register.html", form=request.form), 500

            if errors:
                if is_ajax:
                    return jsonify({"success": False, "error": errors[0]}), 400
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "register.html",
                    form=request.form,
                )

            try:
                user = User(name=name, email=email, role="user")
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"[LinkVault Register Error] User commit failed: {e}")
                err_msg = "Database save failed. Please verify your Render database connection."
                if is_ajax:
                    return jsonify({"success": False, "error": err_msg}), 500
                flash(err_msg, "danger")
                return render_template("register.html", form=request.form), 500

            login_user(user)
            flash(f"Welcome to LinkVault, {name}! Your account is ready.", "success")
            if is_ajax:
                return jsonify({"success": True, "redirect": url_for("index")})
            return redirect(url_for("index"))

        return render_template("register.html", form={})

    # ═══════════════════════════════════════════════════════════════════════════
    # USER WORKSPACE ROUTES
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/landing")
    def landing():
        """Public marketing landing page."""
        return render_template("landing.html")

    @app.route("/")
    def index():
        """Public landing page for visitors; personal workspace for authenticated users."""
        if not current_user.is_authenticated:
            return render_template("landing.html")

        selected_category = request.args.get("category", "")
        search_query = request.args.get("q", "").strip()

        # Scope index to personal links (where team_id is None)
        query = Link.query.filter_by(user_id=current_user.id, team_id=None)

        if selected_category:
            query = query.filter_by(category=selected_category)

        if search_query:
            query = query.filter(
                Link.title.ilike(f"%{search_query}%")
                | Link.url.ilike(f"%{search_query}%")
            )

        # Pinned first, then starred, then newest
        all_links = query.order_by(
            Link.is_pinned.desc(),
            Link.is_starred.desc(),
            Link.created_at.desc(),
        ).all()

        pinned_links  = [l for l in all_links if l.is_pinned]
        regular_links = [l for l in all_links if not l.is_pinned]

        category_counts = {
            cat: Link.query.filter_by(
                user_id=current_user.id, team_id=None, category=cat
            ).count()
            for cat in CATEGORIES
        }

        total = Link.query.filter_by(user_id=current_user.id, team_id=None).count()
        user_teams = current_user.teams

        return render_template(
            "index.html",
            links=regular_links,
            pinned_links=pinned_links,
            categories=CATEGORIES,
            category_counts=category_counts,
            selected_category=selected_category,
            search_query=search_query,
            total=total,
            user_teams=user_teams,
        )

    @app.route("/add", methods=["GET", "POST"])
    @login_required
    def add_link():
        """Create a new link for the user's personal collection or a shared team."""
        user_teams = current_user.teams
        preselect_team = request.args.get("team_id", "")

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            url = request.form.get("url", "").strip()
            category = request.form.get("category", "Other").strip()
            team_id_raw = request.form.get("team_id", "personal").strip()

            if not title or not url:
                flash("Title and URL are required.", "danger")
                return render_template(
                    "add.html",
                    categories=CATEGORIES,
                    user_teams=user_teams,
                    preselect_team=preselect_team,
                )

            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            target_team_id = None
            target_team = None
            if team_id_raw and team_id_raw != "personal":
                try:
                    t_id = int(team_id_raw)
                    t = db.session.get(Team, t_id)
                    if t and (current_user.is_admin or t.is_member(current_user.id)):
                        target_team_id = t.id
                        target_team = t
                except ValueError:
                    pass

            new_link = Link(
                title=title,
                url=url,
                category=category,
                user_id=current_user.id,
                team_id=target_team_id,
            )
            db.session.add(new_link)
            db.session.commit()

            if target_team:
                flash(f'"{title}" has been shared with team "{target_team.name}".', "success")
                return redirect(url_for("team_workspace", team_id=target_team.id))

            flash(f'"{title}" has been saved to your collection.', "success")
            return redirect(url_for("index"))

        return render_template(
            "add.html",
            categories=CATEGORIES,
            user_teams=user_teams,
            preselect_team=preselect_team,
        )

    @app.route("/edit/<int:link_id>", methods=["GET", "POST"])
    @login_required
    def edit_link(link_id):
        """Edit an existing link (personal or team-shared)."""
        link = db.get_or_404(Link, link_id)
        user_teams = current_user.teams

        # Authorization: creator, team admin/owner, or platform admin
        is_authorized = (
            link.user_id == current_user.id
            or current_user.is_admin
            or (link.team and link.team.is_admin_or_owner(current_user.id))
        )
        if not is_authorized:
            abort(403)

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            url = request.form.get("url", "").strip()
            category = request.form.get("category", link.category).strip()
            team_id_raw = request.form.get("team_id", "personal").strip()

            if not title or not url:
                flash("Title and URL are required.", "danger")
                return render_template(
                    "edit.html",
                    link=link,
                    categories=CATEGORIES,
                    user_teams=user_teams,
                )

            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            target_team_id = None
            if team_id_raw and team_id_raw != "personal":
                try:
                    t_id = int(team_id_raw)
                    t = db.session.get(Team, t_id)
                    if t and (current_user.is_admin or t.is_member(current_user.id)):
                        target_team_id = t.id
                except ValueError:
                    pass

            link.title = title
            link.url = url
            link.category = category
            link.team_id = target_team_id
            db.session.commit()

            flash(f'"{title}" has been updated.', "success")
            if link.team_id:
                return redirect(url_for("team_workspace", team_id=link.team_id))
            return redirect(url_for("index"))

        return render_template(
            "edit.html",
            link=link,
            categories=CATEGORIES,
            user_teams=user_teams,
        )

    @app.route("/delete/<int:link_id>", methods=["POST"])
    @login_required
    def delete_link(link_id):
        """Delete a link."""
        link = db.get_or_404(Link, link_id)

        is_authorized = (
            link.user_id == current_user.id
            or current_user.is_admin
            or (link.team and link.team.is_admin_or_owner(current_user.id))
        )
        if not is_authorized:
            abort(403)

        title = link.title
        dest = url_for("team_workspace", team_id=link.team_id) if link.team_id else url_for("index")
        db.session.delete(link)
        db.session.commit()

        flash(f'"{title}" has been removed.', "info")
        return redirect(dest)

    @app.route("/star/<int:link_id>", methods=["POST"])
    @login_required
    def toggle_star(link_id):
        """Toggle starred state; returns JSON for AJAX callers."""
        from flask import jsonify
        link = db.get_or_404(Link, link_id)
        is_authorized = (
            link.user_id == current_user.id
            or current_user.is_admin
            or (link.team and link.team.is_member(current_user.id))
        )
        if not is_authorized:
            abort(403)
        link.is_starred = not link.is_starred
        db.session.commit()
        return jsonify({"starred": link.is_starred, "link_id": link_id})

    @app.route("/pin/<int:link_id>", methods=["POST"])
    @login_required
    def toggle_pin(link_id):
        """Toggle pinned state; returns JSON for AJAX callers."""
        from flask import jsonify
        link = db.get_or_404(Link, link_id)
        is_authorized = (
            link.user_id == current_user.id
            or current_user.is_admin
            or (link.team and link.team.is_member(current_user.id))
        )
        if not is_authorized:
            abort(403)
        link.is_pinned = not link.is_pinned
        db.session.commit()
        return jsonify({"pinned": link.is_pinned, "link_id": link_id})

    # ═══════════════════════════════════════════════════════════════════════════
    # TEAM MANAGEMENT ROUTES
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/teams")
    @login_required
    def teams_list():
        """List all teams the current user belongs to."""
        teams = current_user.teams
        return render_template("teams/index.html", teams=teams)

    @app.route("/teams/new", methods=["POST"])
    @login_required
    def create_team():
        """Create a new team and make current_user the owner."""
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Team name is required.", "danger")
            return redirect(url_for("teams_list"))

        team = Team(
            name=name,
            description=description,
            created_by=current_user.id,
        )
        db.session.add(team)
        db.session.flush()

        member = TeamMember(
            team_id=team.id,
            user_id=current_user.id,
            role="owner",
        )
        db.session.add(member)
        db.session.commit()

        flash(f'Team "{name}" created successfully! Invite your teammates with code {team.invite_code}.', "success")
        return redirect(url_for("team_workspace", team_id=team.id))

    @app.route("/teams/join", methods=["POST"])
    @login_required
    def join_team():
        """Join a team by entering its invite code."""
        code = request.form.get("invite_code", "").strip().upper()

        if not code:
            flash("Invite code is required.", "danger")
            return redirect(url_for("teams_list"))

        team = Team.query.filter_by(invite_code=code).first()
        if not team:
            flash(f'Invalid invite code "{code}". Please verify with your team administrator.', "danger")
            return redirect(url_for("teams_list"))

        if team.is_member(current_user.id):
            flash(f'You are already a member of "{team.name}".', "info")
            return redirect(url_for("team_workspace", team_id=team.id))

        member = TeamMember(
            team_id=team.id,
            user_id=current_user.id,
            role="member",
        )
        db.session.add(member)
        db.session.commit()

        flash(f'Welcome to "{team.name}"! You now have access to all team links and members.', "success")
        return redirect(url_for("team_workspace", team_id=team.id))

    @app.route("/teams/<int:team_id>")
    @login_required
    def team_workspace(team_id):
        """Team workspace: view all shared links and all team members."""
        team = db.get_or_404(Team, team_id)

        if not current_user.is_admin and not team.is_member(current_user.id):
            abort(403)

        selected_category = request.args.get("category", "")
        search_query = request.args.get("q", "").strip()
        active_tab = request.args.get("tab", "links")

        query = Link.query.filter_by(team_id=team.id)

        if selected_category:
            query = query.filter_by(category=selected_category)

        if search_query:
            query = query.filter(
                Link.title.ilike(f"%{search_query}%")
                | Link.url.ilike(f"%{search_query}%")
            )

        team_links = query.order_by(
            Link.is_pinned.desc(),
            Link.is_starred.desc(),
            Link.created_at.desc(),
        ).all()

        category_counts = {
            cat: Link.query.filter_by(team_id=team.id, category=cat).count()
            for cat in CATEGORIES
        }
        total_links = Link.query.filter_by(team_id=team.id).count()

        members = sorted(
            team.memberships,
            key=lambda m: (0 if m.role == "owner" else (1 if m.role == "admin" else 2), m.joined_at)
        )

        user_role = team.get_role(current_user.id) or ("admin" if current_user.is_admin else "viewer")
        can_manage = current_user.is_admin or user_role in ("owner", "admin")

        return render_template(
            "teams/workspace.html",
            team=team,
            links=team_links,
            members=members,
            categories=CATEGORIES,
            category_counts=category_counts,
            selected_category=selected_category,
            search_query=search_query,
            active_tab=active_tab,
            user_role=user_role,
            can_manage=can_manage,
            total_links=total_links,
        )

    @app.route("/teams/<int:team_id>/add-member", methods=["POST"])
    @login_required
    def add_team_member(team_id):
        """Add an existing registered user to the team by their email."""
        team = db.get_or_404(Team, team_id)

        if not current_user.is_admin and not team.is_admin_or_owner(current_user.id):
            abort(403)

        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "member").strip()
        if role not in ("admin", "member"):
            role = "member"

        if not email:
            flash("User email address is required.", "danger")
            return redirect(url_for("team_workspace", team_id=team.id, tab="members"))

        target_user = User.query.filter_by(email=email).first()
        if not target_user:
            flash(
                f'No registered user found with email "{email}". Ask them to create an account first, or share Invite Code: {team.invite_code}',
                "danger",
            )
            return redirect(url_for("team_workspace", team_id=team.id, tab="members"))

        if team.is_member(target_user.id):
            flash(f'"{target_user.name}" ({email}) is already a member of this team.', "info")
            return redirect(url_for("team_workspace", team_id=team.id, tab="members"))

        new_member = TeamMember(
            team_id=team.id,
            user_id=target_user.id,
            role=role,
        )
        db.session.add(new_member)
        db.session.commit()

        flash(f'"{target_user.name}" ({email}) has been added to {team.name} as {role.capitalize()}!', "success")
        return redirect(url_for("team_workspace", team_id=team.id, tab="members"))

    @app.route("/teams/<int:team_id>/members/<int:user_id>/role", methods=["POST"])
    @login_required
    def update_member_role(team_id, user_id):
        """Update a member's role (owner or admin only)."""
        team = db.get_or_404(Team, team_id)

        if not current_user.is_admin and not team.is_admin_or_owner(current_user.id):
            abort(403)

        member = TeamMember.query.filter_by(team_id=team.id, user_id=user_id).first_or_404()
        if member.user_id == team.created_by:
            flash("Cannot modify the team owner's role.", "danger")
            return redirect(url_for("team_workspace", team_id=team.id, tab="members"))

        new_role = request.form.get("role", "member").strip()
        if new_role in ("admin", "member"):
            member.role = new_role
            db.session.commit()
            flash(f'Role for "{member.user.name}" updated to {new_role.capitalize()}.', "success")

        return redirect(url_for("team_workspace", team_id=team.id, tab="members"))

    @app.route("/teams/<int:team_id>/members/<int:user_id>/remove", methods=["POST"])
    @login_required
    def remove_member(team_id, user_id):
        """Remove a member from the team."""
        team = db.get_or_404(Team, team_id)

        if not current_user.is_admin and not team.is_admin_or_owner(current_user.id):
            abort(403)

        member = TeamMember.query.filter_by(team_id=team.id, user_id=user_id).first_or_404()
        if member.user_id == team.created_by:
            flash("The team owner cannot be removed.", "danger")
            return redirect(url_for("team_workspace", team_id=team.id, tab="members"))

        user_name = member.user.name
        db.session.delete(member)
        db.session.commit()

        flash(f'"{user_name}" was removed from {team.name}.', "info")
        return redirect(url_for("team_workspace", team_id=team.id, tab="members"))

    @app.route("/teams/<int:team_id>/leave", methods=["POST"])
    @login_required
    def leave_team(team_id):
        """Allow a member to leave a team."""
        team = db.get_or_404(Team, team_id)
        member = TeamMember.query.filter_by(team_id=team.id, user_id=current_user.id).first_or_404()

        if member.role == "owner":
            flash("Team owners cannot leave their team. Please delete the team or transfer ownership.", "danger")
            return redirect(url_for("team_workspace", team_id=team.id))

        db.session.delete(member)
        db.session.commit()

        flash(f'You have left "{team.name}".', "info")
        return redirect(url_for("teams_list"))

    @app.route("/teams/<int:team_id>/delete", methods=["POST"])
    @login_required
    def delete_team(team_id):
        """Delete a team and its shared links (owner only)."""
        team = db.get_or_404(Team, team_id)

        if not current_user.is_admin and team.created_by != current_user.id:
            abort(403)

        name = team.name
        db.session.delete(team)
        db.session.commit()

        flash(f'Team "{name}" and all its shared links have been deleted.', "info")
        return redirect(url_for("teams_list"))

    # ═══════════════════════════════════════════════════════════════════════════
    # ADMIN ROUTES
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        """Admin overview: stats, recent activity."""
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True, role="user").count()
        total_links = Link.query.count()
        admin_count = User.query.filter_by(role="admin").count()
        total_teams = Team.query.count()

        # Per-category totals
        cat_stats = {
            cat: Link.query.filter_by(category=cat).count()
            for cat in CATEGORIES
        }

        recent_users = (
            User.query.order_by(User.created_at.desc()).limit(6).all()
        )
        recent_links = (
            Link.query
            .join(User)
            .order_by(Link.created_at.desc())
            .limit(6)
            .all()
        )

        return render_template(
            "admin/dashboard.html",
            total_users=total_users,
            active_users=active_users,
            total_links=total_links,
            admin_count=admin_count,
            total_teams=total_teams,
            cat_stats=cat_stats,
            recent_users=recent_users,
            recent_links=recent_links,
        )

    @app.route("/admin/users")
    @admin_required
    def admin_users():
        """List all users with search and role filter."""
        search = request.args.get("q", "").strip()
        role_filter = request.args.get("role", "")

        query = User.query
        if search:
            query = query.filter(
                User.name.ilike(f"%{search}%")
                | User.email.ilike(f"%{search}%")
            )
        if role_filter:
            query = query.filter_by(role=role_filter)

        users = query.order_by(User.created_at.desc()).all()

        return render_template(
            "admin/users.html",
            users=users, search=search, role_filter=role_filter,
        )

    @app.route("/admin/users/new", methods=["GET", "POST"])
    @admin_required
    def admin_create_user():
        """Create a new user account."""
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role", "user")

            errors = []
            if not name:
                errors.append("Full name is required.")
            if not email:
                errors.append("Email address is required.")
            if not password:
                errors.append("Password is required.")
            elif len(password) < 8:
                errors.append("Password must be at least 8 characters.")
            if User.query.filter_by(email=email).first():
                errors.append(f"An account with email '{email}' already exists.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "admin/user_form.html",
                    action="create", form=request.form,
                )

            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash(
                f'Account for "{name}" ({email}) created successfully. '
                f"They can now sign in.",
                "success",
            )
            return redirect(url_for("admin_users"))

        return render_template(
            "admin/user_form.html", action="create", form={},
        )

    @app.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
    @admin_required
    def admin_edit_user(user_id):
        """Edit an existing user account."""
        user = db.get_or_404(User, user_id)

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            role = request.form.get("role", user.role)
            new_password = request.form.get("password", "").strip()

            errors = []
            if not name:
                errors.append("Full name is required.")
            if not email:
                errors.append("Email is required.")
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user_id:
                errors.append("That email is already used by another account.")
            if new_password and len(new_password) < 8:
                errors.append("New password must be at least 8 characters.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "admin/user_form.html",
                    action="edit", user=user, form=request.form,
                )

            user.name = name
            user.email = email
            user.role = role
            if new_password:
                user.set_password(new_password)

            db.session.commit()
            flash(f'User "{name}" updated successfully.', "success")
            return redirect(url_for("admin_users"))

        return render_template(
            "admin/user_form.html", action="edit", user=user, form={},
        )

    @app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
    @admin_required
    def admin_toggle_user(user_id):
        """Activate or deactivate a user account."""
        user = db.get_or_404(User, user_id)
        if user.id == current_user.id:
            flash("You cannot deactivate your own account.", "danger")
            return redirect(url_for("admin_users"))

        user.is_active = not user.is_active
        db.session.commit()
        state = "activated" if user.is_active else "deactivated"
        flash(f'"{user.name}" has been {state}.', "success")
        return redirect(url_for("admin_users"))

    @app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
    @admin_required
    def admin_delete_user(user_id):
        """Permanently delete a user and all their links."""
        user = db.get_or_404(User, user_id)
        if user.id == current_user.id:
            flash("You cannot delete your own account.", "danger")
            return redirect(url_for("admin_users"))

        name = user.name
        db.session.delete(user)
        db.session.commit()
        flash(
            f'User "{name}" and all their data have been permanently deleted.',
            "info",
        )
        return redirect(url_for("admin_users"))

    @app.route("/admin/links")
    @admin_required
    def admin_links():
        """View all links across all users."""
        search = request.args.get("q", "").strip()
        cat_filter = request.args.get("category", "")
        user_filter = request.args.get("user_id", "")

        query = Link.query.join(User)

        if search:
            query = query.filter(
                Link.title.ilike(f"%{search}%")
                | Link.url.ilike(f"%{search}%")
            )
        if cat_filter:
            query = query.filter(Link.category == cat_filter)
        if user_filter:
            query = query.filter(Link.user_id == int(user_filter))

        links = query.order_by(Link.created_at.desc()).all()
        all_users = User.query.filter_by(role="user").order_by(User.name).all()

        return render_template(
            "admin/links.html",
            links=links,
            all_users=all_users,
            categories=CATEGORIES,
            search=search,
            cat_filter=cat_filter,
            user_filter=user_filter,
        )

    # ── Error handlers ────────────────────────────────────────────────────────

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"[LinkVault Error 500] {e}")
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
        if is_ajax:
            return jsonify({
                "success": False,
                "error": "Internal server error. Please verify your Render database connection."
            }), 500
        return render_template("errors/403.html"), 500

    return app

# ── Schema migrations ─────────────────────────────────────────────────────────

def _migrate_schema():
    """Safely add new columns to existing tables (idempotent)."""
    from sqlalchemy import text
    stmts = [
        "ALTER TABLE links ADD COLUMN IF NOT EXISTS is_starred BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE links ADD COLUMN IF NOT EXISTS is_pinned  BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE links ADD COLUMN IF NOT EXISTS team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE",
    ]
    with db.engine.connect() as conn:
        for stmt in stmts:
            conn.execute(text(stmt))
        conn.commit()


# ── Admin seed ────────────────────────────────────────────────────────────────

def _seed_admin():
    """Create the default admin account on first boot if none exists."""
    from sqlalchemy.exc import IntegrityError

    if User.query.filter_by(role="admin").first():
        return

    admin_email = os.getenv("ADMIN_EMAIL", "admin@linkvault.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123456")
    admin_name = os.getenv("ADMIN_NAME", "Platform Admin")

    admin = User(name=admin_name, email=admin_email, role="admin")
    admin.set_password(admin_password)

    try:
        db.session.add(admin)
        db.session.commit()
        print(f"[LinkVault] ✓ Default admin seeded → {admin_email}")
        print(f"[LinkVault]   Password: {admin_password}")
        print(f"[LinkVault]   Set ADMIN_EMAIL / ADMIN_PASSWORD in your .env to change.")
    except IntegrityError:
        db.session.rollback()
        print(f"[LinkVault] Admin already exists – seed skipped.")



# ── WSGI entry point ──────────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
