import csv
import io
import os
import csv
from dotenv import load_dotenv

load_dotenv()

from flask import Response
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import text
from config import Config
from services.analytics_agent import AnalyticsAgent
from services.venue_agent import VenueAgent
from services.analytics_agent import AnalyticsAgent
from services.scheduling_agent import SchedulingAgent
from services.speaker_agent import SpeakerAgent
from services.email_service import EmailService
from services.intelligence_engine import EventIntelligenceEngine
from services.orchestrator import AgentOrchestrator
from services.platform_ops_service import PlatformOperationsService

from models import (
    db,
    Attendee,
    Venue,
    Speaker,
    Session,
    Sponsor,
    SponsorDeliverable,
    Incident,
    OperationalAlert,
    OrchestrationRun
)
from services.sponsorship_agent import sponsorship_agent
from services.registration_agent import RegistrationAgent
from utils.qr_generator import generate_qr
registration_agent = RegistrationAgent()
email_service = EmailService()
speaker_agent = SpeakerAgent()
scheduling_agent = SchedulingAgent()
analytics_agent = AnalyticsAgent()
venue_agent = VenueAgent()
intelligence_engine = EventIntelligenceEngine()
orchestrator = AgentOrchestrator(intelligence_engine)

app = Flask(__name__)
app.config.from_object(Config)


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response

db.init_app(app)
platform_ops_service = PlatformOperationsService(app)

with app.app_context():
    db.create_all()


