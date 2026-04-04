(function () {
  const templates = window.APP_BOOTSTRAP.templates;
  const CLIENT_SESSION_STORAGE_KEY = "mcp-demo-client-session-id";

  const elements = {
    targetUrl: document.getElementById("target-url"),
    transportMode: document.getElementById("transport-mode"),
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
  };

  let isConnected = false;

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

  function syncActionButtons() {
    elements.connectButton.disabled = isConnected;
    elements.disconnectButton.disabled = !isConnected;
    elements.sendButton.disabled = !isConnected;
    elements.targetUrl.disabled = isConnected;
    elements.transportMode.disabled = isConnected;
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
    elements.protocolVersionDisplay.textContent = `MCP Protocol Version: ${version || "unknown"}`;
  }

  function setSessionToken(token) {
    elements.sessionTokenDisplay.textContent = `MCP Session Token: ${token || "unknown"}`;
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

  async function connect() {
    setConnectionState("neutral", "Connecting to the selected MCP endpoint...");
    clearResponseError();
    clearRequestError();

    try {
      const data = await postJson("/api/connect", {
        target_url: elements.targetUrl.value,
        transport: elements.transportMode.value,
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
      updateRequestMeta(`Connection established for ${data.endpoint_url}`);
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

  elements.connectButton.addEventListener("click", connect);
  elements.disconnectButton.addEventListener("click", disconnect);
  elements.sendButton.addEventListener("click", sendRequest);
  elements.formatButton.addEventListener("click", () => {
    clearRequestError();
    try {
      const parsed = JSON.parse(elements.requestEditor.value);
      elements.requestEditor.value = formatJson(parsed);
      updateRequestMeta("JSON formatted successfully.");
    } catch (error) {
      showRequestError(`Invalid JSON: ${error.message}`);
    }
  });

  renderActionGroups();
  applyDisconnectedUi("No active MCP session.");
  if (templates.length > 0) {
    populateTemplate(templates[0].id);
  }
})();
