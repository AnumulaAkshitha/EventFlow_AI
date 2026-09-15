from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Attendee(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, index=True)

    phone = db.Column(db.String(20), index=True)

    event = db.Column(db.String(100), index=True)

    category = db.Column(db.String(50))

    checkin = db.Column(db.Boolean, default=False, index=True)

    qr_code = db.Column(db.String(200))

    registration_id = db.Column(db.String(20), unique=True)

    checkin_time = db.Column(db.DateTime)

    def __repr__(self):
        return self.name

class Venue(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    location = db.Column(db.String(200))

    capacity = db.Column(db.Integer, nullable=False)

    facilities = db.Column(db.String(500))

    available = db.Column(db.Boolean, default=True)

    event = db.Column(db.String(100))

class Speaker(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True)

    expertise = db.Column(db.String(300))

    experience = db.Column(db.Integer)

    availability = db.Column(db.Boolean, default=True)

    assigned_event = db.Column(db.String(100))

    assigned_session = db.Column(db.String(100))


class Session(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)

    event = db.Column(db.String(100), nullable=False)

    date = db.Column(db.Date, nullable=False)

    start_time = db.Column(db.Time, nullable=False)

    end_time = db.Column(db.Time, nullable=False)

    speaker_id = db.Column(
        db.Integer,
        db.ForeignKey("speaker.id")
    )

    venue_id = db.Column(
        db.Integer,
        db.ForeignKey("venue.id")
    )

    status = db.Column(
        db.String(30),
        default="Scheduled",
        index=True
    )

    def __repr__(self):
       return self.title

    # ==============================
    # MILESTONE 3 - SPONSORSHIP MODEL
    # ==============================

class Sponsor(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    company_name = db.Column(db.String(150), nullable=False)

    contact_person = db.Column(db.String(100))

    email = db.Column(db.String(120))

    phone = db.Column(db.String(20))

    sponsorship_package = db.Column(db.String(50))

    sponsorship_amount = db.Column(db.Float, default=0)

    # Revenue directly attributable to this sponsor's contribution.
    attributable_revenue = db.Column(db.Float, nullable=True)

    payment_status = db.Column(
        db.String(30),
        default="Pending"
    )

    contract_status = db.Column(
        db.String(30),
        default="Pending"
    )

    engagement_score = db.Column(
        db.Float,
        default=0
    )

    event = db.Column(db.String(100))

    status = db.Column(
        db.String(30),
        default="Active"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return self.company_name


# ==============================
# SPONSOR DELIVERABLE MODEL
# ==============================

class SponsorDeliverable(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    sponsor_id = db.Column(
        db.Integer,
        db.ForeignKey("sponsor.id"),
        nullable=False
    )

    deliverable_name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(db.String(500))

    status = db.Column(
        db.String(30),
        default="Pending"
    )

    deadline = db.Column(db.DateTime)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==============================
# MILESTONE 3 - INCIDENT MODEL
# ==============================

class Incident(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.String(1000),
        nullable=False
    )

    category = db.Column(db.String(100))

    severity = db.Column(db.String(30))

    priority = db.Column(db.String(30))

    affected_area = db.Column(db.String(150))

    responsible_team = db.Column(db.String(100))

    recommended_action = db.Column(db.String(500))

    status = db.Column(
        db.String(30),
        default="Open"
    )

    escalation_status = db.Column(
        db.String(30),
        default="Not Escalated"
    )

    reported_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    resolved_at = db.Column(db.DateTime)

    resolution = db.Column(db.String(1000))

    def __repr__(self):
        return self.title


# ==============================
# OPERATIONAL ALERT MODEL
# ==============================

class OperationalAlert(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    message = db.Column(
        db.String(500),
        nullable=False
    )

    alert_type = db.Column(
        db.String(50)
    )

    priority = db.Column(
        db.String(30)
    )

    status = db.Column(
        db.String(30),
        default="Active"
    )

    related_incident_id = db.Column(
        db.Integer,
        db.ForeignKey("incident.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
       return self.message


class OrchestrationRun(db.Model):
    """Audit trail for coordinated multi-agent operational workflows."""

    id = db.Column(db.Integer, primary_key=True)
    trigger = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Completed")
    steps = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)