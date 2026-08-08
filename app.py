import csv
import io
import csv
from flask import Response
from flask import Flask, render_template, request, redirect, url_for
from config import Config
from models import db, Attendee
from utils.qr_generator import generate_qr

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

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
        recent_attendees=recent_attendees
    )
# ===========================
# Register Attendee
# ===========================
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

        # Duplicate Email Check
        existing_email = Attendee.query.filter_by(email=email).first()

        if existing_email:
            return render_template(
                "register.html",
                error="This email is already registered."
            )

        # Duplicate Phone Check
        existing_phone = Attendee.query.filter_by(phone=phone).first()

        if existing_phone:
            return render_template(
                "register.html",
                error="This phone number is already registered."
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
# Venues
# ===========================
@app.route("/venues")
def venues():
    return "<h2>Venue Module - Coming Soon</h2>"


# ===========================
# Speakers
# ===========================
@app.route("/speakers")
def speakers():
    return "<h2>Speaker Module - Coming Soon</h2>"


# ===========================
# Sessions
# ===========================
@app.route("/sessions")
def sessions():
    return "<h2>Sessions Module - Coming Soon</h2>"


# ===========================
# Check-In
# ===========================
from datetime import datetime

@app.route("/checkin", methods=["GET", "POST"])
def checkin():

    message = ""

    if request.method == "POST":

        registration_id = request.form["registration_id"]

        try:
            attendee_id = int(registration_id.replace("EVT", ""))

            attendee = Attendee.query.get(attendee_id)

            if attendee:

                if attendee.checkin:

                    message = "⚠ Attendee already checked in."

                else:

                    attendee.checkin = True
                    attendee.checkin_time = datetime.now()

                    db.session.commit()

                    message = f"✅ {attendee.name} checked in successfully."

            else:

                message = "❌ Attendee not found."

        except:

            message = "❌ Invalid Registration ID."

    return render_template("checkin.html", message=message)

# ===========================
# Analytics
# ===========================
@app.route("/analytics")
def analytics():

    total = Attendee.query.count()

    students = Attendee.query.filter_by(category="Student").count()

    professionals = Attendee.query.filter_by(category="Professional").count()

    speakers = Attendee.query.filter_by(category="Speaker").count()

    ai = Attendee.query.filter_by(event="AI Workshop").count()

    hackathon = Attendee.query.filter_by(event="Hackathon").count()

    cloud = Attendee.query.filter_by(event="Cloud Summit").count()

    return render_template(
        "analytics.html",
        total=total,
        students=students,
        professionals=professionals,
        speakers=speakers,
        ai=ai,
        hackathon=hackathon,
        cloud=cloud
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
@app.route("/ai")
def ai():

    total = Attendee.query.count()

    checked_in = Attendee.query.filter_by(checkin=True).count()

    pending = total - checked_in

    # Category counts
    students = Attendee.query.filter_by(category="Student").count()
    professionals = Attendee.query.filter_by(category="Professional").count()
    speakers = Attendee.query.filter_by(category="Speaker").count()

    # Event counts
    ai_count = Attendee.query.filter_by(event="AI Workshop").count()
    hackathon_count = Attendee.query.filter_by(event="Hackathon").count()
    cloud_count = Attendee.query.filter_by(event="Cloud Summit").count()

    # Most Popular Event
    events = {
        "AI Workshop": ai_count,
        "Hackathon": hackathon_count,
        "Cloud Summit": cloud_count
    }

    trending_event = max(events, key=events.get)

    # Majority Category
    categories = {
        "Students": students,
        "Professionals": professionals,
        "Speakers": speakers
    }

    majority_category = max(categories, key=categories.get)

    # Attendance Prediction (90%)
    expected_attendance = round(total * 0.90)

    # Venue Recommendation
    if total <= 50:
        venue = "Seminar Hall"
    elif total <= 150:
        venue = "Conference Hall"
    else:
        venue = "Main Auditorium"

    # Volunteer Recommendation
    volunteers = max(2, (total // 25) + 1)

    # Crowd Alert
    if checked_in >= total * 0.80 and total > 0:
        crowd = "High Crowd Expected"
    elif checked_in >= total * 0.50:
        crowd = "Moderate Crowd"
    else:
        crowd = "Low Crowd"

    # Confidence
    confidence = min(95, 80 + total)

    return render_template(
        "ai_insights.html",
        total=total,
        checked_in=checked_in,
        pending=pending,
        trending_event=trending_event,
        majority_category=majority_category,
        expected_attendance=expected_attendance,
        venue=venue,
        volunteers=volunteers,
        crowd=crowd,
        confidence=confidence
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
# Run Application
# ===========================
if __name__ == "__main__":
    app.run(debug=True)