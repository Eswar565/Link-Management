from datetime import datetime, timezone
from extensions import db


class Link(db.Model):
    """Represents a saved web link in the tracker."""

    __tablename__ = "links"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    category = db.Column(db.String(100), nullable=False, default="General")
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Link {self.id}: {self.title}>"
