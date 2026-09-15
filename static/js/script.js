document.addEventListener("DOMContentLoaded", () => {
	const tabs = document.querySelectorAll("[data-ops-tab]");
	const panels = document.querySelectorAll("[data-ops-panel]");

	tabs.forEach((tab) => tab.addEventListener("click", () => {
		tabs.forEach((item) => {
			const selected = item === tab;
			item.classList.toggle("active", selected);
			item.setAttribute("aria-selected", String(selected));
		});
		panels.forEach((panel) => {
			panel.hidden = panel.dataset.opsPanel !== tab.dataset.opsTab;
		});
	}));

	const runTests = document.querySelector("#run-tests");
	if (runTests) {
		runTests.addEventListener("click", async () => {
			runTests.disabled = true;
			runTests.innerHTML = '<i class="bi bi-hourglass-split"></i> Running...';
			const feedback = document.querySelector("#test-feedback");
			try {
				const report = await fetch("/api/platform-ops/checks").then((response) => response.json());
				const passed = report.checks.filter((check) => check.status === "Passed").length;
				const review = report.checks.filter((check) => check.status === "Review").length;
				document.querySelector("#tests-run").textContent = report.checks.length;
				document.querySelector("#tests-passed").textContent = passed;
				document.querySelector("#tests-review").textContent = review + report.checks.filter((check) => check.status === "Failed").length;
				document.querySelector("#test-summary").textContent = `${passed}/${report.checks.length} passed`;
				document.querySelector("#test-results").replaceChildren(...report.checks.map((check) => {
					const row = document.createElement("div");
					const marker = document.createElement("span");
					const content = document.createElement("div");
					const name = document.createElement("strong");
					const detail = document.createElement("small");
					const status = document.createElement("em");
					row.className = "test-row";
					marker.textContent = check.status === "Passed" ? "✓" : "!";
					name.textContent = check.name;
					detail.textContent = check.detail;
					status.className = check.status === "Passed" ? "passed" : "review";
					status.textContent = check.status;
					content.append(name, detail);
					row.append(marker, content, status);
					return row;
				}));
				feedback.textContent = review ? "Suite completed with deployment configuration review." : "Test suite completed successfully.";
			} catch (error) {
				feedback.textContent = "Test suite could not reach the application.";
			} finally {
				runTests.disabled = false;
				runTests.innerHTML = '<i class="bi bi-play-fill"></i> Run test suite';
			}
		});
	}

	const refresh = document.querySelector("#refresh-dashboard");
	if (refresh) refresh.addEventListener("click", () => window.location.reload());

	const liveMetrics = document.querySelector("[data-live-dashboard]");
	if (liveMetrics) {
		const metricMap = { "Attendees": "attendees", "Check-in rate": "attendance_rate", "Scheduled sessions": "scheduled_sessions", "Open incidents": "open_incidents", "Sponsors": "sponsors", "Payment realization": "sponsor_payment_realization" };
		let eventChart;
		let attendanceChart;
		let incidentChart;
		let sessionChart;
		const drawCharts = (snapshot) => {
			if (typeof Chart === "undefined") return;
			const chartOptions = { responsive: true, plugins: { legend: { labels: { color: "#52606d" } } }, scales: { x: { ticks: { color: "#52606d" }, grid: { color: "#e5e9ed" } }, y: { beginAtZero: true, ticks: { color: "#52606d" }, grid: { color: "#e5e9ed" } } } };
			if (eventChart) eventChart.destroy();
			eventChart = new Chart(document.querySelector("#event-demand-chart"), { type: "bar", data: { labels: Object.keys(snapshot.events), datasets: [{ label: "Registrations", data: Object.values(snapshot.events), backgroundColor: "#6d8b99", borderRadius: 5 }] }, options: chartOptions });
			if (attendanceChart) attendanceChart.destroy();
			attendanceChart = new Chart(document.querySelector("#attendance-chart"), { type: "doughnut", data: { labels: ["Checked in", "Pending"], datasets: [{ data: [snapshot.metrics.checked_in, Math.max(snapshot.metrics.attendees - snapshot.metrics.checked_in, 0)], backgroundColor: ["#5b9d8e", "#d8a36a"], borderColor: "#ffffff", borderWidth: 3 }] }, options: { responsive: true, cutout: "65%", plugins: { legend: { position: "bottom", labels: { color: "#52606d" } } } } });
			if (incidentChart) incidentChart.destroy();
			incidentChart = new Chart(document.querySelector("#incident-chart"), { type: "bar", data: { labels: Object.keys(snapshot.analytics.incident_severity), datasets: [{ label: "Incidents", data: Object.values(snapshot.analytics.incident_severity), backgroundColor: ["#8aa5b5", "#d8a36a", "#c9825e", "#b65757"], borderRadius: 4 }] }, options: { ...chartOptions, plugins: { legend: { display: false } } } });
			if (sessionChart) sessionChart.destroy();
			sessionChart = new Chart(document.querySelector("#session-chart"), { type: "doughnut", data: { labels: Object.keys(snapshot.analytics.session_status), datasets: [{ data: Object.values(snapshot.analytics.session_status), backgroundColor: ["#5b9d8e", "#d8a36a", "#8aa5b5", "#b65757"], borderColor: "#ffffff", borderWidth: 3 }] }, options: { responsive: true, cutout: "65%", plugins: { legend: { position: "bottom", labels: { color: "#52606d" } } } } });
			const alertList = document.querySelector("#live-alert-list");
			if (alertList) alertList.replaceChildren(...(snapshot.alerts.length ? snapshot.alerts.map((alert) => { const item = document.createElement("div"); item.className = "live-alert"; const priority = document.createElement("b"); priority.textContent = alert.priority || "Alert"; const message = document.createElement("span"); message.textContent = alert.message; item.append(priority, message); return item; }) : [Object.assign(document.createElement("p"), { className: "text-muted", textContent: "No active alerts." })]));
		};
		const refreshLiveMetrics = async () => {
			try {
				const response = await fetch("/api/live", { headers: { "Accept": "application/json" } });
				if (!response.ok) return;
				const live = await response.json();
				const snapshot = live.intelligence;
				const metrics = snapshot.metrics;
				drawCharts(snapshot);
					document.querySelector("#live-sync-status").textContent = `Synced ${live.server_time.slice(11, 19)}`;
				liveMetrics.querySelectorAll("[data-metric-label]").forEach((element) => {
					const key = metricMap[element.dataset.metricLabel];
					if (key && metrics[key] !== undefined) element.textContent = `${metrics[key]}${key.includes("rate") || key === "attendance_rate" ? "%" : ""}`;
				});
			} catch (error) {
			}
		};
		drawCharts({ events: JSON.parse(liveMetrics.dataset.events), metrics: JSON.parse(liveMetrics.dataset.metrics), analytics: JSON.parse(liveMetrics.dataset.analytics), alerts: JSON.parse(liveMetrics.dataset.alerts) });
		window.setInterval(refreshLiveMetrics, 30000);
	}

	const copyButton = document.querySelector("#copy-config");
	if (copyButton) copyButton.addEventListener("click", async () => {
		await navigator.clipboard.writeText(copyButton.dataset.copy);
		document.querySelector("#copy-feedback").textContent = "Configuration template copied.";
	});

	const pipeline = document.querySelector(".pipeline");
	if (pipeline) {
		const pipelineStages = JSON.parse(pipeline.dataset.stages || "[]");
		const selectStage = (stage) => {
			pipeline.querySelectorAll("[data-pipeline-key]").forEach((card) => card.classList.toggle("selected", card.dataset.pipelineKey === stage.key));
			document.querySelector("#pipeline-detail-title").textContent = stage.name;
			document.querySelector("#pipeline-detail-status").textContent = stage.status;
			document.querySelector("#pipeline-detail-input").textContent = stage.input;
			document.querySelector("#pipeline-detail-output").textContent = stage.output;
			document.querySelector("#pipeline-detail-description").textContent = stage.detail;
		};
		pipeline.querySelectorAll("[data-pipeline-key]").forEach((card) => card.addEventListener("click", () => selectStage(pipelineStages.find((stage) => stage.key === card.dataset.pipelineKey))));
		const refreshPipeline = document.querySelector("#refresh-pipeline");
		if (refreshPipeline) refreshPipeline.addEventListener("click", async () => {
			refreshPipeline.disabled = true;
			try { window.location.reload(); } finally { refreshPipeline.disabled = false; }
		});
	}

	const trigger = document.querySelector("#trigger-orchestration");
	const history = document.querySelector("#orchestration-history");
	if (history) fetch("/api/orchestration/runs").then((response) => response.json()).then((data) => {
		if (!data.runs.length) {
			history.textContent = "No orchestration runs have been recorded.";
			return;
		}
		history.replaceChildren(...data.runs.map((run) => {
			const item = document.createElement("div");
			item.className = "test-row";
			item.textContent = `#${run.id} ${run.trigger} · ${run.status} · ${run.created_at}`;
			return item;
		}));
	}).catch(() => { history.textContent = "Run history is temporarily unavailable."; });

	if (trigger) trigger.addEventListener("click", async () => {
		const sessionId = document.querySelector("#orchestration-session").value;
		const feedback = document.querySelector("#orchestration-feedback");
		if (!sessionId) {
			feedback.textContent = "Select a scheduled session before executing the workflow.";
			return;
		}
		trigger.disabled = true;
		try {
			const response = await fetch("/api/orchestration/trigger", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ event_type: "speaker_cancelled", session_id: Number(sessionId), reason: document.querySelector("#orchestration-reason").value }) });
			const result = await response.json();
			if (!response.ok) throw new Error(result.error || "Workflow rejected");
			feedback.textContent = `Workflow #${result.run_id} completed and persisted.`;
			document.querySelector("#orchestration-steps").replaceChildren(...result.steps.map((step) => {
				const item = document.createElement("div");
				item.className = "test-row";
				item.textContent = `${step.agent}: ${step.message}`;
				return item;
			}));
		} catch (error) {
			feedback.textContent = error.message;
		} finally {
			trigger.disabled = false;
		}
	});
});
