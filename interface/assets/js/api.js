(function () {
  function getBaseUrl() {
    return window.localStorage.getItem("apiBaseUrl") || "http://127.0.0.1:5000";
  }

  function buildHeaders(extraHeaders) {
    const token = window.localStorage.getItem("accessToken");
    const headers = {
      "Content-Type": "application/json",
      ...extraHeaders,
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return headers;
  }

  async function request(path, options) {
    const response = await fetch(`${getBaseUrl()}${path}`, {
      ...options,
      headers: buildHeaders(options && options.headers),
    });

    const text = await response.text();
    const body = text ? JSON.parse(text) : {};

    if (!response.ok) {
      const error = new Error(body.error || "Request failed");
      error.status = response.status;
      error.body = body;
      throw error;
    }

    return body;
  }

  window.AppApi = {
    get baseUrl() {
      return getBaseUrl();
    },
    setBaseUrl(nextBaseUrl) {
      window.localStorage.setItem("apiBaseUrl", nextBaseUrl);
    },
    get(path) {
      return request(path, { method: "GET" });
    },
    post(path, payload) {
      return request(path, {
        method: "POST",
        body: JSON.stringify(payload || {}),
      });
    },
    put(path, payload) {
      return request(path, {
        method: "PUT",
        body: JSON.stringify(payload || {}),
      });
    },
  };
})();