# ===========================
# Dashboard
# ===========================
@app.route("/")
def home():

    total_attendees = Attendee.query.count()

    checked_in = Attendee.query.filter_by(checkin=True).count()

    pending = total_attendees - checked_in

    expected_attendance = round(total_attendees * 0.90)

    students = Attendee.query.filter_by(category="Student").count()
    professionals = Attendee.query.filter_by(category="Professional").count()
    speakers = Attendee.query.filter_by(category="Speaker").count()

    ai = Attendee.query.filter_by(event="AI Workshop").count()
    hackathon = Attendee.query.filter_by(event="Hackathon").count()
    cloud = Attendee.query.filter_by(event="Cloud Summit").count()

    events = {
        "AI Workshop": ai,
        "Hackathon": hackathon,
        "Cloud Summit": cloud
    }

    trending_event = max(events, key=events.get)

    categories = {
        "Students": students,
        "Professionals": professionals,
        "Speakers": speakers
    }

    majority_category = max(categories, key=categories.get)

    if total_attendees <= 50:
        venue = "Seminar Hall"
    elif total_attendees <= 150:
        venue = "Conference Hall"
    else:
        venue = "Main Auditorium"

    volunteers = max(2, total_attendees // 25 + 1)

    if checked_in >= total_attendees * 0.8 and total_attendees > 0:
        crowd = "High"
    elif checked_in >= total_attendees * 0.5:
        crowd = "Moderate"
    else:
        crowd = "Low"

    confidence = min(95, 80 + total_attendees)

    recent_attendees = Attendee.query.order_by(Attendee.id.desc()).limit(5).all()

    intelligence = orchestrator.run()

    return render_template(
        "index.html",
        total_attendees=total_attendees,
        checked_in=checked_in,
        pending=pending,
        expected_attendance=expected_attendance,
        trending_event=trending_event,
        majority_category=majority_category,
        venue=venue,
        volunteers=volunteers,
        crowd=crowd,
        confidence=confidence,
        recent_attendees=recent_attendees,
        intelligence=intelligence
    )


@app.route("/executive-dashboard")
def executive_dashboard():
    return render_template("executive_dashboard.html", intelligence=orchestrator.run())


@app.route("/intelligence")
def intelligence():
    return render_template("intelligence.html", intelligence=orchestrator.run())


@app.route("/agents")
def agents():
    intelligence = orchestrator.run()
    registry = [
        {"name": "Registration Agent", "domain": "Attendees", "records": Attendee.query.count(), "role": "Validates and deduplicates registrations"},
        {"name": "Speaker Agent", "domain": "Speakers", "records": Speaker.query.count(), "role": "Matches speakers to session topics"},
        {"name": "Venue Agent", "domain": "Venues", "records": Venue.query.count(), "role": "Optimizes capacity and facilities"},
        {"name": "Scheduling Agent", "domain": "Sessions", "records": Session.query.count(), "role": "Detects speaker and venue conflicts"},
        {"name": "Analytics Agent", "domain": "Event data", "records": sum(int(value) for value in intelligence["events"].values()), "role": "Produces trends and performance insights"},
        {"name": "Sponsorship Agent", "domain": "Sponsors", "records": Sponsor.query.count(), "role": "Monitors sponsor commitments and risk"},
        {"name": "Incident Agent", "domain": "Operations", "records": Incident.query.count(), "role": "Prioritizes incidents and escalates risk"},
    ]
    orchestration_sessions = Session.query.filter_by(status="Scheduled").order_by(Session.date.asc(), Session.start_time.asc()).all()
    return render_template("agents.html", intelligence=intelligence, registry=registry, orchestration_sessions=orchestration_sessions)


@app.route("/platform-ops")
def platform_ops():
    checks = platform_ops_service.run_checks()
    sections = platform_ops_service.section_status()
    return render_template("platform_ops.html", checks=checks, sections=sections, intelligence=orchestrator.run())


@app.route("/api/platform-ops/checks")
def platform_ops_checks():
    checks = platform_ops_service.run_checks()
    return {"checks": checks, "generated_at": datetime.now().astimezone().isoformat(timespec="seconds")}


@app.route("/api/platform-ops/sections")
def platform_ops_sections():
    return {"sections": platform_ops_service.section_status(), "generated_at": datetime.now().astimezone().isoformat(timespec="seconds")}


@app.route("/api/orchestration/trigger", methods=["POST"])
def trigger_orchestration():
    payload = request.get_json(silent=True) or {}
    try:
        return orchestrator.process_event(payload.get("event_type"), payload), 201
    except ValueError as error:
        return {"status": "rejected", "error": str(error)}, 400


@app.route("/api/orchestration/runs")
def orchestration_runs():
    runs = OrchestrationRun.query.order_by(OrchestrationRun.created_at.desc()).limit(10).all()
    return {"runs": [{"id": run.id, "trigger": run.trigger, "status": run.status, "steps": run.steps, "created_at": run.created_at.isoformat() + "Z"} for run in runs]}


@app.route("/api/intelligence")
def intelligence_api():
    persist_alerts = request.args.get("persist", "0") == "1"
    return orchestrator.run(persist_alerts=persist_alerts)


@app.route("/api/live")
def live_updates():
    """Return the current dashboard snapshot and active alerts for polling clients."""
    return {"intelligence": orchestrator.run(), "server_time": datetime.now().astimezone().isoformat(timespec="seconds")}


@app.route("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return {"status": "ok", "service": "eventflow-ai", "database": db.engine.url.get_backend_name()}
    except Exception:
        db.session.rollback()
        return {"status": "degraded", "service": "eventflow-ai", "database": "unavailable"}, 503
# ===========================
# Register Attendee
# ===========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # Get form data
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["phone"].strip()
        event = request.form["event"]
        category = request.form["category"]


        # ===========================
        # Registration Agent
        # ===========================

        agent_result = registration_agent.process_registration(
            name=name,
            email=email,
            phone=phone,
            event=event,
            category=category
        )

        # Stop registration if validation fails
        if not agent_result["success"]:

            return render_template(
                "register.html",
                error=" ".join(agent_result["errors"])
            )
        

        

        # Create Attendee
        attendee = Attendee(
            name=name,
            email=email,
            phone=phone,
            event=event,
            category=category
        )

        db.session.add(attendee)
        db.session.commit()

        # Generate Registration ID
        registration_id = f"EVT{attendee.id:05d}"
        attendee.registration_id = registration_id

        # Generate QR Code
        qr_path = generate_qr(registration_id)

        # Save QR Path
        attendee.qr_code = qr_path

        db.session.commit()


        # ===========================
        # Send Confirmation Email
        # ===========================

        email_result = email_service.send_registration_confirmation(
            attendee=attendee,
            registration_id=registration_id,
            qr_path=qr_path
        )

        if not email_result["success"]:

            print(
                 "Email notification failed:",
                  email_result["message"]
            )

        return render_template(
            "success.html",
            attendee=attendee,
            registration_id=registration_id
        )

    return render_template("register.html")



@app.route("/attendees")
def attendees():

    attendees = Attendee.query.all()

    return render_template(
        "attendees.html",
        attendees=attendees
    )




# ===========================
# Edit Attendee
# ===========================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    attendee = Attendee.query.get_or_404(id)

    if request.method == "POST":

        attendee.name = request.form["name"]
        attendee.email = request.form["email"]
        attendee.phone = request.form["phone"]
        attendee.event = request.form["event"]
        attendee.category = request.form["category"]

        db.session.commit()

        return redirect(url_for("attendees"))

    return render_template(
        "edit.html",
        attendee=attendee
    )


# ===========================
# Delete Attendee
# ===========================
@app.route("/delete/<int:id>")
def delete(id):

    attendee = Attendee.query.get_or_404(id)

    db.session.delete(attendee)
    db.session.commit()

    return redirect(url_for("attendees"))



# ===========================
# Speakers
# ===========================
# ===========================
# Speaker Management
# ===========================

@app.route("/speakers", methods=["GET", "POST"])
def speakers():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        expertise = request.form["expertise"].strip()
        experience = int(request.form["experience"])

        availability = request.form.get(
            "availability"
        ) == "1"

        speaker = Speaker(
            name=name,
            email=email,
            expertise=expertise,
            experience=experience,
            availability=availability
        )

        db.session.add(speaker)
        db.session.commit()

        return redirect(url_for("speakers"))

    speakers = Speaker.query.order_by(
        Speaker.id.desc()
    ).all()

    return render_template(
        "speakers.html",
        speakers=speakers
    )


# ===========================
# AI Speaker Recommendation
# ===========================

@app.route("/recommend-speaker", methods=["POST"])
def recommend_speaker():

    topic = request.form.get(
        "topic",
        ""
    ).strip()

    required_experience = int(
        request.form.get(
            "experience",
            0
        )
    )

    speakers = Speaker.query.order_by(
        Speaker.name.asc()
    ).all()

    recommendations = speaker_agent.recommend(
        speakers=speakers,
        topic=topic,
        required_experience=required_experience
    )

    return render_template(
        "speakers.html",
        speakers=speakers,
        recommendations=recommendations.get(
            "recommendations",
            []
        ),
        recommendation=recommendations.get(
            "recommendation"
        ),
        speaker_result=recommendations,
        topic=topic
    )

# ===========================
# Sessions
# ===========================
# ===========================
# Session Scheduling
# ===========================

@app.route("/sessions", methods=["GET", "POST"])
def sessions():

    scheduling_result = None

    speakers = Speaker.query.order_by(
        Speaker.name.asc()
    ).all()

    venues = Venue.query.order_by(
        Venue.name.asc()
    ).all()

    if request.method == "POST":

        title = request.form["title"].strip()

        event = request.form["event"]

        session_date = datetime.strptime(
            request.form["date"],
            "%Y-%m-%d"
        ).date()

        start_time = datetime.strptime(
            request.form["start_time"],
            "%H:%M"
        ).time()

        end_time = datetime.strptime(
            request.form["end_time"],
            "%H:%M"
        ).time()

        speaker_id = int(
            request.form["speaker_id"]
        )

        venue_id = int(
            request.form["venue_id"]
        )

        # --------------------------------
        # AI Scheduling Agent
        # --------------------------------

        scheduling_result = scheduling_agent.check_schedule(
            date=session_date,
            start_time=start_time,
            end_time=end_time,
            speaker_id=speaker_id,
            venue_id=venue_id
        )

        # --------------------------------
        # Save only if schedule is valid
        # --------------------------------

        if scheduling_result["success"]:

            new_session = Session(

                title=title,

                event=event,

                date=session_date,

                start_time=start_time,

                end_time=end_time,

                speaker_id=speaker_id,

                venue_id=venue_id,

                status="Scheduled"
            )

            db.session.add(new_session)

            db.session.commit()

    session_list = Session.query.order_by(
        Session.date.asc(),
        Session.start_time.asc()
    ).all()

    return render_template(
        "sessions.html",

        speakers=speakers,

        venues=venues,

        sessions=session_list,

        scheduling_result=scheduling_result
    )

# ===========================
# Check-In
# ===========================
from datetime import datetime

@app.route("/checkin", methods=["GET", "POST"])
def checkin():

    message = ""
    attendee = None
    status = ""

    if request.method == "POST":

        registration_id = request.form["registration_id"].strip().upper()

        try:

            attendee_id = int(
                registration_id.replace("EVT", "")
            )

            attendee = Attendee.query.get(attendee_id)

            if attendee:

                if attendee.checkin:

                    status = "already_checked"
                    message = "Attendee has already checked in."

                else:

                    attendee.checkin = True
                    attendee.checkin_time = datetime.now()

                    db.session.commit()

                    status = "success"
                    message = "Check-in successful."

            else:

                status = "not_found"
                message = "Attendee not found."

        except (ValueError, TypeError):

            status = "invalid"
            message = "Invalid Registration ID."

    return render_template(
        "checkin.html",
        message=message,
        attendee=attendee,
        status=status
    )
# ===========================
# Analytics
# ===========================
@app.route("/analytics")
def analytics():

    insights = analytics_agent.generate_insights()

    return render_template(
        "analytics.html",
        insights=insights
    )


@app.route("/import", methods=["GET", "POST"])
def import_csv():

    if request.method == "POST":

        file = request.files["file"]

        if file:

            stream = io.StringIO(
                file.stream.read().decode("UTF8"),
                newline=None
            )

            csv_input = csv.DictReader(stream)

            imported = 0
            skipped = 0

            for row in csv_input:

                name = row["Name"].strip()
                email = row["Email"].strip().lower()
                phone = row["Phone"].strip()
                event = row["Event"].strip()
                category = row["Category"].strip()

                # Skip duplicate email
                existing_email = Attendee.query.filter_by(email=email).first()

                # Skip duplicate phone
                existing_phone = Attendee.query.filter_by(phone=phone).first()

                if existing_email or existing_phone:
                    skipped += 1
                    continue

                attendee = Attendee(
                    name=name,
                    email=email,
                    phone=phone,
                    event=event,
                    category=category
                )

                db.session.add(attendee)
                db.session.commit()

                # Generate Registration ID
                registration_id = f"EVT{attendee.id:05d}"
                attendee.registration_id = registration_id

                # Generate QR Code
                attendee.qr_code = generate_qr(registration_id)

                db.session.commit()

                imported += 1

            return render_template(
                "import.html",
                success=f"{imported} attendees imported successfully.",
                skipped=f"{skipped} duplicate records were skipped."
            )

    return render_template("import.html")
# ===========================
# AI Insights
# ===========================
# ===========================
# AI Insights
# ===========================

@app.route("/ai")
def ai():

    # Generate AI analytics
    analytics_agent = AnalyticsAgent()

    insights = analytics_agent.generate_insights()

    return render_template(
        "ai_insights.html",

        # Attendee Analytics
        total=insights["total_attendees"],
        checked_in=insights["checked_in"],
        pending=insights["pending"],
        attendance_rate=insights["attendance_rate"],

        # Event Analytics
        events=insights["events"],
        trending_event=insights["popular_event"],

        # Category Analytics
        categories=insights["categories"],
        majority_category=insights["majority_category"],

        # Venue Analytics
        total_venues=insights["total_venues"],
        available_venues=insights["available_venues"],
        occupied_venues=insights["occupied_venues"],
        venue_availability=insights["venue_availability"],

        # Speaker Analytics
        total_speakers=insights["total_speakers"],
        available_speakers=insights["available_speakers"],
        unavailable_speakers=insights["unavailable_speakers"],
        speaker_performance=insights["speaker_performance"],

        # Session Analytics
        total_sessions=insights["total_sessions"],
        scheduled_sessions=insights["scheduled_sessions"],
        cancelled_sessions=insights["cancelled_sessions"],
        scheduled_session_rate=insights["scheduled_session_rate"],
        session_popularity=insights["session_popularity"],
        most_popular_session=insights["most_popular_session"],

        # Venue Utilization
        venue_utilization=insights["venue_utilization"],

        # AI Recommendations
        recommendations=insights["recommendations"]
    )

from flask import Response
import csv

class Echo:
    def write(self, value):
        return value


@app.route("/export")
def export():

    attendees = Attendee.query.all()

    def generate():
        data = csv.writer(Echo())

        yield data.writerow([
            "ID",
            "Name",
            "Email",
            "Phone",
            "Event",
            "Category",
            "Checked In"
        ])

        for attendee in attendees:
            yield data.writerow([
                attendee.id,
                attendee.name,
                attendee.email,
                attendee.phone,
                attendee.event,
                attendee.category,
                attendee.checkin
            ])

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=attendees.csv"
        }
    )


