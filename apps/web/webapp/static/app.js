(function () {
  const templates = window.APP_BOOTSTRAP.templates;
  const themeOptions = window.APP_BOOTSTRAP.themeOptions || [];
  const protocolVersionOptions = window.APP_BOOTSTRAP.protocolVersionOptions || [];
  const CLIENT_SESSION_STORAGE_KEY = "mcp-demo-client-session-id";
  const THEME_STORAGE_KEY = "mcp-demo-theme";
  const VIEW_STORAGE_KEY = "mcp-demo-active-view";
  const WELCOME_MODAL_DISMISS_STORAGE_KEY = "mcp-demo-hide-welcome-modal";
  const DEFAULT_THEME = window.APP_BOOTSTRAP.defaultTheme || "neo-brutalism";
  const DEFAULT_PROTOCOL_VERSION =
    window.APP_BOOTSTRAP.defaultProtocolVersion || "2025-11-25";

  const elements = {
    targetUrl: document.getElementById("target-url"),
    transportMode: document.getElementById("transport-mode"),
    protocolVersion: document.getElementById("protocol-version"),
    clientTab: document.getElementById("client-tab"),
    serverTab: document.getElementById("server-tab"),
    themeTab: document.getElementById("theme-tab"),
    clientView: document.getElementById("client-view"),
    serverView: document.getElementById("server-view"),
    themeView: document.getElementById("theme-view"),
    connectButton: document.getElementById("connect-button"),
    disconnectButton: document.getElementById("disconnect-button"),
    connectionState: document.getElementById("connection-state"),
    actionGroups: document.getElementById("action-groups"),
    templateDescription: document.getElementById("template-description"),
    requestEditor: document.getElementById("request-editor"),
    requestError: document.getElementById("request-error"),
    requestMeta: document.getElementById("request-meta"),
    formatButton: document.getElementById("format-button"),
    sendButton: document.getElementById("send-button"),
    responseViewer: document.getElementById("response-viewer"),
    responseError: document.getElementById("response-error"),
    protocolVersionDisplay: document.getElementById("protocol-version-display"),
    sessionTokenDisplay: document.getElementById("session-token-display"),
    serverTransportMode: document.getElementById("server-transport-mode"),
    serverProtocolVersion: document.getElementById("server-protocol-version"),
    serverHost: document.getElementById("server-host"),
    serverPort: document.getElementById("server-port"),
    serverStartButton: document.getElementById("server-start-button"),
    serverStopButton: document.getElementById("server-stop-button"),
    serverRestartButton: document.getElementById("server-restart-button"),
    serverRefreshButton: document.getElementById("server-refresh-button"),
    serverResetLogsButton: document.getElementById("server-reset-logs-button"),
    serverState: document.getElementById("server-state"),
    serverStatusTransport: document.getElementById("server-status-transport"),
    serverStatusVersion: document.getElementById("server-status-version"),
    serverStatusPid: document.getElementById("server-status-pid"),
    serverStatusUptime: document.getElementById("server-status-uptime"),
    serverStatusEndpoint: document.getElementById("server-status-endpoint"),
    serverStatusError: document.getElementById("server-status-error"),
    serverLogsViewer: document.getElementById("server-logs-viewer"),
    themeOptionsList: document.getElementById("theme-options-list"),
    welcomeModal: document.getElementById("welcome-modal"),
    welcomeDismissToggle: document.getElementById("welcome-dismiss-toggle"),
    welcomeModalOk: document.getElementById("welcome-modal-ok"),
  };

  let isConnected = false;
  let activeServerStatus = null;
  let serverStatusPollHandle = null;
  let serverStatusPollTick = 0;

  function createClientSessionId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }

    const randomPart = Math.random().toString(36).slice(2, 12);
    const timePart = Date.now().toString(36);
    return `session-${timePart}-${randomPart}`;
  }

  function getClientSessionId() {
    const existing = window.localStorage.getItem(CLIENT_SESSION_STORAGE_KEY);
    if (existing) {
      return existing;
    }
    const created = createClientSessionId();
    window.localStorage.setItem(CLIENT_SESSION_STORAGE_KEY, created);
    return created;
  }

  function getStoredTheme() {
    return window.localStorage.getItem(THEME_STORAGE_KEY);
  }

  function getStoredView() {
    return window.localStorage.getItem(VIEW_STORAGE_KEY);
  }

  function setStoredTheme(theme) {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }

  function setStoredView(view) {
    window.localStorage.setItem(VIEW_STORAGE_KEY, view);
  }

  function shouldPresentWelcomeModal() {
    return window.localStorage.getItem(WELCOME_MODAL_DISMISS_STORAGE_KEY) !== "true";
  }

  function setWelcomeModalDismissed(shouldDismiss) {
    window.localStorage.setItem(
      WELCOME_MODAL_DISMISS_STORAGE_KEY,
      shouldDismiss ? "true" : "false"
    );
  }

  function isSupportedTheme(theme) {
    return themeOptions.some((option) => option.id === theme);
  }

  function applyTheme(theme) {
    const nextTheme = isSupportedTheme(theme) ? theme : DEFAULT_THEME;
    document.body.dataset.theme = nextTheme;
    syncThemeButtons(nextTheme);
    syncFortinetEmptyControls();
    return nextTheme;
  }

  function syncFortinetEmptyControls() {
    document.querySelectorAll("input, select, textarea").forEach((control) => {
      const value =
        typeof control.value === "string" ? control.value.trim() : String(control.value || "");
      control.classList.toggle("fortinet-empty-control", value === "");
    });
  }

  function getTargetEndpoint() {
    return elements.targetUrl.value.trim();
  }

  function getTransportLabel(transport) {
    if (transport === "streamable-http") {
      return "Streamable HTTP";
    }
    if (transport === "sse") {
      return "SSE";
    }
    return transport || "Unknown";
  }

  function getProtocolVersion() {
    return elements.protocolVersion.value;
  }

  function syncActionButtons() {
    elements.connectButton.disabled = isConnected;
    elements.disconnectButton.disabled = !isConnected;
    elements.sendButton.disabled = !isConnected;
    elements.targetUrl.disabled = isConnected;
    elements.transportMode.disabled = isConnected;
    elements.protocolVersion.disabled = isConnected;
  }

  function setActiveView(view) {
    const nextView = ["client", "server", "theme"].includes(view) ? view : "client";
    elements.clientTab.classList.toggle("active", nextView === "client");
    elements.serverTab.classList.toggle("active", nextView === "server");
    elements.themeTab.classList.toggle("active", nextView === "theme");
    elements.clientView.classList.toggle("hidden", nextView !== "client");
    elements.serverView.classList.toggle("hidden", nextView !== "server");
    elements.themeView.classList.toggle("hidden", nextView !== "theme");
    setStoredView(nextView);
    if (nextView === "server") {
      startServerStatusPolling();
    } else {
      stopServerStatusPolling();
    }
  }

  function formatElapsedUptime(startedAt) {
    if (!startedAt) {
      return "n/a";
    }
    const started =
      typeof startedAt === "number" ? startedAt : new Date(startedAt).getTime();
    if (Number.isNaN(started)) {
      return "n/a";
    }
    const elapsed = Math.max(0, Math.floor((Date.now() - started) / 1000));
    const hours = String(Math.floor(elapsed / 3600)).padStart(2, "0");
    const minutes = String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0");
    const seconds = String(elapsed % 60).padStart(2, "0");
    return `${hours}:${minutes}:${seconds}`;
  }

  function parseUptimeToSeconds(uptime) {
    if (!uptime || typeof uptime !== "string") {
      return null;
    }
    const parts = uptime.split(":").map((part) => Number(part));
    if (parts.length !== 3 || parts.some((value) => Number.isNaN(value))) {
      return null;
    }
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  }

  function getServerStartedAtMs(runtime) {
    if (!runtime) {
      return null;
    }
    if (typeof runtime.started_at_ms === "number") {
      return runtime.started_at_ms;
    }
    if (runtime.started_at) {
      const parsed = new Date(runtime.started_at).getTime();
      if (!Number.isNaN(parsed)) {
        runtime.started_at_ms = parsed;
        return parsed;
      }
    }
    const uptimeSeconds = parseUptimeToSeconds(runtime.uptime);
    if (uptimeSeconds !== null) {
      runtime.started_at_ms = Date.now() - uptimeSeconds * 1000;
      return runtime.started_at_ms;
    }
    return null;
  }

  function syncServerUptime() {
    if (!activeServerStatus || !activeServerStatus.running) {
      return;
    }
    const startedAtMs = getServerStartedAtMs(activeServerStatus);
    elements.serverStatusUptime.textContent =
      formatElapsedUptime(startedAtMs) || activeServerStatus.uptime || "n/a";
  }

  function startServerStatusPolling() {
    stopServerStatusPolling();
    serverStatusPollTick = 0;
    serverStatusPollHandle = window.setInterval(() => {
      serverStatusPollTick += 1;
      syncServerUptime();
      if (serverStatusPollTick % 5 === 0) {
        refreshServerStatus();
      }
    }, 1000);
    syncServerUptime();
  }

  function stopServerStatusPolling() {
    if (serverStatusPollHandle) {
      window.clearInterval(serverStatusPollHandle);
      serverStatusPollHandle = null;
    }
  }

  function syncThemeButtons(activeTheme) {
    if (!elements.themeOptionsList) {
      return;
    }
    elements.themeOptionsList.querySelectorAll(".theme-action-button").forEach((button) => {
      button.classList.toggle("active", button.dataset.themeId === activeTheme);
    });
  }

  function showWelcomeModal() {
    if (!elements.welcomeModal) {
      return;
    }
    elements.welcomeDismissToggle.checked = !shouldPresentWelcomeModal();
    elements.welcomeModal.classList.remove("hidden");
  }

  function hideWelcomeModal() {
    if (!elements.welcomeModal) {
      return;
    }
    elements.welcomeModal.classList.add("hidden");
  }

  function groupTemplates(items) {
    const groups = new Map();
    items.forEach((item) => {
      if (!groups.has(item.category)) {
        groups.set(item.category, []);
      }
      groups.get(item.category).push(item);
    });
    return groups;
  }

  function renderActionGroups() {
    const grouped = groupTemplates(templates);
    grouped.forEach((groupTemplatesList, category) => {
      const section = document.createElement("details");
      section.className = "action-section";

      const summary = document.createElement("summary");
      summary.className = "action-summary";
      summary.textContent = category;
      section.appendChild(summary);

      const list = document.createElement("div");
      list.className = "action-list";

      groupTemplatesList.forEach((template) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "action-button";
        button.textContent = template.label;
        button.title = template.description;
        button.dataset.templateId = template.id;
        button.addEventListener("click", () => populateTemplate(template.id));
        list.appendChild(button);
      });

      section.appendChild(list);
      elements.actionGroups.appendChild(section);
    });
  }

  function renderThemeOptions() {
    themeOptions.forEach((themeOption) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "action-button theme-action-button";
      button.textContent = themeOption.label;
      button.dataset.themeId = themeOption.id;
      button.addEventListener("click", () => {
        const nextTheme = applyTheme(themeOption.id);
        setStoredTheme(nextTheme);
      });
      elements.themeOptionsList.appendChild(button);
    });
  }

  function findTemplate(templateId) {
    return templates.find((item) => item.id === templateId);
  }

  function formatJson(value) {
    return JSON.stringify(value, null, 2);
  }

  function setConnectionState(state, message) {
    elements.connectionState.className = "status-badge";
    if (state === "connected") {
      elements.connectionState.classList.add("connected");
      elements.connectionState.textContent = "Connected";
    } else if (state === "error") {
      elements.connectionState.classList.add("error");
      elements.connectionState.textContent = "Disconnected";
    } else {
      elements.connectionState.classList.add("disconnected");
      elements.connectionState.textContent = "Disconnected";
    }
    elements.connectionState.title = message;
  }

  function setResponse(payload) {
    elements.responseViewer.textContent = formatJson(payload);
  }

  function showRequestError(message) {
    elements.requestError.textContent = message;
    elements.requestError.classList.remove("hidden");
  }

  function clearRequestError() {
    elements.requestError.textContent = "";
    elements.requestError.classList.add("hidden");
  }

  function showResponseError(message) {
    elements.responseError.textContent = message;
    elements.responseError.classList.remove("hidden");
  }

  function clearResponseError() {
    elements.responseError.textContent = "";
    elements.responseError.classList.add("hidden");
  }

  function updateRequestMeta(message) {
    elements.requestMeta.textContent = message;
  }

  function setProtocolVersion(version) {
    if (!elements.protocolVersionDisplay) {
      return;
    }
    elements.protocolVersionDisplay.querySelector(".meta-value").textContent = version || "unknown";
  }

  function setSessionToken(token) {
    elements.sessionTokenDisplay.querySelector(".meta-value").textContent = token || "unknown";
  }

  function applyDisconnectedUi(message) {
    isConnected = false;
    setConnectionState("neutral", message || "Disconnected.");
    setProtocolVersion(null);
    setSessionToken(null);
    syncActionButtons();
  }

  function getConnectionDetails(result) {
    const connection = result?.connection || result?.probe?.connection || {};
    const response = result?.response || result?.probe?.response || {};
    const requestHttp = response?.request_http || {};
    const bootstrapInitialize =
      result?.bootstrap?.initialize || result?.probe?.bootstrap?.initialize || {};

    return {
      protocolVersion:
        connection.protocol_version ||
        requestHttp.headers?.["mcp-protocol-version"] ||
        bootstrapInitialize.headers?.["mcp-protocol-version"] ||
        null,
      sessionToken:
        connection.mcp_session_id ||
        response.mcp_session_id ||
        requestHttp.mcp_session_id ||
        bootstrapInitialize.mcp_session_id ||
        null,
    };
  }

  function populateTemplate(templateId) {
    const template = findTemplate(templateId);
    if (!template) {
      return;
    }
    elements.requestEditor.value = formatJson(template.request);
    elements.templateDescription.textContent = template.description;
    updateRequestMeta(`Loaded template: ${template.label}`);
    clearRequestError();
  }

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      const error = new Error(data.message || "Request failed.");
      error.payload = data;
      throw error;
    }
    return data;
  }

  async function fetchJson(url) {
    const response = await fetch(url);
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(data.message || "Request failed.");
      error.payload = data;
      throw error;
    }
    return data;
  }

  async function connect() {
    setConnectionState("neutral", "Connecting to the selected MCP endpoint...");
    clearResponseError();
    clearRequestError();

    try {
      const data = await postJson("/api/connect", {
        target_url: elements.targetUrl.value,
        transport: elements.transportMode.value,
        protocol_version: getProtocolVersion(),
        client_session_id: getClientSessionId(),
      });
      isConnected = true;
      syncActionButtons();
      setConnectionState(
        "connected",
        `Connected to ${data.endpoint_url} using ${getTransportLabel(data.transport)}.`
      );
      const connectionDetails = getConnectionDetails(data.probe);
      setProtocolVersion(connectionDetails.protocolVersion);
      setSessionToken(connectionDetails.sessionToken);
      updateRequestMeta(
        `Connection established for ${data.endpoint_url} using protocol ${getProtocolVersion()}.`
      );
      setResponse(extractMcpPayload(data.probe));
    } catch (error) {
      applyDisconnectedUi(error.message);
      showResponseError(error.message);
      setResponse(
        (error.payload && error.payload.waf_response) || { error: error.message }
      );
    }
  }

  async function disconnect() {
    clearResponseError();
    clearRequestError();

    try {
      const data = await postJson("/api/disconnect", {
        client_session_id: getClientSessionId(),
        protocol_version: getProtocolVersion(),
      });
      applyDisconnectedUi("Disconnected from the active MCP session.");
      updateRequestMeta(data.message || "Session disconnected.");
      setResponse(data.result || { disconnected: true });
    } catch (error) {
      applyDisconnectedUi(error.message);
      showResponseError(error.message);
      setResponse({ error: error.message });
    }
  }

  function extractMcpPayload(result) {
    if (!result) {
      return { message: "No response received." };
    }

    if (result.response && result.response.event) {
      return result.response.event;
    }

    if (result.response && result.response.body) {
      return result.response.body;
    }

    if (result.probe && result.probe.response) {
      if (result.probe.response.event) {
        return result.probe.response.event;
      }
      if (result.probe.response.body) {
        return result.probe.response.body;
      }
    }

    return result;
  }

  async function sendRequest() {
    clearRequestError();
    clearResponseError();

    if (!isConnected) {
      showRequestError("Connect first before sending an MCP request.");
      return;
    }

    let parsedJson;

    try {
      parsedJson = JSON.parse(elements.requestEditor.value);
    } catch (error) {
      showRequestError(`Invalid JSON: ${error.message}`);
      return;
    }

    updateRequestMeta("JSON parsed successfully. Sending request on the current session.");
    setResponse({ message: "Sending request..." });

    try {
      const data = await postJson("/api/send", {
        target_url: elements.targetUrl.value,
        transport: elements.transportMode.value,
        protocol_version: getProtocolVersion(),
        client_session_id: getClientSessionId(),
        request: parsedJson,
      });
      setConnectionState(
        "connected",
        `Last MCP request succeeded against ${getTargetEndpoint()}.`
      );
      const connectionDetails = getConnectionDetails(data.result);
      setProtocolVersion(connectionDetails.protocolVersion);
      setSessionToken(connectionDetails.sessionToken);
      setResponse(extractMcpPayload(data.result));
      updateRequestMeta("Request completed on the active session.");
    } catch (error) {
      setConnectionState("error", error.message);
      showResponseError(error.message);
      setResponse(
        (error.payload && error.payload.waf_response) || { error: error.message }
      );
    }
  }

  function getServerPayload() {
    return {
      transport: elements.serverTransportMode.value,
      protocol_version: elements.serverProtocolVersion.value,
      host: elements.serverHost.value.trim(),
      port: Number(elements.serverPort.value),
    };
  }

  function applyServerStatus(status, logs) {
    const runtime = status || {};
    activeServerStatus = runtime;
    const running = runtime.running === true;
    const startedAtMs = getServerStartedAtMs(runtime);
    elements.serverState.textContent = runtime.state || "stopped";
    elements.serverStatusTransport.textContent = runtime.transport || "n/a";
    elements.serverStatusVersion.textContent = runtime.protocol_version || "n/a";
    elements.serverStatusPid.textContent = runtime.pid || "n/a";
    elements.serverStatusUptime.textContent = running
      ? (startedAtMs ? formatElapsedUptime(startedAtMs) : runtime.uptime || "n/a")
      : runtime.uptime || "n/a";
    elements.serverStatusEndpoint.textContent = runtime.endpoint_url || "n/a";
    elements.serverStatusError.textContent = runtime.last_error || "none";

    if (runtime.transport) {
      elements.serverTransportMode.value = runtime.transport;
    }
    if (runtime.protocol_version) {
      elements.serverProtocolVersion.value = runtime.protocol_version;
    }
    if (runtime.host) {
      elements.serverHost.value = runtime.host;
    }
    if (runtime.port) {
      elements.serverPort.value = runtime.port;
    }

    elements.serverStartButton.disabled = running;
    elements.serverStopButton.disabled = !running;
    elements.serverRestartButton.disabled = !running;
    elements.serverTransportMode.disabled = running;
    elements.serverProtocolVersion.disabled = running;
    elements.serverHost.disabled = running;
    elements.serverPort.disabled = running;

    if (Array.isArray(logs) && logs.length > 0) {
      elements.serverLogsViewer.textContent = logs.join("\n");
    } else {
      elements.serverLogsViewer.textContent = "No logs yet.";
    }
  }

  async function refreshServerStatus() {
    try {
      const data = await fetchJson("/api/server/status");
      applyServerStatus(data.status, data.logs);
    } catch (error) {
      elements.serverLogsViewer.textContent = error.message;
    }
  }

  async function resetServerLogs() {
    clearResponseError();
    try {
      const data = await postJson("/api/server/logs/reset", {});
      applyServerStatus(data.status, data.logs);
    } catch (error) {
      applyServerStatus(error.payload?.status, error.payload?.logs);
      showResponseError(error.message);
    }
  }

  async function startServer() {
    clearResponseError();
    try {
      const data = await postJson("/api/server/start", getServerPayload());
      applyServerStatus(data.status, data.logs);
    } catch (error) {
      applyServerStatus(error.payload?.status, error.payload?.logs);
      showResponseError(error.message);
    }
  }

  async function stopServer() {
    clearResponseError();
    try {
      const data = await postJson("/api/server/stop", {});
      applyServerStatus(data.status, data.logs);
    } catch (error) {
      applyServerStatus(error.payload?.status, error.payload?.logs);
      showResponseError(error.message);
    }
  }

  async function restartServer() {
    clearResponseError();
    try {
      const data = await postJson("/api/server/restart", getServerPayload());
      applyServerStatus(data.status, data.logs);
    } catch (error) {
      applyServerStatus(error.payload?.status, error.payload?.logs);
      showResponseError(error.message);
    }
  }

  elements.connectButton.addEventListener("click", connect);
  elements.disconnectButton.addEventListener("click", disconnect);
  elements.sendButton.addEventListener("click", sendRequest);
  elements.clientTab.addEventListener("click", () => setActiveView("client"));
  elements.serverTab.addEventListener("click", () => setActiveView("server"));
  elements.themeTab.addEventListener("click", () => setActiveView("theme"));
  elements.serverStartButton.addEventListener("click", startServer);
  elements.serverStopButton.addEventListener("click", stopServer);
  elements.serverRestartButton.addEventListener("click", restartServer);
  elements.serverRefreshButton.addEventListener("click", refreshServerStatus);
  elements.serverResetLogsButton.addEventListener("click", resetServerLogs);
  elements.welcomeDismissToggle.addEventListener("change", (event) => {
    setWelcomeModalDismissed(event.target.checked);
  });
  elements.welcomeModalOk.addEventListener("click", () => {
    setWelcomeModalDismissed(elements.welcomeDismissToggle.checked);
    hideWelcomeModal();
  });
  elements.formatButton.addEventListener("click", () => {
    clearRequestError();
    try {
      const parsed = JSON.parse(elements.requestEditor.value);
      elements.requestEditor.value = formatJson(parsed);
      syncFortinetEmptyControls();
      updateRequestMeta("JSON formatted successfully.");
    } catch (error) {
      showRequestError(`Invalid JSON: ${error.message}`);
    }
  });

  document.querySelectorAll("input, select, textarea").forEach((control) => {
    const syncControlState = () => syncFortinetEmptyControls();
    control.addEventListener("input", syncControlState);
    control.addEventListener("change", syncControlState);
  });

  renderActionGroups();
  renderThemeOptions();
  if (protocolVersionOptions.includes(DEFAULT_PROTOCOL_VERSION)) {
    elements.protocolVersion.value = DEFAULT_PROTOCOL_VERSION;
    elements.serverProtocolVersion.value = DEFAULT_PROTOCOL_VERSION;
  }
  setActiveView("server");
  applyTheme(getStoredTheme() || DEFAULT_THEME);
  syncFortinetEmptyControls();
  applyDisconnectedUi("No active MCP session.");
  if (shouldPresentWelcomeModal()) {
    showWelcomeModal();
  }
  refreshServerStatus();
  if (templates.length > 0) {
    populateTemplate(templates[0].id);
  }
})();
