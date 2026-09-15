from models import Attendee, Venue, Speaker, Session


class AnalyticsAgent:
    """
    AI Session Analytics Agent

    Generates:
    - Attendance analytics
    - Event popularity
    - Category distribution
    - Venue availability
    - Venue utilization
    - Speaker workload
    - Session statistics
    - Session popularity
    - AI recommendations
    """

    def generate_insights(self):

        # =====================================================
        # ATTENDEE ANALYTICS
        # =====================================================

        total_attendees = Attendee.query.count()

        checked_in = Attendee.query.filter_by(
            checkin=True
        ).count()

        pending = total_attendees - checked_in

        if total_attendees > 0:

            attendance_rate = round(
                (checked_in / total_attendees) * 100,
                1
            )

        else:

            attendance_rate = 0


        # =====================================================
        # EVENT POPULARITY
        # =====================================================

        event_rows = (
            Attendee.query.with_entities(
                Attendee.event
            )
            .filter(
                Attendee.event.isnot(None)
            )
            .all()
        )

        events = {}

        for row in event_rows:

            event_name = row[0]

            if event_name:

                events[event_name] = (
                    events.get(event_name, 0) + 1
                )


        if events:

            popular_event = max(
                events,
                key=events.get
            )

        else:

            popular_event = "No data"


        # =====================================================
        # CATEGORY ANALYSIS
        # =====================================================

        categories = {

            "Students": Attendee.query.filter_by(
                category="Student"
            ).count(),

            "Professionals": Attendee.query.filter_by(
                category="Professional"
            ).count(),

            "Speakers": Attendee.query.filter_by(
                category="Speaker"
            ).count()

        }


        if categories:

            majority_category = max(
                categories,
                key=categories.get
            )

        else:

            majority_category = "No data"


        # =====================================================
        # VENUE ANALYTICS
        # =====================================================

        total_venues = Venue.query.count()

        available_venues = Venue.query.filter_by(
            available=True
        ).count()

        occupied_venues = (
            total_venues - available_venues
        )


        if total_venues > 0:

            venue_availability = round(
                (
                    available_venues
                    /
                    total_venues
                ) * 100,
                1
            )

        else:

            venue_availability = 0


        # =====================================================
        # VENUE UTILIZATION
        # =====================================================

        venue_utilization = []

        sessions = Session.query.filter_by(
            status="Scheduled"
        ).all()

        for session in sessions:

            if not session.venue_id:
                continue

            venue = Venue.query.get(
                session.venue_id
            )

            if not venue:
                continue

            # Current data model associates attendees
            # with events rather than individual sessions.
            event_attendees = Attendee.query.filter_by(
                event=session.event
            ).count()

            if venue.capacity > 0:

                utilization = round(
                    (
                        event_attendees
                        /
                        venue.capacity
                    ) * 100,
                    1
                )

            else:

                utilization = 0

            venue_utilization.append({

                "session": session.title,

                "venue": venue.name,

                "capacity": venue.capacity,

                "attendees": event_attendees,

                "utilization": utilization

            })


        # =====================================================
        # SPEAKER ANALYTICS
        # =====================================================

        total_speakers = Speaker.query.count()

        available_speakers = Speaker.query.filter_by(
            availability=True
        ).count()

        unavailable_speakers = (
            total_speakers - available_speakers
        )


        # Speaker workload

        speaker_performance = []

        speakers = Speaker.query.all()

        for speaker in speakers:

            session_count = Session.query.filter_by(
                speaker_id=speaker.id
            ).count()

            scheduled_count = Session.query.filter_by(
                speaker_id=speaker.id,
                status="Scheduled"
            ).count()

            speaker_performance.append({

                "id": speaker.id,

                "name": speaker.name,

                "expertise": speaker.expertise,

                "experience": speaker.experience,

                "available": speaker.availability,

                "total_sessions": session_count,

                "scheduled_sessions": scheduled_count

            })


        # Sort speakers by number of sessions

        speaker_performance.sort(
            key=lambda x: x["total_sessions"],
            reverse=True
        )


        # =====================================================
        # SESSION ANALYTICS
        # =====================================================

        total_sessions = Session.query.count()

        scheduled_sessions = Session.query.filter_by(
            status="Scheduled"
        ).count()

        cancelled_sessions = Session.query.filter_by(
            status="Cancelled"
        ).count()


        # =====================================================
        # SESSION POPULARITY
        # =====================================================

        session_popularity = []

        for session in sessions:

            event_attendees = Attendee.query.filter_by(
                event=session.event
            ).count()

            session_popularity.append({

                "id": session.id,

                "title": session.title,

                "event": session.event,

                "date": session.date,

                "start_time": session.start_time,

                "end_time": session.end_time,

                "attendees": event_attendees,

                "status": session.status

            })


        session_popularity.sort(
            key=lambda x: x["attendees"],
            reverse=True
        )


        if session_popularity:

            most_popular_session = (
                session_popularity[0]["title"]
            )

        else:

            most_popular_session = "No data"


        # =====================================================
        # SESSION EVENT DISTRIBUTION
        # =====================================================

        session_events = {}

        for session in sessions:

            event_name = session.event

            session_events[event_name] = (
                session_events.get(event_name, 0) + 1
            )


        # =====================================================
        # SCHEDULED SESSION RATE
        # =====================================================

        if total_sessions > 0:

            scheduled_session_rate = round(
                (
                    scheduled_sessions
                    /
                    total_sessions
                ) * 100,
                1
            )

        else:

            scheduled_session_rate = 0


        # =====================================================
        # AI RECOMMENDATIONS
        # =====================================================

        recommendations = []


        # Attendance recommendation

        if total_attendees == 0:

            recommendations.append(
                "Start registering attendees to generate event insights."
            )

        elif attendance_rate < 50:

            recommendations.append(
                "Attendance is below 50%. "
                "Consider sending reminder emails."
            )

        elif attendance_rate >= 80:

            recommendations.append(
                "Attendance is strong. "
                "Current event capacity planning appears effective."
            )

        else:

            recommendations.append(
                "Attendance is moderate. "
                "Continue monitoring registrations and check-ins."
            )


        # Popular event

        if events:

            recommendations.append(
                f"{popular_event} is currently the "
                f"most popular event with "
                f"{events[popular_event]} registrations."
            )


        # Venue recommendation

        if total_venues > 0:

            if venue_availability < 30:

                recommendations.append(
                    "Venue availability is low. "
                    "Consider adding more venues."
                )

            elif venue_availability >= 70:

                recommendations.append(
                    "Venue availability is healthy."
                )


        # Speaker recommendation

        if total_speakers > 0:

            if available_speakers < 2:

                recommendations.append(
                    "Few speakers are currently available. "
                    "Consider adding more speakers."
                )

            else:

                recommendations.append(
                    f"{available_speakers} speakers are "
                    "currently available for scheduling."
                )


        # Session recommendation

        if total_sessions > 0:

            recommendations.append(
                f"{scheduled_sessions} of "
                f"{total_sessions} sessions are scheduled."
            )


        # Popular session

        if session_popularity:

            recommendations.append(
                f"{most_popular_session} is currently "
                "the most popular session based on "
                "event participation."
            )


        # =====================================================
        # FINAL ANALYTICS RESULT
        # =====================================================

        return {

            # Attendees

            "total_attendees": total_attendees,

            "checked_in": checked_in,

            "pending": pending,

            "attendance_rate": attendance_rate,


            # Events

            "events": events,

            "popular_event": popular_event,


            # Categories

            "categories": categories,

            "majority_category": majority_category,


            # Venues

            "total_venues": total_venues,

            "available_venues": available_venues,

            "occupied_venues": occupied_venues,

            "venue_availability": venue_availability,

            "venue_utilization": venue_utilization,


            # Speakers

            "total_speakers": total_speakers,

            "available_speakers": available_speakers,

            "unavailable_speakers": unavailable_speakers,

            "speaker_performance": speaker_performance,


            # Sessions

            "total_sessions": total_sessions,

            "scheduled_sessions": scheduled_sessions,

            "cancelled_sessions": cancelled_sessions,

            "scheduled_session_rate": scheduled_session_rate,

            "session_popularity": session_popularity,

            "most_popular_session": most_popular_session,

            "session_events": session_events,


            # AI

            "recommendations": recommendations

        }