# ===========================
# Venue Management
# ===========================

@app.route("/venues")
def venues():

    all_venues = Venue.query.order_by(Venue.id.desc()).all()

    return render_template(
        "venues.html",
        venues=all_venues,
        recommendation=None
    )


@app.route("/add-venue", methods=["POST"])
def add_venue():

    name = request.form["name"].strip()
    location = request.form["location"].strip()
    capacity = int(request.form["capacity"])
    facilities = request.form["facilities"].strip()

    venue = Venue(
        name=name,
        location=location,
        capacity=capacity,
        facilities=facilities,
        available=True
    )

    db.session.add(venue)
    db.session.commit()

    return redirect(url_for("venues"))


@app.route("/recommend-venue", methods=["POST"])
def recommend_venue():

    required_capacity = int(
        request.form["capacity"]
    )

    required_facility = request.form.get(
        "facility",
        ""
    ).strip()

    all_venues = Venue.query.order_by(
        Venue.id.desc()
    ).all()

    optimization_result = venue_agent.optimize_venue(
        venues=all_venues,
        required_capacity=required_capacity,
        required_facility=required_facility
    )

    return render_template(
        "venues.html",
        venues=all_venues,
        recommendation=optimization_result.get(
            "recommendation"
        ),
        optimization=optimization_result,
        required_capacity=required_capacity,
        required_facility=required_facility
    )

