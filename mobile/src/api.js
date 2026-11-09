import { API_URL } from "./config";

let token = null;
let onUnauthorized = () => {};

export function setToken(value) {
  token = value;
}

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth && token) headers.Authorization = `Token ${token}`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  let response;
  try {
    response = await fetch(`${API_URL}/api${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (error) {
    throw new ApiError(`Cannot reach the campus server at ${API_URL}. Check your connection and try again.`, 0, null);
  } finally {
    clearTimeout(timer);
  }

  if (response.status === 204) return null;
  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }

  if (!response.ok) {
    if (response.status === 401 && auth && token) onUnauthorized();
    const message =
      (data && typeof data.detail === "string" && data.detail) ||
      (response.status === 429 ? "Too many attempts. Wait a minute and try again." : "Something went wrong. Please try again.");
    throw new ApiError(message, response.status, data);
  }
  return data;
}

export const api = {
  get: (path) => request(path),
  post: (path, body, options) => request(path, { method: "POST", body: body ?? {}, ...options }),
  patch: (path, body) => request(path, { method: "PATCH", body }),
  del: (path) => request(path, { method: "DELETE" }),
};
