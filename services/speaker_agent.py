class SpeakerAgent:
    """
    AI Speaker Recommendation Agent

    Evaluates speakers based on:
    - Expertise match
    - Experience
    - Availability

    Total score = 100 points
    """

    def recommend(
        self,
        speakers,
        topic,
        required_experience=0
    ):

        recommendations = []

        topic = (
            topic or ""
        ).strip().lower()

        # =================================
        # Evaluate every speaker
        # =================================

        for speaker in speakers:

            # --------------------------------
            # Availability
            # --------------------------------

            if not speaker.availability:
                continue

            # --------------------------------
            # Expertise matching
            # --------------------------------

            expertise = (
                speaker.expertise or ""
            ).lower()

            topic_words = set(
                topic.split()
            )

            expertise_words = set(
                expertise.replace(",", " ").split()
            )

            matched_words = (
                topic_words.intersection(
                    expertise_words
                )
            )

            # Exact topic match
            if topic and topic in expertise:

                expertise_score = 60

            # Partial keyword match
            elif matched_words:

                expertise_score = 40

            # No match
            else:

                expertise_score = 10

            # --------------------------------
            # Experience - 30 points
            # --------------------------------

            speaker_experience = (
                speaker.experience or 0
            )

            if required_experience <= 0:

                experience_score = 30

            elif speaker_experience >= required_experience:

                experience_score = 30

            else:

                experience_score = round(
                    (
                        speaker_experience
                        /
                        required_experience
                    ) * 30
                )

                experience_score = min(
                    experience_score,
                    30
                )

            # --------------------------------
            # Availability - 10 points
            # --------------------------------

            availability_score = 10

            # --------------------------------
            # Final score
            # --------------------------------

            score = (
                expertise_score
                +
                experience_score
                +
                availability_score
            )

            recommendations.append({

                "speaker": speaker,

                "score": score,

                "expertise_score": expertise_score,

                "experience_score": experience_score,

                "availability_score": availability_score

            })

        # =================================
        # No suitable speaker
        # =================================

        if not recommendations:

            return {

                "success": False,

                "recommendation": None,

                "recommendations": [],

                "message": (
                    "No available speaker "
                    "matches the requirements."
                ),

                "suggestion": (
                    "Consider adding more speakers "
                    "or changing the expertise requirement."
                )

            }

        # =================================
        # Sort by highest score
        # =================================

        recommendations.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        # =================================
        # Best speaker
        # =================================

        best = recommendations[0]

        best_speaker = best["speaker"]

        # =================================
        # AI explanation
        # =================================

        if best["expertise_score"] == 60:

            explanation = (
                f"{best_speaker.name} has a strong "
                f"expertise match for the requested topic."
            )

        elif best["expertise_score"] == 40:

            explanation = (
                f"{best_speaker.name} has a partial "
                f"expertise match for the requested topic."
            )

        else:

            explanation = (
                f"{best_speaker.name} has limited "
                f"topic matching but scores well "
                f"on other criteria."
            )

        # =================================
        # Final result
        # =================================

        return {

            "success": True,

            "recommendation": best_speaker,

            "recommendations": recommendations,

            "score": best["score"],

            "expertise_score": best["expertise_score"],

            "experience_score": best["experience_score"],

            "availability_score": best["availability_score"],

            "message": (
                f"AI recommends {best_speaker.name} "
                f"with a match score of "
                f"{best['score']}/100."
            ),

            "suggestion": explanation

        }