# =====================================
# MILESTONE 3 - SPONSORSHIP MANAGEMENT
# =====================================

@app.route("/sponsors")
def sponsors():

    sponsor_list = Sponsor.query.all()

    return render_template(
        "sponsors.html",
        sponsors=sponsor_list
    )


@app.route("/add_sponsor", methods=["POST"])
def add_sponsor():

    sponsor = Sponsor(
        company_name=request.form["company_name"],
        contact_person=request.form.get("contact_person"),
        email=request.form.get("email"),
        phone=request.form.get("phone"),
        sponsorship_package=request.form.get("sponsorship_package"),
        sponsorship_amount=float(
            request.form.get("sponsorship_amount") or 0
        ),
        attributable_revenue=(
            float(request.form["attributable_revenue"])
            if request.form.get("attributable_revenue")
            else None
        ),
        payment_status=request.form.get(
            "payment_status",
            "Pending"
        ),
        contract_status=request.form.get(
            "contract_status",
            "Pending"
        ),
        engagement_score=float(
            request.form.get("engagement_score") or 0
        ),
        event=request.form.get("event")
    )

    db.session.add(sponsor)
    db.session.commit()

    return redirect(url_for("sponsors"))


@app.route("/sponsor/<int:sponsor_id>/analysis")
def sponsor_analysis(sponsor_id):

    sponsor = Sponsor.query.get_or_404(sponsor_id)

    analysis = sponsorship_agent.analyze_sponsor(sponsor)

    return render_template(
        "sponsor_analysis.html",
        analysis=analysis
    )

