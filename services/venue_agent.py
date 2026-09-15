class VenueAgent:
    """
    AI Venue Optimization Agent

    Evaluates venues using:
    - Capacity matching
    - Facility matching
    - Availability
    - Space efficiency
    - Overall optimization score

    Total score = 100 points
    """

    def optimize_venue(
        self,
        venues,
        required_capacity,
        required_facility=""
    ):

        recommendations = []

        required_facility = (
            required_facility or ""
        ).strip().lower()

        # =================================
        # Evaluate every venue
        # =================================

        for venue in venues:

            # --------------------------------
            # 1. Availability Check
            # --------------------------------

            if not venue.available:
                continue

            # --------------------------------
            # 2. Capacity Check
            # --------------------------------

            if venue.capacity < required_capacity:
                continue

            # --------------------------------
            # Calculate utilization
            # --------------------------------

            utilization = (
                required_capacity / venue.capacity
            )

            utilization_percentage = round(
                utilization * 100,
                1
            )

            # =================================
            # 3. Capacity Score - 40 points
            # =================================

            if utilization >= 0.70:

                capacity_score = 40

            elif utilization >= 0.50:

                capacity_score = 35

            elif utilization >= 0.30:

                capacity_score = 30

            else:

                capacity_score = 20

            # =================================
            # 4. Facility Score - 25 points
            # =================================

            facilities = (
                venue.facilities or ""
            ).lower()

            if not required_facility:

                facility_score = 25

            elif required_facility in facilities:

                facility_score = 25

            else:

                # Venue does not satisfy the
                # requested facility.
                continue

            # =================================
            # 5. Availability Score - 20 points
            # =================================

            availability_score = 20

            # =================================
            # 6. Space Efficiency - 15 points
            # =================================

            if 0.70 <= utilization <= 0.90:

                efficiency_score = 15

            elif 0.50 <= utilization < 0.70:

                efficiency_score = 12

            elif utilization > 0.90:

                efficiency_score = 8

            else:

                efficiency_score = 5

            # =================================
            # Final Score - 100 points
            # =================================

            score = (
                capacity_score
                + facility_score
                + availability_score
                + efficiency_score
            )

            # =================================
            # Unused Capacity
            # =================================

            unused_capacity = (
                venue.capacity - required_capacity
            )

            recommendations.append({

                "venue": venue,

                "score": score,

                "utilization": utilization_percentage,

                "unused_capacity": unused_capacity,

                "capacity_score": capacity_score,

                "facility_score": facility_score,

                "availability_score": availability_score,

                "efficiency_score": efficiency_score

            })

        # =================================
        # No suitable venue
        # =================================

        if not recommendations:

            return {

                "success": False,

                "recommendation": None,

                "recommendations": [],

                "message": (
                    "No suitable venue found "
                    "for the given requirements."
                ),

                "suggestion": (
                    "Consider adding a larger venue, "
                    "changing the facility requirement, "
                    "or adding more available venues."
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
        # Best venue
        # =================================

        best = recommendations[0]

        best_venue = best["venue"]

        # =================================
        # Upgrade / Downgrade Analysis
        # =================================

        if best["utilization"] < 40:

            suggestion = (
                f"{best_venue.name} is only "
                f"{best['utilization']}% utilized. "
                f"Consider downgrading to a smaller "
                f"venue to reduce unused space."
            )

        elif best["utilization"] >= 90:

            suggestion = (
                f"{best_venue.name} is highly utilized "
                f"at {best['utilization']}%. "
                f"Consider upgrading to a larger venue "
                f"if attendance increases."
            )

        elif best["utilization"] >= 70:

            suggestion = (
                f"{best_venue.name} is efficiently utilized "
                f"at {best['utilization']}%. "
                f"This is an efficient capacity match."
            )

        else:

            suggestion = (
                f"{best_venue.name} provides a good balance "
                f"between capacity and available space."
            )

        # =================================
        # Final Result
        # =================================

        return {

            "success": True,

            "recommendation": best_venue,

            "recommendations": recommendations,

            "utilization": best["utilization"],

            "unused_capacity": best["unused_capacity"],

            "facility_match": best["facility_score"],

            "score": best["score"],

            "capacity_score": best["capacity_score"],

            "facility_score": best["facility_score"],

            "availability_score": best["availability_score"],

            "efficiency_score": best["efficiency_score"],

            "message": (
                f"AI recommends {best_venue.name}. "
                f"Optimization score: "
                f"{best['score']}/100. "
                f"Expected utilization: "
                f"{best['utilization']}%."
            ),

            "suggestion": suggestion

        }