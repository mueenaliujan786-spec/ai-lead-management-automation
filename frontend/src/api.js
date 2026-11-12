const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "leadflow_token";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

// The login token lives in sessionStorage: it is cleared when the tab closes.
// React escapes all text it renders, and this app never injects raw HTML.
export const getToken = () => sessionStorage.getItem(TOKEN_KEY);
export const clearToken = () => sessionStorage.removeItem(TOKEN_KEY);

function readDetail(data) {
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) {
    return data.detail.map((d) => d.msg).join(", ");
  }
  return "Something went wrong.";
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${BASE}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("Cannot reach the server. Is the backend running?", 0);
  }

  if (response.status === 401 && path !== "/auth/login") {
    clearToken();
    window.dispatchEvent(new Event("leadflow:logout"));
    throw new ApiError("Your session expired. Please log in again.", 401);
  }

  if (!response.ok) {
    let data = null;
    try {
      data = await response.json();
    } catch {
      // The server sent no JSON body; the generic message is used.
    }
    throw new ApiError(readDetail(data), response.status);
  }
  return response.json();
}

export async function login(email, password) {
  const data = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  sessionStorage.setItem(TOKEN_KEY, data.access_token);
}

export const fetchMe = () => request("/auth/me");

export const listDrafts = (status) =>
  request(`/dashboard/drafts${status ? `?status=${status}` : ""}`);

export const getDraft = (id) => request(`/dashboard/drafts/${id}`);

export const editDraft = (id, subject, body) =>
  request(`/dashboard/drafts/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ subject, body }),
  });

export const reviewDraft = (id, decision) =>
  request(`/dashboard/drafts/${id}/review`, {
    method: "POST",
    body: JSON.stringify({ decision }),
  });