# =====================================
# SPONSOR DELIVERABLE MANAGEMENT
# =====================================

@app.route("/sponsor/<int:sponsor_id>/deliverables")
def sponsor_deliverables(sponsor_id):

    sponsor = Sponsor.query.get_or_404(sponsor_id)

    deliverables = SponsorDeliverable.query.filter_by(
        sponsor_id=sponsor_id
    ).all()

    return render_template(
        "sponsor_deliverables.html",
        sponsor=sponsor,
        deliverables=deliverables
    )


@app.route(
    "/sponsor/<int:sponsor_id>/add_deliverable",
    methods=["POST"]
)
def add_deliverable(sponsor_id):

    deadline = request.form.get("deadline")

    deliverable = SponsorDeliverable(
        sponsor_id=sponsor_id,
        deliverable_name=request.form["deliverable_name"],
        description=request.form.get("description"),
        status=request.form.get("status", "Pending")
    )

    if deadline:
        deadline = datetime.strptime(
            deadline,
            "%Y-%m-%d"
        )
        deliverable.deadline = deadline

    db.session.add(deliverable)
    db.session.commit()

    return redirect(
        url_for(
            "sponsor_deliverables",
            sponsor_id=sponsor_id
        )
    )


@app.route(
    "/deliverable/<int:deliverable_id>/complete"
)
def complete_deliverable(deliverable_id):

    deliverable = SponsorDeliverable.query.get_or_404(
        deliverable_id
    )

    deliverable.status = "Completed"

    db.session.commit()

    return redirect(
        url_for(
            "sponsor_deliverables",
            sponsor_id=deliverable.sponsor_id
        )
    )

