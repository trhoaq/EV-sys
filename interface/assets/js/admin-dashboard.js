(function () {
  const currentUser = window.AppAuth.requireRole("admin");
  if (!currentUser) {
    return;
  }

  const adminWelcomeMessage = document.getElementById("adminWelcomeMessage");
  const overviewMetrics = document.getElementById("overviewMetrics");
  const deviceCards = document.getElementById("deviceCards");
  const deviceTableBody = document.getElementById("deviceTableBody");
  const deviceHistoryFilter = document.getElementById("deviceHistoryFilter");
  const adminHistoryChart = document.getElementById("adminHistoryChart");
  const alertTableBody = document.getElementById("alertTableBody");
  const assignmentUser = document.getElementById("assignmentUser");
  const assignmentPlate = document.getElementById("assignmentPlate");
  const assignmentDevice = document.getElementById("assignmentDevice");
  const assignmentDisplayName = document.getElementById("assignmentDisplayName");
  const assignmentMessage = document.getElementById("assignmentMessage");
  const settingsMessage = document.getElementById("settingsMessage");
  const minCurrentInput = document.getElementById("minCurrent");
  const detectionCurrentInput = document.getElementById("detectionCurrent");
  const maxCurrentInput = document.getElementById("maxCurrent");
  const adminSocketStatus = document.getElementById("adminSocketStatus");

  let state = { devices: [], alerts: [], users: [], settings: null, history: [] };

  function formatTime(value) {
    return value ? new Date(value).toLocaleString() : "--";
  }

  function formatNumber(value, suffix) {
    if (value === null || value === undefined) {
      return "--";
    }
    return `${Number(value).toFixed(1)}${suffix || ""}`;
  }

  function renderStatus(status) {
    return `<span class="status-pill ${status}">${status.replace("_", " ")}</span>`;
  }

  function renderOverview() {
    const onlineDevices = state.devices.filter(function (device) {
      return device.status && device.status !== "offline";
    }).length;

    overviewMetrics.innerHTML = `
      <div class="metric-card">
        <div class="subtle">Devices</div>
        <div class="metric-value">${state.devices.length}</div>
      </div>
      <div class="metric-card">
        <div class="subtle">Online</div>
        <div class="metric-value">${onlineDevices}</div>
      </div>
      <div class="metric-card">
        <div class="subtle">Alerts</div>
        <div class="metric-value">${state.alerts.length}</div>
      </div>
      <div class="metric-card">
        <div class="subtle">Users</div>
        <div class="metric-value">${state.users.length}</div>
      </div>
    `;
  }

  function renderUsers() {
    assignmentUser.innerHTML = state.users
      .filter(function (user) {
        return user.role === "user";
      })
      .map(function (user) {
        return `<option value="${user.id}">${user.email}</option>`;
      })
      .join("");
  }

  function renderDevices() {
    if (!state.devices.length) {
      deviceCards.innerHTML = '<div class="vehicle-card"><p class="message">No devices available yet.</p></div>';
      deviceTableBody.innerHTML = '<tr><td colspan="7">No devices available yet.</td></tr>';
      return;
    }

    deviceCards.innerHTML = state.devices
      .map(function (device) {
        const reading = device.latest_reading || {};
        const activePlate = device.active_vehicle ? device.active_vehicle.license_plate : "No active charging";
        return `
          <article class="vehicle-card">
            <div class="row" style="justify-content: space-between; align-items: center">
              <div>
                <h3>${device.name || device.device_code}</h3>
                <p class="subtle">${device.device_code}</p>
              </div>
              ${renderStatus(device.status)}
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
                <div class="subtle">Active session</div>
                <div class="metric-value" style="font-size: 1rem">${activePlate}</div>
              </div>
            </div>
          </article>
        `;
      })
      .join("");

    deviceTableBody.innerHTML = state.devices
      .map(function (device) {
        const reading = device.latest_reading || {};
        return `
          <tr>
            <td>${device.device_code}</td>
            <td>${renderStatus(device.status)}</td>
            <td>${formatNumber(reading.current, " mA")}</td>
            <td>${formatNumber(reading.power, " W")}</td>
            <td>${device.active_vehicle ? device.active_vehicle.license_plate : "No active charging"}</td>
            <td>${device.assigned_vehicle ? device.assigned_vehicle.license_plate : "--"}</td>
            <td>${formatTime(device.last_seen_at)}</td>
          </tr>
        `;
      })
      .join("");
  }

  function renderAlerts() {
    if (!state.alerts.length) {
      alertTableBody.innerHTML = '<tr><td colspan="4">No alerts yet.</td></tr>';
      return;
    }

    alertTableBody.innerHTML = state.alerts
      .map(function (alert) {
        return `
          <tr>
            <td>${formatTime(alert.created_at)}</td>
            <td>${alert.type}</td>
            <td>${alert.message}</td>
            <td>${alert.measured_value}</td>
          </tr>
        `;
      })
      .join("");
  }

  function renderHistoryChart() {
    if (!state.history.length) {
      adminHistoryChart.innerHTML = '<p class="message">No history for the selected station yet.</p>';
      return;
    }

    const width = 760;
    const height = 220;
    const padding = 18;
    const values = state.history.map(function (item) {
      return item.current;
    });
    const max = Math.max.apply(null, values);
    const min = Math.min.apply(null, values);
    const range = Math.max(max - min, 1);

    const points = state.history
      .slice()
      .reverse()
      .map(function (item, index, array) {
        const x = padding + ((width - padding * 2) / Math.max(array.length - 1, 1)) * index;
        const y = height - padding - ((item.current - min) / range) * (height - padding * 2);
        return `${x},${y}`;
      })
      .join(" ");

    adminHistoryChart.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        <polyline fill="none" stroke="#0d5c74" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" points="${points}" />
      </svg>
    `;
  }

  async function loadDeviceHistory() {
    const deviceCode = deviceHistoryFilter.value;
    if (!deviceCode) {
      state.history = [];
      renderHistoryChart();
      return;
    }

    const response = await window.AppApi.get(`/api/admin/history?device_code=${encodeURIComponent(deviceCode)}`);
    state.history = response.items || [];
    renderHistoryChart();
  }

  async function loadAll() {
    adminWelcomeMessage.textContent = `Signed in as ${currentUser.email}`;
    const [users, devices, alerts, settings] = await Promise.all([
      window.AppApi.get("/api/admin/users"),
      window.AppApi.get("/api/admin/devices"),
      window.AppApi.get("/api/admin/alerts"),
      window.AppApi.get("/api/admin/settings"),
    ]);

    state.users = users.items || [];
    state.devices = devices.items || [];
    state.alerts = alerts.items || [];
    state.settings = settings;

    minCurrentInput.value = settings.min_current_ma;
    detectionCurrentInput.value = settings.charging_detection_current_ma;
    maxCurrentInput.value = settings.max_current_ma;
    deviceHistoryFilter.innerHTML = state.devices
      .map(function (device) {
        return `<option value="${device.device_code}">${device.device_code}</option>`;
      })
      .join("");

    renderOverview();
    renderUsers();
    renderDevices();
    renderAlerts();
    await loadDeviceHistory();
  }

  document.getElementById("saveSettingsButton").addEventListener("click", async function () {
    try {
      const updated = await window.AppApi.put("/api/admin/settings", {
        min_current_ma: Number(minCurrentInput.value),
        charging_detection_current_ma: Number(detectionCurrentInput.value),
        max_current_ma: Number(maxCurrentInput.value),
      });
      state.settings = updated;
      settingsMessage.textContent = "Settings saved.";
      settingsMessage.className = "message success";
      renderOverview();
    } catch (error) {
      settingsMessage.textContent = error.message;
      settingsMessage.className = "message error";
    }
  });

  document.getElementById("assignVehicleButton").addEventListener("click", async function () {
    try {
      await window.AppApi.post("/api/admin/vehicles/assign", {
        user_id: Number(assignmentUser.value),
        license_plate: assignmentPlate.value.trim(),
        device_code: assignmentDevice.value.trim(),
        display_name: assignmentDisplayName.value.trim(),
      });
      assignmentMessage.textContent = "Vehicle assigned.";
      assignmentMessage.className = "message success";
      await loadAll();
    } catch (error) {
      assignmentMessage.textContent = error.message;
      assignmentMessage.className = "message error";
    }
  });

  document.getElementById("adminRefreshButton").addEventListener("click", loadAll);
  deviceHistoryFilter.addEventListener("change", loadDeviceHistory);
  document.getElementById("adminLogoutButton").addEventListener("click", function () {
    window.AppAuth.clearSession();
    window.location.href = "login.html";
  });

  const socket = window.AppSocket.connect({
    connected: function () {
      adminSocketStatus.textContent = "Socket connected";
      adminSocketStatus.className = "status-pill online";
    },
    "sensor:update:admin": function () {
      loadAll();
    },
    "alert:new": function () {
      loadAll();
    },
    "device:status": function () {
      loadAll();
    },
  });

  if (!socket) {
    adminSocketStatus.textContent = "Socket unavailable";
    adminSocketStatus.className = "status-pill offline";
  }

  loadAll();
})();
