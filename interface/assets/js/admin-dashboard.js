(function () {
  const currentUser = window.AppAuth.requireRole("admin");
  if (!currentUser) {
    return;
  }

  const adminWelcomeMessage = document.getElementById("adminWelcomeMessage");
  const overviewMetrics = document.getElementById("overviewMetrics");
  const deviceCards = document.getElementById("deviceCards");
  const deviceTableBody = document.getElementById("deviceTableBody");
  const stationCharts = document.getElementById("stationCharts");
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
  const adminCriticalAlert = document.getElementById("adminCriticalAlert");
  const adminToastStack = document.getElementById("adminToastStack");

  let state = { devices: [], alerts: [], users: [], settings: null, historyByDevice: {} };

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

  function isCriticalAlert(alert) {
    return Boolean(alert && alert.type);
  }

  function findUserEmail(userId) {
    const user = state.users.find(function (item) {
      return item.id === userId;
    });
    return user ? user.email : "Chua xac dinh chu xe";
  }

  function findVehicleForDevice(device) {
    return device.active_vehicle || device.assigned_vehicle || null;
  }

  function latestAlertForDevice(deviceId) {
    return state.alerts.find(function (alert) {
      return alert.device_id === deviceId;
    }) || null;
  }

  function buildCriticalDeviceContext(device) {
    const vehicle = findVehicleForDevice(device);
    const latestAlert = latestAlertForDevice(device.id);
    const reading = device.latest_reading || {};

    return {
      label: device.name || device.device_code,
      deviceCode: device.device_code,
      plateLabel: vehicle ? vehicle.license_plate : "Chua co bien so dang sac",
      ownerLabel: vehicle ? findUserEmail(vehicle.user_id) : "Chua co chu so huu",
      currentLabel: formatNumber(reading.current, " A"),
      alertMessage: latestAlert ? latestAlert.message : "He thong vua dua thiet bi vao trang thai abnormal.",
      updatedAt: formatTime((latestAlert && latestAlert.created_at) || reading.timestamp || device.last_seen_at),
    };
  }

  function renderCriticalBanner() {
    const abnormalDevices = state.devices.filter(function (device) {
      return device.status === "abnormal";
    });

    if (!abnormalDevices.length) {
      adminCriticalAlert.className = "alert-spotlight hidden";
      adminCriticalAlert.innerHTML = "";
      return;
    }

    adminCriticalAlert.className = "alert-spotlight";
    adminCriticalAlert.innerHTML = `
      <div class="alert-spotlight-kicker">Abnormal detected</div>
      <h2>Canh bao do: co ${abnormalDevices.length} thiet bi dang abnormal.</h2>
      <p>Kiem tra ngay tram sac, bien so dang gan, va nguoi so huu de xu ly su co.</p>
      <div class="alert-spotlight-grid">
        ${abnormalDevices
          .map(function (device) {
            const context = buildCriticalDeviceContext(device);
            return `
              <article class="alert-spotlight-card">
                <strong>${context.label}</strong>
                <p>${context.alertMessage}</p>
                <div class="alert-spotlight-meta">
                  <span><strong>Device:</strong> ${context.deviceCode}</span>
                  <span><strong>Plate:</strong> ${context.plateLabel}</span>
                  <span><strong>Owner:</strong> ${context.ownerLabel}</span>
                  <span><strong>Current:</strong> ${context.currentLabel}</span>
                  <span><strong>Updated:</strong> ${context.updatedAt}</span>
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    `;
  }

  function pushCriticalToast(context) {
    if (!context) {
      return;
    }

    const toast = document.createElement("article");
    toast.className = "toast toast-critical";
    toast.innerHTML = `
      <h3 class="toast-title">ABNORMAL DETECTED</h3>
      <div class="toast-lines">
        <span>Device: ${context.deviceCode}</span>
        <span>Plate: ${context.plateLabel}</span>
        <span>Owner: ${context.ownerLabel}</span>
        <span>${context.alertMessage}</span>
      </div>
    `;
    adminToastStack.prepend(toast);

    window.setTimeout(function () {
      toast.remove();
    }, 7000);
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
          <article class="vehicle-card${device.status === "abnormal" ? " is-critical" : ""}">
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
                <div class="metric-value">${formatNumber(reading.current, " A")}</div>
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
          <tr class="${device.status === "abnormal" ? "alert-row-critical" : ""}">
            <td>${device.device_code}</td>
            <td>${renderStatus(device.status)}</td>
            <td>${formatNumber(reading.current, " A")}</td>
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
          <tr class="${isCriticalAlert(alert) ? "alert-row-critical" : ""}">
            <td>${formatTime(alert.created_at)}</td>
            <td>${alert.type}</td>
            <td>${alert.message}</td>
            <td>${alert.measured_value}</td>
          </tr>
        `;
      })
      .join("");
  }

  function renderMetricChart(historyItems, valueKey, unitLabel, strokeColor) {
    if (!historyItems.length) {
      return '<div class="chart-surface compact"><p class="message">No history yet.</p></div>';
    }

    const width = 720;
    const height = 240;
    const paddingLeft = 52;
    const paddingRight = 18;
    const paddingTop = 18;
    const paddingBottom = 34;
    const plotWidth = width - paddingLeft - paddingRight;
    const plotHeight = height - paddingTop - paddingBottom;
    const orderedItems = historyItems.slice().reverse();
    const values = orderedItems.map(function (item) {
      return Number(item[valueKey] || 0);
    });
    const max = Math.max.apply(null, values);
    const min = Math.min.apply(null, values);
    const range = Math.max(max - min, 1);
    const latestValue = values[values.length - 1];
    const rowCount = 4;
    const colCount = Math.min(5, Math.max(2, orderedItems.length));
    const highlightIndexes = {
      latest: values.length - 1,
      min: values.indexOf(min),
      max: values.indexOf(max),
    };
    const plottedPoints = orderedItems.map(function (item, index, array) {
      const value = Number(item[valueKey] || 0);
      const x = paddingLeft + (plotWidth / Math.max(array.length - 1, 1)) * index;
      const y = paddingTop + plotHeight - ((value - min) / range) * plotHeight;
      return {
        x,
        y,
        value,
        timestamp: item.timestamp,
        isLatest: index === array.length - 1,
        isMin: value === min,
        isMax: value === max,
      };
    });
    const pointList = plottedPoints.map(function (point) {
      return `${point.x},${point.y}`;
    }).join(" ");
    const pointMarkers = plottedPoints.map(function (point) {
      const classes = ["chart-point"];
      let fillColor = strokeColor;
      if (point.isLatest) {
        classes.push("latest");
        fillColor = "#19d3c5";
      } else if (point.isMax) {
        classes.push("max");
        fillColor = "#d1495b";
      } else if (point.isMin) {
        classes.push("min");
        fillColor = "#d98a00";
      }
      const timeLabel = point.timestamp
        ? new Date(point.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        : "--:--";
      return `
        <circle class="${classes.join(" ")}" cx="${point.x}" cy="${point.y}" r="${point.isLatest ? 5 : 3.5}" fill="${fillColor}">
          <title>${timeLabel} - ${point.value.toFixed(1)} ${unitLabel}</title>
        </circle>
      `;
    }).join("");
    const labelConfigs = [
      { key: "latest", text: `Latest ${latestValue.toFixed(1)} ${unitLabel}` },
      { key: "max", text: `Max ${max.toFixed(1)} ${unitLabel}` },
      { key: "min", text: `Min ${min.toFixed(1)} ${unitLabel}` },
    ];
    const seenLabelIndexes = new Set();
    const pointLabels = labelConfigs.map(function (config) {
      const index = highlightIndexes[config.key];
      if (index === undefined || seenLabelIndexes.has(index)) {
        return "";
      }
      seenLabelIndexes.add(index);
      const point = plottedPoints[index];
      const textX = Math.min(width - paddingRight - 70, point.x + 10);
      const textY = Math.max(paddingTop + 14, point.y - 10);
      return `<text x="${textX}" y="${textY}" class="chart-point-label">${config.text}</text>`;
    }).join("");

    const horizontalGrid = Array.from({ length: rowCount + 1 }, function (_unused, index) {
      const y = paddingTop + (plotHeight / rowCount) * index;
      const value = max - ((max - min) / rowCount) * index;
      return `
        <line x1="${paddingLeft}" y1="${y}" x2="${width - paddingRight}" y2="${y}" class="chart-grid-line"></line>
        <text x="${paddingLeft - 10}" y="${y + 4}" text-anchor="end" class="chart-axis-label">${value.toFixed(1)}</text>
      `;
    }).join("");

    const verticalGrid = Array.from({ length: colCount }, function (_unused, index) {
      const x = paddingLeft + (plotWidth / Math.max(colCount - 1, 1)) * index;
      const itemIndex = Math.min(
        orderedItems.length - 1,
        Math.round((orderedItems.length - 1) * (index / Math.max(colCount - 1, 1)))
      );
      const item = orderedItems[itemIndex];
      const label = item && item.timestamp
        ? new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        : "--:--";
      return `
        <line x1="${x}" y1="${paddingTop}" x2="${x}" y2="${paddingTop + plotHeight}" class="chart-grid-line vertical"></line>
        <text x="${x}" y="${height - 10}" text-anchor="middle" class="chart-axis-label">${label}</text>
      `;
    }).join("");

    return `
      <div class="chart-legend">
        <span class="chart-legend-item"><i class="chart-legend-dot" style="background:${strokeColor}"></i>Series</span>
        <span class="chart-legend-item"><i class="chart-legend-dot latest"></i>Latest</span>
        <span class="chart-legend-item"><i class="chart-legend-dot max"></i>Max</span>
        <span class="chart-legend-item"><i class="chart-legend-dot min"></i>Min</span>
      </div>
      <div class="chart-summary">
        <span class="chart-summary-item"><strong>Latest:</strong> ${latestValue.toFixed(1)} ${unitLabel}</span>
        <span class="chart-summary-item"><strong>Min:</strong> ${min.toFixed(1)} ${unitLabel}</span>
        <span class="chart-summary-item"><strong>Max:</strong> ${max.toFixed(1)} ${unitLabel}</span>
      </div>
      <div class="chart-surface compact">
        <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
          ${horizontalGrid}
          ${verticalGrid}
          <line x1="${paddingLeft}" y1="${paddingTop + plotHeight}" x2="${width - paddingRight}" y2="${paddingTop + plotHeight}" class="chart-axis-line"></line>
          <line x1="${paddingLeft}" y1="${paddingTop}" x2="${paddingLeft}" y2="${paddingTop + plotHeight}" class="chart-axis-line"></line>
          <polyline fill="none" stroke="${strokeColor}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" points="${pointList}" />
          ${pointMarkers}
          ${pointLabels}
          <text x="${paddingLeft - 28}" y="${paddingTop - 2}" text-anchor="start" class="chart-unit-label">${unitLabel}</text>
          <text x="${width - paddingRight}" y="${height - 10}" text-anchor="end" class="chart-unit-label">Minute</text>
        </svg>
      </div>
    `;
  }

  function renderStationCharts() {
    if (!state.devices.length) {
      stationCharts.innerHTML = '<div class="vehicle-card"><p class="message">No station charts available yet.</p></div>';
      return;
    }

    stationCharts.innerHTML = state.devices
      .map(function (device) {
        const historyItems = state.historyByDevice[device.device_code] || [];
        return `
          <article class="station-chart-card">
            <div class="row" style="justify-content: space-between; align-items: center">
              <div>
                <h3>${device.name || device.device_code}</h3>
                <p class="subtle">${device.device_code}</p>
              </div>
              ${renderStatus(device.status)}
            </div>
            <div class="station-chart-grid">
              <section>
                <h4>Current (A)</h4>
                ${renderMetricChart(historyItems, "current", "A", "#0fb98b")}
              </section>
              <section>
                <h4>Voltage (V)</h4>
                ${renderMetricChart(historyItems, "voltage", "V", "#0d5c74")}
              </section>
            </div>
          </article>
        `;
      })
      .join("");
  }

  async function loadDeviceHistories() {
    const historyResponses = await Promise.all(
      state.devices.map(function (device) {
        return window.AppApi
          .get(`/api/admin/history?device_code=${encodeURIComponent(device.device_code)}`)
          .then(function (response) {
            return { deviceCode: device.device_code, items: response.items || [] };
          });
      })
    );

    state.historyByDevice = {};
    historyResponses.forEach(function (entry) {
      state.historyByDevice[entry.deviceCode] = entry.items;
    });
    renderStationCharts();
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

    renderOverview();
    renderUsers();
    renderDevices();
    renderAlerts();
    renderCriticalBanner();
    await loadDeviceHistories();
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
    "alert:new": async function (alert) {
      await loadAll();
      if (alert && alert.device_id) {
        const device = state.devices.find(function (item) {
          return item.id === alert.device_id;
        });
        pushCriticalToast(device ? buildCriticalDeviceContext(device) : null);
      }
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
