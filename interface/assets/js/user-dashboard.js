(function () {
  const currentUser = window.AppAuth.requireRole("user");
  if (!currentUser) {
    return;
  }

  const welcomeMessage = document.getElementById("welcomeMessage");
  const vehicleFilter = document.getElementById("vehicleFilter");
  const vehicleCards = document.getElementById("vehicleCards");
  const historyChart = document.getElementById("historyChart");
  const snapshotMetrics = document.getElementById("snapshotMetrics");
  const alertList = document.getElementById("alertList");
  const socketStatus = document.getElementById("socketStatus");

  let dashboardState = { vehicles: [], alerts: [], history: [] };

  function formatNumber(value, suffix) {
    if (value === null || value === undefined) {
      return "--";
    }
    return `${Number(value).toFixed(1)}${suffix || ""}`;
  }

  function formatTime(value) {
    return value ? new Date(value).toLocaleString() : "--";
  }

  function renderStatus(status) {
    const normalized = status || "offline";
    return `<span class="status-pill ${normalized}">${normalized.replace("_", " ")}</span>`;
  }

  function renderVehicleCards() {
    if (!dashboardState.vehicles.length) {
      vehicleCards.innerHTML = '<div class="vehicle-card"><p class="message">No vehicles assigned yet.</p></div>';
      return;
    }

    vehicleCards.innerHTML = dashboardState.vehicles
      .map(function (vehicle) {
        const reading = vehicle.latest_reading || {};
        const status = vehicle.status || "offline";
        return `
          <article class="vehicle-card">
            <div class="row" style="justify-content: space-between; align-items: center">
              <div>
                <h3>${vehicle.display_name || vehicle.license_plate}</h3>
                <p class="subtle">${vehicle.license_plate}</p>
              </div>
              ${renderStatus(status)}
            </div>
            <div class="metric-grid">
              <div>
                <div class="subtle">Current</div>
                <div class="metric-value">${formatNumber(reading.current, " mA")}</div>
              </div>
              <div>
                <div class="subtle">Power</div>
                <div class="metric-value">${formatNumber(reading.power, " W")}</div>
              </div>
              <div>
                <div class="subtle">Updated</div>
                <div class="metric-value" style="font-size: 1rem">${formatTime(reading.timestamp)}</div>
              </div>
            </div>
          </article>
        `;
      })
      .join("");
  }

  function renderSnapshot() {
    const selectedPlate = vehicleFilter.value;
    const selectedVehicle = dashboardState.vehicles.find(function (vehicle) {
      return vehicle.license_plate === selectedPlate;
    }) || dashboardState.vehicles[0];

    const reading = selectedVehicle && selectedVehicle.latest_reading ? selectedVehicle.latest_reading : {};
    const alert = selectedVehicle && selectedVehicle.latest_alert ? selectedVehicle.latest_alert : null;

    snapshotMetrics.innerHTML = `
      <div class="metric-card">
        <div class="subtle">Selected plate</div>
        <div class="metric-value">${selectedVehicle ? selectedVehicle.license_plate : "--"}</div>
      </div>
      <div class="metric-card">
        <div class="subtle">Voltage</div>
        <div class="metric-value">${formatNumber(reading.voltage, " V")}</div>
      </div>
      <div class="metric-card">
        <div class="subtle">Power</div>
        <div class="metric-value">${formatNumber(reading.power, " W")}</div>
      </div>
      <div class="metric-card">
        <div class="subtle">Latest alert</div>
        <div class="metric-value" style="font-size: 1rem">${alert ? alert.type : "none"}</div>
      </div>
    `;
  }

  function renderAlerts() {
    if (!dashboardState.alerts.length) {
      alertList.innerHTML = '<div class="alert-item"><p class="message">No alerts yet.</p></div>';
      return;
    }

    alertList.innerHTML = dashboardState.alerts
      .map(function (alert) {
        return `
          <article class="alert-item">
            <div class="row" style="justify-content: space-between">
              <strong>${alert.type}</strong>
              <span class="subtle">${formatTime(alert.created_at)}</span>
            </div>
            <p>${alert.message}</p>
            <p class="subtle">Measured: ${alert.measured_value} | Threshold: ${alert.threshold_value}</p>
          </article>
        `;
      })
      .join("");
  }

  function renderHistoryChart() {
    if (!dashboardState.history.length) {
      historyChart.innerHTML = '<p class="message">No history for the selected plate yet.</p>';
      return;
    }

    const width = 640;
    const height = 210;
    const padding = 18;
    const values = dashboardState.history.map(function (item) {
      return item.current;
    });
    const max = Math.max.apply(null, values);
    const min = Math.min.apply(null, values);
    const range = Math.max(max - min, 1);

    const points = dashboardState.history
      .slice()
      .reverse()
      .map(function (item, index, array) {
        const x = padding + ((width - padding * 2) / Math.max(array.length - 1, 1)) * index;
        const y = height - padding - ((item.current - min) / range) * (height - padding * 2);
        return `${x},${y}`;
      })
      .join(" ");

    historyChart.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        <polyline fill="none" stroke="#10b981" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" points="${points}" />
      </svg>
    `;
  }

  async function loadHistory() {
    const plate = vehicleFilter.value;
    if (!plate) {
      dashboardState.history = [];
      renderHistoryChart();
      return;
    }

    const response = await window.AppApi.get(`/api/user/history?plate=${encodeURIComponent(plate)}`);
    dashboardState.history = response.items || [];
    renderHistoryChart();
  }

  async function loadDashboard() {
    welcomeMessage.textContent = `Signed in as ${currentUser.email}`;
    const dashboard = await window.AppApi.get("/api/user/dashboard");
    const alerts = await window.AppApi.get("/api/user/alerts");
    dashboardState.vehicles = dashboard.vehicles || [];
    dashboardState.alerts = alerts.items || [];

    vehicleFilter.innerHTML = dashboardState.vehicles
      .map(function (vehicle) {
        return `<option value="${vehicle.license_plate}">${vehicle.license_plate}</option>`;
      })
      .join("");

    renderVehicleCards();
    renderSnapshot();
    renderAlerts();
    await loadHistory();
  }

  function wireSocket() {
    const socket = window.AppSocket.connect({
      connected: function () {
        socketStatus.textContent = "Socket connected";
        socketStatus.className = "status-pill online";
      },
      "sensor:update:user": function (payload) {
        const target = dashboardState.vehicles.find(function (vehicle) {
          return payload.vehicle && vehicle.id === payload.vehicle.id;
        });
        if (target) {
          target.latest_reading = payload.reading;
          target.status = payload.reading.status || target.status;
          renderVehicleCards();
          renderSnapshot();
          if (vehicleFilter.value === payload.vehicle.license_plate) {
            dashboardState.history.unshift(payload.reading);
            dashboardState.history = dashboardState.history.slice(0, 200);
            renderHistoryChart();
          }
        }
      },
      "alert:new": function (alert) {
        dashboardState.alerts.unshift(alert);
        dashboardState.alerts = dashboardState.alerts.slice(0, 20);
        renderAlerts();
      },
    });

    if (!socket) {
      socketStatus.textContent = "Socket unavailable";
      socketStatus.className = "status-pill offline";
    }
  }

  vehicleFilter.addEventListener("change", async function () {
    renderSnapshot();
    await loadHistory();
  });

  document.getElementById("refreshButton").addEventListener("click", loadDashboard);
  document.getElementById("logoutButton").addEventListener("click", function () {
    window.AppAuth.clearSession();
    window.location.href = "login.html";
  });

  loadDashboard();
  wireSocket();
})();
