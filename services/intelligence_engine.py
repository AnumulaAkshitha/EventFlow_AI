from datetime import datetime, timezone

from models import Attendee, Incident, OperationalAlert, OrchestrationRun, Session, Speaker, Sponsor, Venue, db


class EventIntelligenceEngine:
    """Build a deterministic operational view from the current event state."""

    def snapshot(self):
        total_attendees = Attendee.query.count()
        checked_in = Attendee.query.filter_by(checkin=True).count()
        total_sessions = Session.query.count()
        scheduled_sessions = Session.query.filter_by(status="Scheduled").count()
        total_venues = Venue.query.count()
        available_venues = Venue.query.filter_by(available=True).count()
        open_incidents = Incident.query.filter_by(status="Open").count()
        active_alert_count = OperationalAlert.query.filter_by(status="Active").count()
        sponsors = Sponsor.query.count()
        paid_sponsors = Sponsor.query.filter_by(payment_status="Paid").count()
        sponsor_payment_realization = round(paid_sponsors / sponsors * 100, 1) if sponsors else 0
        sponsors_with_roi_data = Sponsor.query.filter(
            Sponsor.attributable_revenue.isnot(None),
            Sponsor.sponsorship_amount > 0,
        ).all()
        roi_investment = sum(sponsor.sponsorship_amount or 0 for sponsor in sponsors_with_roi_data)
        roi_revenue = sum(sponsor.attributable_revenue or 0 for sponsor in sponsors_with_roi_data)
        sponsor_roi = round((roi_revenue - roi_investment) / roi_investment * 100, 1) if roi_investment else None
        latest_run = OrchestrationRun.query.order_by(OrchestrationRun.created_at.desc()).first()
        incident_severity = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
        for incident in Incident.query.with_entities(Incident.severity).all():
            if incident[0] in incident_severity:
                incident_severity[incident[0]] += 1

        session_status = {}
        for session in Session.query.with_entities(Session.status).all():
            session_status[session[0] or "Unknown"] = session_status.get(session[0] or "Unknown", 0) + 1

        venue_utilization = []
        for session in Session.query.filter_by(status="Scheduled").all():
            venue = db.session.get(Venue, session.venue_id) if session.venue_id else None
            if venue:
                attendees = Attendee.query.filter_by(event=session.event).count()
                utilization = round(attendees / venue.capacity * 100, 1) if venue.capacity else 0
                venue_utilization.append({"venue": venue.name, "session": session.title, "utilization": utilization})

        active_alert_records = OperationalAlert.query.filter_by(status="Active").order_by(OperationalAlert.created_at.desc()).limit(10).all()

        attendance_rate = round(checked_in / total_attendees * 100, 1) if total_attendees else 0
        session_rate = round(scheduled_sessions / total_sessions * 100, 1) if total_sessions else 0
        venue_rate = round(available_venues / total_venues * 100, 1) if total_venues else 0

        event_counts = {}
        for attendee in Attendee.query.with_entities(Attendee.event).all():
            if attendee[0]:
                event_counts[attendee[0]] = event_counts.get(attendee[0], 0) + 1

        risks = []
        if total_attendees and attendance_rate < 50:
            risks.append({"level": "high", "title": "Low check-in conversion", "detail": f"Only {attendance_rate}% of registered attendees are checked in."})
        if total_venues and venue_rate < 30:
            risks.append({"level": "high", "title": "Venue capacity risk", "detail": "Less than 30% of venues are currently available."})
        if open_incidents:
            risks.append({"level": "critical" if open_incidents > 2 else "medium", "title": "Open incidents require attention", "detail": f"{open_incidents} incident(s) remain open."})
        if total_sessions and scheduled_sessions < total_sessions:
            risks.append({"level": "medium", "title": "Scheduling coverage gap", "detail": f"{total_sessions - scheduled_sessions} session(s) are not scheduled."})

        recommendations = [
            "Review the live risk queue before making operational changes.",
            "Use check-in trends to adjust staffing and room capacity in real time.",
        ]
        if total_attendees == 0:
            recommendations[0] = "Import or register attendees to activate event intelligence."
        elif attendance_rate < 50:
            recommendations[0] = "Trigger an attendee reminder campaign and monitor check-in conversion."
        if not total_sessions:
            recommendations.append("Create the first session schedule so venue and speaker utilization can be measured.")
        if not risks:
            recommendations.append("No threshold risks detected. Continue monitoring the live operational metrics.")

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "metrics": {
                "attendees": total_attendees,
                "checked_in": checked_in,
                "attendance_rate": attendance_rate,
                "sessions": total_sessions,
                "scheduled_sessions": scheduled_sessions,
                "session_rate": session_rate,
                "venues": total_venues,
                "available_venues": available_venues,
                "venue_rate": venue_rate,
                "speakers": Speaker.query.count(),
                "open_incidents": open_incidents,
                "active_alerts": active_alert_count,
                "sponsors": sponsors,
                "paid_sponsors": paid_sponsors,
                "sponsor_payment_realization": sponsor_payment_realization,
                "sponsor_roi": sponsor_roi,
                "sponsor_roi_investment": roi_investment,
                "sponsor_attributable_revenue": roi_revenue,
            },
            "events": event_counts,
            "analytics": {
                "incident_severity": incident_severity,
                "session_status": session_status,
                "venue_utilization": venue_utilization,
            },
            "alerts": [{"id": alert.id, "message": alert.message, "priority": alert.priority, "created_at": alert.created_at.isoformat() + "Z"} for alert in active_alert_records],
            "pipeline": [
                {"key": "registration", "name": "Registration Agent", "status": "Active", "input": "Attendee records", "output": f"{total_attendees} attendees processed", "detail": f"Reads attendee registrations, check-in state, and event assignments from MySQL."},
                {"key": "specialists", "name": "Specialist Agents", "status": "Active", "input": f"{Speaker.query.count()} speakers, {total_venues} venues, {total_sessions} sessions", "output": "Operational domain signals", "detail": "Speaker, venue, scheduling, sponsorship, and incident agents contribute domain-specific signals."},
                {"key": "intelligence", "name": "Intelligence Engine", "status": "Active", "input": "Agent signals and event records", "output": f"{len(recommendations)} recommendations, {len(risks)} risks", "detail": "Calculates KPIs, thresholds, demand, risk priority, and decision recommendations."},
                {"key": "decisions", "name": "Decision Support", "status": "Ready", "input": f"{len(risks)} prioritized risks", "output": "Executive dashboard updates", "detail": f"Publishes live decisions and alerts. Latest orchestration run: #{latest_run.id}." if latest_run else "Publishes live decisions and alerts. No manual orchestration run has been recorded yet."},
            ],
            "risks": risks,
            "recommendations": recommendations,
        }