@app.route("/sponsor_analytics")
def sponsor_analytics():

    sponsors = Sponsor.query.all()

    total_sponsors = len(sponsors)

    total_amount = sum(
        sponsor.sponsorship_amount or 0
        for sponsor in sponsors
    )

    paid_sponsors = sum(
        1 for sponsor in sponsors
        if sponsor.payment_status == "Paid"
    )

    pending_sponsors = sum(
        1 for sponsor in sponsors
        if sponsor.payment_status == "Pending"
    )

    average_engagement = 0

    if total_sponsors > 0:
        average_engagement = round(
            sum(
                sponsor.engagement_score or 0
                for sponsor in sponsors
            ) / total_sponsors,
            2
        )

    return render_template(
        "sponsor_analytics.html",
        sponsors=sponsors,
        total_sponsors=total_sponsors,
        total_amount=total_amount,
        paid_sponsors=paid_sponsors,
        pending_sponsors=pending_sponsors,
        average_engagement=average_engagement
    )


# ==========================================
# MILESTONE 3 - INCIDENT MANAGEMENT ROUTES
# ==========================================

@app.route("/incidents")
def incidents():
    incidents_list = Incident.query.order_by(
        Incident.reported_at.desc()
    ).all()

    return render_template(
        "incidents.html",
        incidents=incidents_list
    )


@app.route("/add_incident", methods=["POST"])
def add_incident():

    severity = request.form.get("severity")

    # Automatic Priority Assignment
    priority_map = {
        "Low": "Low",
        "Medium": "Medium",
        "High": "High",
        "Critical": "Critical"
    }

    priority = priority_map.get(
        severity,
        "Medium"
    )

    # Create Incident
    incident = Incident(
        title=request.form.get("title"),
        description=request.form.get("description"),
        category=request.form.get("category"),
        severity=severity,
        priority=priority,
        affected_area=request.form.get("affected_area"),
        responsible_team=request.form.get("responsible_team"),
        status="Open"
    )

    # Save Incident
    db.session.add(incident)
    db.session.commit()


    # ==========================================
    # AUTOMATIC INCIDENT ESCALATION
    # ==========================================

    if incident.severity == "Critical":

        incident.escalation_status = "Escalated"

        incident.recommended_action = (
            "Critical incident automatically escalated "
            "to the Event Management Team for immediate action."
        )

        db.session.commit()


    # ==========================================
    # AUTOMATIC OPERATIONAL ALERT GENERATION
    # ==========================================

    if incident.severity in ["High", "Critical"]:

        alert_message = (
            f"{incident.severity} Alert: "
            f"{incident.title} reported in "
            f"{incident.affected_area or 'the event area'}."
        )

        alert = OperationalAlert(
            message=alert_message,
            alert_type="Incident",
            priority=incident.priority,
            related_incident_id=incident.id,
            status="Active"
        )

        db.session.add(alert)
        db.session.commit()


    return redirect("/incidents")
# ==========================================
# AUTOMATIC OPERATIONAL ALERT GENERATION
# ==========================================

# ==========================================
# AI INCIDENT ANALYSIS
# ==========================================

