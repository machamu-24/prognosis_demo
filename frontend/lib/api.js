const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export function getApiBase() {
  return API_BASE;
}

async function fetchJson(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);

  if (!response.ok) {
    let message = "Request failed";
    try {
      const data = await response.json();
      message = data.detail || JSON.stringify(data);
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.json();
}

export function fetchMetadata() {
  return fetchJson("/metadata");
}

export function fetchMetrics() {
  return fetchJson("/metrics");
}

export function predictCase(payload) {
  return fetchJson("/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
}

