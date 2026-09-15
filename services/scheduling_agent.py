from models import Session, Speaker, Venue


class SchedulingAgent:
    """
    AI-assisted Scheduling Agent.

    Checks:
    - Speaker availability
    - Venue availability
    - Speaker scheduling conflicts
    - Venue scheduling conflicts
    - Invalid time ranges
    """

    def check_schedule(
        self,
        date,
        start_time,
        end_time,
        speaker_id,
        venue_id
    ):

        conflicts = []

        # --------------------------------
        # Validate time
        # --------------------------------

        if start_time >= end_time:

            conflicts.append(
                "End time must be later than start time."
            )

            return {
                "success": False,
                "conflicts": conflicts
            }

        # --------------------------------
        # Check speaker
        # --------------------------------

        speaker = Speaker.query.get(speaker_id)

        if not speaker:

            conflicts.append(
                "Selected speaker does not exist."
            )

        elif not speaker.availability:

            conflicts.append(
                f"{speaker.name} is currently unavailable."
            )

        # --------------------------------
        # Check venue
        # --------------------------------

        venue = Venue.query.get(venue_id)

        if not venue:

            conflicts.append(
                "Selected venue does not exist."
            )

        elif not venue.available:

            conflicts.append(
                f"{venue.name} is currently unavailable."
            )

        # --------------------------------
        # Check speaker conflicts
        # --------------------------------

        if speaker:

            speaker_conflict = Session.query.filter(
                Session.speaker_id == speaker_id,
                Session.date == date,
                Session.start_time < end_time,
                Session.end_time > start_time
            ).first()

            if speaker_conflict:

                conflicts.append(
                    f"{speaker.name} is already assigned to "
                    f"'{speaker_conflict.title}' during this time."
                )

        # --------------------------------
        # Check venue conflicts
        # --------------------------------

        if venue:

            venue_conflict = Session.query.filter(
                Session.venue_id == venue_id,
                Session.date == date,
                Session.start_time < end_time,
                Session.end_time > start_time
            ).first()

            if venue_conflict:

                conflicts.append(
                    f"{venue.name} is already occupied by "
                    f"'{venue_conflict.title}' during this time."
                )

        # --------------------------------
        # Final decision
        # --------------------------------

        if conflicts:

            return {
                "success": False,
                "conflicts": conflicts
            }

        return {
            "success": True,
            "conflicts": [],
            "message": (
                "Schedule is valid. "
                "No speaker or venue conflicts detected."
            )
        }