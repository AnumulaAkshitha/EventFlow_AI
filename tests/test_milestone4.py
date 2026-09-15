import unittest

from app import app


class Milestone4Tests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_is_database_backed(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")
        self.assertIn("database", response.get_json())

    def test_intelligence_snapshot_contract(self):
        response = self.client.get("/api/intelligence")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("metrics", payload)
        self.assertIn("risks", payload)
        self.assertIn("recommendations", payload)
        self.assertIn("analytics", payload)
        self.assertIn("incident_severity", payload["analytics"])
        self.assertIn("session_status", payload["analytics"])
        self.assertIn("venue_utilization", payload["analytics"])

    def test_live_update_contract(self):
        response = self.client.get("/api/live")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("server_time", payload)
        self.assertIn("intelligence", payload)
        self.assertIsInstance(payload["intelligence"]["alerts"], list)

    def test_executive_dashboard_renders_advanced_graphs(self):
        response = self.client.get("/executive-dashboard")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        for chart_id in ("event-demand-chart", "attendance-chart", "incident-chart", "session-chart"):
            self.assertIn(chart_id, page)

    def test_platform_operations_are_live(self):
        response = self.client.get("/api/platform-ops/checks")
        self.assertEqual(response.status_code, 200)
        checks = response.get_json()["checks"]
        self.assertTrue(any(check["name"] == "Database connectivity" for check in checks))
        self.assertTrue(all(check["status"] in {"Passed", "Review", "Failed"} for check in checks))

    def test_invalid_orchestration_event_is_rejected(self):
        response = self.client.post("/api/orchestration/trigger", json={"event_type": "unknown"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()