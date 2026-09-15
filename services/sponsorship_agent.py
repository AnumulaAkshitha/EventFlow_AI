from models import Sponsor, SponsorDeliverable


class SponsorshipAgent:

    def analyze_sponsor(self, sponsor):

        pending_deliverables = SponsorDeliverable.query.filter_by(
            sponsor_id=sponsor.id,
            status="Pending"
        ).count()

        total_deliverables = SponsorDeliverable.query.filter_by(
            sponsor_id=sponsor.id
        ).count()

        completed_deliverables = SponsorDeliverable.query.filter_by(
            sponsor_id=sponsor.id,
            status="Completed"
        ).count()

        # Calculate deliverable completion percentage
        if total_deliverables > 0:
            completion_percentage = round(
                (completed_deliverables / total_deliverables) * 100,
                2
            )
        else:
            completion_percentage = 0

        # Determine sponsor risk
        risk_level = "Low"

        if sponsor.payment_status != "Paid":
            risk_level = "High"

        elif pending_deliverables > 0:
            risk_level = "Medium"

        # Generate recommendation
        recommendations = []

        if sponsor.payment_status != "Paid":
            recommendations.append(
                "Follow up regarding pending sponsorship payment."
            )

        if sponsor.contract_status != "Signed":
            recommendations.append(
                "Follow up regarding the sponsorship contract."
            )

        if pending_deliverables > 0:
            recommendations.append(
                f"Complete {pending_deliverables} pending deliverable(s)."
            )

        if sponsor.engagement_score < 50:
            recommendations.append(
                "Increase sponsor engagement through promotional activities."
            )

        if not recommendations:
            recommendations.append(
                "Sponsor commitments are progressing successfully."
            )

        return {
            "sponsor": sponsor.company_name,
            "package": sponsor.sponsorship_package,
            "payment_status": sponsor.payment_status,
            "contract_status": sponsor.contract_status,
            "engagement_score": sponsor.engagement_score,
            "total_deliverables": total_deliverables,
            "completed_deliverables": completed_deliverables,
            "pending_deliverables": pending_deliverables,
            "completion_percentage": completion_percentage,
            "risk_level": risk_level,
            "recommendations": recommendations
        }


sponsorship_agent = SponsorshipAgent()