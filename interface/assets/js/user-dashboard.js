(function () {
  const currentUser = window.AppAuth.requireRole("user");
  if (!currentUser) {
    return;
  }

  const welcomeMessage = document.getElementById("welcomeMessage");
  const vehicleFilter = document.getElementById("vehicleFilter");
  const vehicleCards = document.getElementById("vehicleCards");
  const userHistoryCharts = document.getElementById("userHistoryCharts");
  const snapshotMetrics = document.getElementById("snapshotMetrics");
  const paymentHistoryBody = document.getElementById("paymentHistoryBody");
  const alertList = document.getElementById("alertList");
  const socketStatus = document.getElementById("socketStatus");
  const userCriticalAlert = document.getElementById("userCriticalAlert");
  const userToastStack = document.getElementById("userToastStack");

  let dashboardState = { vehicles: [], alerts: [], history: [], payments: [] };

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

  function isCriticalAlert(alert) {
    return Boolean(alert && alert.type);
  }

  function findVehicleById(vehicleId) {
    return dashboardState.vehicles.find(function (vehicle) {
      return vehicle.id === vehicleId;
    }) || null;
  }

  function buildCriticalVehicleContext(vehicle) {
    const reading = vehicle && vehicle.latest_reading ? vehicle.latest_reading : {};
    const latestAlert = vehicle && vehicle.latest_alert
      ? vehicle.latest_alert
      : dashboardState.alerts.find(function (alert) {
          return vehicle && alert.vehicle_id === vehicle.id;
        }) || null;

    return {
      plateLabel: vehicle ? vehicle.license_plate : "Khong ro bien so",
      deviceCode: reading.device_code || "--",
      currentLabel: formatNumber(reading.current, " A"),
      alertMessage: latestAlert ? latestAlert.message : "Xe cua ban dang o trang thai abnormal.",
      updatedAt: formatTime((latestAlert && latestAlert.created_at) || reading.timestamp),
    };
  }

  function renderCriticalBanner() {
    const abnormalVehicles = dashboardState.vehicles.filter(function (vehicle) {
      return vehicle.status === "abnormal";
    });

    if (!abnormalVehicles.length) {
      userCriticalAlert.className = "alert-spotlight hidden";
      userCriticalAlert.innerHTML = "";
      return;
    }

    userCriticalAlert.className = "alert-spotlight";
    userCriticalAlert.innerHTML = `
      <div class="alert-spotlight-kicker">Xe cua ban dang canh bao</div>
      <h2>Canh bao do: phat hien abnormal tren bien so cua ban.</h2>
      <p>Ngat sac va kiem tra thiet bi ngay neu dong dien dang vuot nguong an toan.</p>
      <div class="alert-spotlight-grid">
        ${abnormalVehicles
          .map(function (vehicle) {
            const context = buildCriticalVehicleContext(vehicle);
            return `
              <article class="alert-spotlight-card">
                <strong>${context.plateLabel}</strong>
                <p>${context.alertMessage}</p>
                <div class="alert-spotlight-meta">
                  <span><strong>Device:</strong> ${context.deviceCode}</span>
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

  function pushCriticalToast(alert) {
    const vehicle = findVehicleById(alert && alert.vehicle_id);
    const context = buildCriticalVehicleContext(vehicle);
    const toast = document.createElement("article");
    toast.className = "toast toast-critical";
    toast.innerHTML = `
      <h3 class="toast-title">ABNORMAL DETECTED</h3>
      <div class="toast-lines">
        <span>Plate: ${context.plateLabel}</span>
        <span>Device: ${context.deviceCode}</span>
        <span>${context.alertMessage}</span>
      </div>
    `;
    userToastStack.prepend(toast);

    window.setTimeout(function () {
      toast.remove();
    }, 7000);
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
          <article class="vehicle-card${status === "abnormal" ? " is-critical" : ""}">
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
                <div class="metric-value">${formatNumber(reading.current, " A")}</div>
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
      <div class="metric-card${selectedVehicle && selectedVehicle.status === "abnormal" ? " metric-card-critical" : ""}">
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
          <article class="alert-item${isCriticalAlert(alert) ? " is-critical" : ""}">
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

  function renderPaymentHistory() {
    if (!dashboardState.payments.length) {
      paymentHistoryBody.innerHTML = '<tr><td colspan="7">No completed charging session yet.</td></tr>';
      return;
    }

    paymentHistoryBody.innerHTML = dashboardState.payments
      .map(function (session) {
        return `
          <tr>
            <td>${session.license_plate || "--"}</td>
            <td>${session.device_code || "--"}</td>
            <td>${formatTime(session.started_at)}</td>
            <td>${formatTime(session.ended_at)}</td>
            <td>${formatNumber(session.duration_minutes, " min")}</td>
            <td>${formatNumber(session.energy_kwh, " kWh")}</td>
            <td>${formatNumber(session.total_vnd, " VND")}</td>
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

  function renderHistoryChart() {
    if (!dashboardState.history.length) {
      userHistoryCharts.innerHTML = '<div class="chart-surface compact"><p class="message">No history for the selected plate yet.</p></div>';
      return;
    }

    userHistoryCharts.innerHTML = `
      <section>
        <h3>Current (A)</h3>
        ${renderMetricChart(dashboardState.history, "current", "A", "#0fb98b")}
      </section>
      <section>
        <h3>Voltage (V)</h3>
        ${renderMetricChart(dashboardState.history, "voltage", "V", "#0d5c74")}
      </section>
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
    const [dashboard, alerts, payments] = await Promise.all([
      window.AppApi.get("/api/user/dashboard"),
      window.AppApi.get("/api/user/alerts"),
      window.AppApi.get("/api/user/payment-history"),
    ]);
    dashboardState.vehicles = dashboard.vehicles || [];
    dashboardState.alerts = alerts.items || [];
    dashboardState.payments = payments.items || [];

    vehicleFilter.innerHTML = dashboardState.vehicles
      .map(function (vehicle) {
        return `<option value="${vehicle.license_plate}">${vehicle.license_plate}</option>`;
      })
      .join("");

    renderVehicleCards();
    renderSnapshot();
    renderAlerts();
    renderCriticalBanner();
    renderPaymentHistory();
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
          renderCriticalBanner();
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
        const target = findVehicleById(alert.vehicle_id);
        if (target) {
          target.latest_alert = alert;
          target.status = "abnormal";
        }
        renderAlerts();
        renderVehicleCards();
        renderSnapshot();
        renderCriticalBanner();
        pushCriticalToast(alert);
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
