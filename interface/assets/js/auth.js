(function () {
  function saveSession(payload) {
    window.localStorage.setItem("accessToken", payload.access_token);
    window.localStorage.setItem("currentUser", JSON.stringify(payload.user));
  }

  function getCurrentUser() {
    const raw = window.localStorage.getItem("currentUser");
    return raw ? JSON.parse(raw) : null;
  }

  function clearSession() {
    window.localStorage.removeItem("accessToken");
    window.localStorage.removeItem("currentUser");
  }

  function redirectByRole() {
    const user = getCurrentUser();

    if (!user) {
      window.location.href = "login.html";
      return;
    }

    window.location.href = user.role === "admin" ? "admin-dashboard.html" : "user-dashboard.html";
  }

  function requireRole(expectedRole) {
    const token = window.localStorage.getItem("accessToken");
    const user = getCurrentUser();

    if (!token || !user) {
      window.location.href = "login.html";
      return null;
    }

    if (expectedRole && user.role !== expectedRole) {
      redirectByRole();
      return null;
    }

    return user;
  }

  window.AppAuth = {
    saveSession,
    getCurrentUser,
    clearSession,
    redirectByRole,
    requireRole,
  };
})();
