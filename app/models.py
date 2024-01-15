from datetime import datetime, UTC

from app import db


def utcnow():
    return datetime.now(UTC)


class LinkTag(db.Model):
    __tablename__ = "link_tags"
    timestamp = db.Column(db.DateTime, index=True, default=utcnow)

    link_id = db.Column(db.Integer, db.ForeignKey("links.id"), primary_key=True)
    tag_id = db.Column(db.String(64), db.ForeignKey("tags.id"), primary_key=True)


class Link(db.Model):
    __tablename__ = 'links'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=utcnow)

    url = db.Column(db.String(256), nullable=False)
    domain = db.Column(db.String(128), nullable=False)

    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)

    link_tags = db.relationship("LinkTag",
                                foreign_keys=[LinkTag.link_id],
                                backref=db.backref("link", lazy="joined"),
                                lazy="dynamic",
                                cascade="all, delete-orphan")


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.String(64), primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=utcnow)

    name = db.Column(db.String(64), nullable=False)

    link_tags = db.relationship("LinkTag",
                                foreign_keys=[LinkTag.tag_id],
                                backref=db.backref("tag", lazy="joined"),
                                lazy="dynamic",
                                cascade="all, delete-orphan")
