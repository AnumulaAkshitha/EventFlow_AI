from models import (
    Attendee,
    Incident,
    OperationalAlert,
    OrchestrationRun,
    Session,
    Speaker,
    Venue,
    db,
)


class AgentOrchestrator:
    """Coordinate intelligence generation and operational alert creation."""

    def __init__(self, intelligence_engine):
        self.intelligence_engine = intelligence_engine

    def run(self, persist_alerts=False):
        snapshot = self.intelligence_engine.snapshot()
        if persist_alerts:
            for risk in snapshot["risks"]:
                message = f"{risk['title']}: {risk['detail']}"
                existing = OperationalAlert.query.filter_by(message=message, status="Active").first()
                if not existing:
                    db.session.add(OperationalAlert(
                        message=message,
                        alert_type="Intelligence",
                        priority=risk["level"].title(),
                    ))
            db.session.commit()
            snapshot["metrics"]["active_alerts"] = OperationalAlert.query.filter_by(status="Active").count()
        return snapshot

    def process_event(self, event_type, payload):
        """Execute a supported event workflow and persist its audit trail."""
        if event_type != "speaker_cancelled":
            raise ValueError(f"Unsupported orchestration event: {event_type}")

        session_id = payload.get("session_id")
        session = db.session.get(Session, session_id) if session_id else None
        if not session:
            raise ValueError("A valid session_id is required")

        speaker = db.session.get(Speaker, session.speaker_id) if session.speaker_id else None
        steps = [{
            "agent": "Speaker Agent",
            "status": "Completed",
            "message": f"Cancellation received for {speaker.name if speaker else 'unassigned speaker'}.",
        }]

        session.status = "Cancelled"
        if speaker:
            speaker.availability = True
        steps.append({"agent": "Event Intelligence Engine", "status": "Completed", "message": "Cancellation impact calculated from current event records."})

        replacement_venues = Venue.query.filter_by(available=True).order_by(Venue.capacity.asc()).all()
        event_attendees = Attendee.query.filter_by(event=session.event).count()
        suitable_venue = next((venue for venue in replacement_venues if venue.capacity >= event_attendees), None)
        steps.append({"agent": "Venue Agent", "status": "Completed", "message": f"{suitable_venue.name} is available for {event_attendees} affected attendees." if suitable_venue else "No available venue meets the affected attendance capacity."})
        steps.append({"agent": "Registration / Attendee System", "status": "Completed", "message": f"Identified {event_attendees} attendee(s) registered for {session.event}."})

        incident = Incident(
            title=f"Speaker cancellation: {session.title}",
            description=payload.get("reason", "Speaker cancellation requires schedule recovery."),
            category="Speaker",
            severity="High",
            priority="High",
            affected_area=session.event,
            responsible_team="Event Management Team",
            recommended_action="Assign a replacement speaker and notify affected attendees.",
            status="Open",
            escalation_status="Escalated",
        )
        db.session.add(incident)
        db.session.flush()
        steps.append({"agent": "Incident Agent", "status": "Completed", "message": f"Created incident #{incident.id} and escalated it to the Event Management Team."})

        db.session.add(OperationalAlert(
            message=f"High Alert: Speaker cancellation affects '{session.title}'.",
            alert_type="Orchestration",
            priority="High",
            related_incident_id=incident.id,
            status="Active",
        ))
        steps.append({"agent": "Operational Alert", "status": "Completed", "message": "Event manager alert created and linked to the incident."})

        run = OrchestrationRun(trigger=event_type, status="Completed", steps=steps)
        db.session.add(run)
        db.session.commit()
        return {"run_id": run.id, "trigger": event_type, "status": run.status, "steps": steps}