@app.route("/incident/<int:incident_id>/analysis")
def incident_analysis(incident_id):

    incident = Incident.query.get_or_404(incident_id)

    recommendations = []

    # AI-based recommendations
    if incident.category == "Technical":
        recommendations.append(
            "Immediately inspect the affected technical equipment."
        )
        recommendations.append(
            "Assign the technical or AV team for quick resolution."
        )

    elif incident.category == "Security":
        recommendations.append(
            "Notify the security team and assess the situation immediately."
        )
        recommendations.append(
            "Restrict access to the affected area if required."
        )

    elif incident.category == "Medical":
        recommendations.append(
            "Alert the medical response team immediately."
        )
        recommendations.append(
            "Provide first aid and escalate if emergency support is required."
        )

    elif incident.category == "Venue":
        recommendations.append(
            "Inspect the affected venue area immediately."
        )
        recommendations.append(
            "Arrange an alternative venue or backup facility if required."
        )

    elif incident.category == "Speaker":
        recommendations.append(
            "Contact the speaker immediately to confirm availability."
        )
        recommendations.append(
            "Prepare a backup speaker or adjust the session schedule."
        )

    else:
        recommendations.append(
            "Assign the responsible team and investigate the incident."
        )

    # Additional recommendation based on severity
    if incident.severity == "Critical":
        recommendations.append(
            "CRITICAL: Escalate immediately to the Event Manager."
        )

    elif incident.severity == "High":
        recommendations.append(
            "High priority: Resolve this incident as soon as possible."
        )

    elif incident.severity == "Medium":
        recommendations.append(
            "Monitor progress and resolve the incident within the event timeline."
        )

    else:
        recommendations.append(
            "Track the incident and resolve it through the normal workflow."
        )

    return render_template(
        "incident_analysis.html",
        incident=incident,
        recommendations=recommendations
    )


@app.route("/incident/<int:incident_id>/update_status/<status>")
def update_incident_status(incident_id, status):

    incident = Incident.query.get_or_404(incident_id)

    allowed_statuses = [
        "Open",
        "In Progress",
        "Resolved",
        "Closed"
    ]

    if status in allowed_statuses:

        incident.status = status

        if status == "Resolved":
            incident.resolved_at = datetime.utcnow()

        db.session.commit()

    return redirect("/incidents")


@app.route("/alerts")
def alerts():

    alerts_list = OperationalAlert.query.order_by(
        OperationalAlert.created_at.desc()
    ).all()

    return render_template(
        "alerts.html",
        alerts=alerts_list
    )

@app.route("/alerts/<int:alert_id>/resolve")
def resolve_alert(alert_id):

    alert = OperationalAlert.query.get_or_404(
        alert_id
    )

    alert.status = "Resolved"

    db.session.commit()

    return redirect("/alerts")


# ==========================================
# MILESTONE 3 - ANALYTICAL REPORTS
# ==========================================

@app.route("/reports")
def reports():

    # ==========================
    # SPONSOR REPORT
    # ==========================

    sponsors = Sponsor.query.all()

    total_sponsors = len(sponsors)

    total_sponsorship = sum(
        float(sponsor.sponsorship_amount or 0)
        for sponsor in sponsors
    )

    paid_sponsors = sum(
        1 for sponsor in sponsors
        if sponsor.payment_status == "Paid"
    )

    pending_sponsors = sum(
        1 for sponsor in sponsors
        if sponsor.payment_status != "Paid"
    )

    average_engagement = 0

    if total_sponsors > 0:

        average_engagement = round(
            sum(
                float(sponsor.engagement_score or 0)
                for sponsor in sponsors
            ) / total_sponsors,
            2
        )


    # ==========================
    # INCIDENT REPORT
    # ==========================

    incidents_list = Incident.query.all()

    total_incidents = len(incidents_list)

    open_incidents = sum(
        1 for incident in incidents_list
        if incident.status == "Open"
    )

    closed_incidents = sum(
        1 for incident in incidents_list
        if incident.status == "Closed"
    )

    high_incidents = sum(
        1 for incident in incidents_list
        if incident.severity == "High"
    )

    critical_incidents = sum(
        1 for incident in incidents_list
        if incident.severity == "Critical"
    )


    # ==========================
    # OPERATIONAL ALERT REPORT
    # ==========================

    alerts = OperationalAlert.query.all()

    total_alerts = len(alerts)

    active_alerts = sum(
        1 for alert in alerts
        if alert.status == "Active"
    )

    resolved_alerts = sum(
        1 for alert in alerts
        if alert.status == "Resolved"
    )


    return render_template(
        "reports.html",

        total_sponsors=total_sponsors,
        total_sponsorship=total_sponsorship,
        paid_sponsors=paid_sponsors,
        pending_sponsors=pending_sponsors,
        average_engagement=average_engagement,

        total_incidents=total_incidents,
        open_incidents=open_incidents,
        closed_incidents=closed_incidents,
        high_incidents=high_incidents,
        critical_incidents=critical_incidents,

        total_alerts=total_alerts,
        active_alerts=active_alerts,
        resolved_alerts=resolved_alerts
    )

# ===========================
# Run Application
# ===========================
if __name__ == "__main__":
    app.run(debug=True)


