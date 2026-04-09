(function () {
  function connect(eventHandlers) {
    if (typeof window.io !== "function") {
      return null;
    }

    const token = window.localStorage.getItem("accessToken");
    if (!token) {
      return null;
    }

    const socket = window.io(window.AppApi.baseUrl, {
      query: { token },
      transports: ["websocket"],
    });

    Object.entries(eventHandlers || {}).forEach(([eventName, handler]) => {
      socket.on(eventName, handler);
    });

    return socket;
  }

  window.AppSocket = { connect };
})();
