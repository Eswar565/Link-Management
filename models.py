from datetime import datetime, timezone
import secrets

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(db.Model, UserMixin):
    """Platform user – either an admin or a regular user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'admin' | 'user'
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    links = db.relationship(
        "Link", backref="owner", lazy=True, cascade="all, delete-orphan"
    )

    # ── Password helpers ─────────────────────────────────────────────────────

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # ── Convenience properties ───────────────────────────────────────────────

    @property
    def link_count(self) -> int:
        return len(self.links)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def initials(self) -> str:
        parts = self.name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.name[:2].upper()

    @property
    def teams(self):
        """List of Team objects this user is a member of."""
        return [m.team for m in self.team_memberships if m.team is not None]

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email} [{self.role}]>"


class Team(db.Model):
    """A collaborative workspace where members share links and manage access."""

    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    invite_code = db.Column(
        db.String(32),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: secrets.token_hex(4).upper(),
    )
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_teams")
    memberships = db.relationship(
        "TeamMember", backref="team", lazy=True, cascade="all, delete-orphan"
    )
    links = db.relationship(
        "Link", backref="team", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def member_count(self) -> int:
        return len(self.memberships)

    @property
    def link_count(self) -> int:
        return len(self.links)

    def is_member(self, user_id: int) -> bool:
        return any(m.user_id == user_id for m in self.memberships)

    def get_member(self, user_id: int):
        for m in self.memberships:
            if m.user_id == user_id:
                return m
        return None

    def get_role(self, user_id: int) -> str | None:
        m = self.get_member(user_id)
        return m.role if m else None

    def is_admin_or_owner(self, user_id: int) -> bool:
        role = self.get_role(user_id)
        return role in ("owner", "admin")

    def __repr__(self) -> str:
        return f"<Team {self.id}: {self.name}>"


class TeamMember(db.Model):
    """Membership join record between a User and a Team."""

    __tablename__ = "team_members"
    __table_args__ = (
        db.UniqueConstraint("team_id", "user_id", name="uq_team_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(20), nullable=False, default="member")  # 'owner' | 'admin' | 'member'
    joined_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship to user
    user = db.relationship(
        "User", backref=db.backref("team_memberships", cascade="all, delete-orphan")
    )

    def __repr__(self) -> str:
        return f"<TeamMember user={self.user_id} team={self.team_id} role={self.role}>"


class Link(db.Model):
    """A saved web link belonging to a user (and optionally shared with a team)."""

    __tablename__ = "links"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    category = db.Column(db.String(100), nullable=False, default="Other")
    is_starred = db.Column(db.Boolean, nullable=False, default=False)
    is_pinned  = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @property
    def is_team_link(self) -> bool:
        return self.team_id is not None

    def __repr__(self) -> str:
        return f"<Link {self.id}: {self.title}>"
