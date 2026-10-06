export const tokenKey = "pikom-attendee-token";
export const getToken = () => (typeof window === "undefined" ? "" : window.localStorage.getItem(tokenKey) || "");
export const saveToken = (token) => window.localStorage.setItem(tokenKey, token);
export const clearToken = () => window.localStorage.removeItem(tokenKey);

export async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`/api/${path.replace(/^\//, "")}`, {
    ...options, headers, cache: "no-store",
    body: options.body && typeof options.body !== "string" ? JSON.stringify(options.body) : options.body,
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "The request could not be completed.");
  return data;
}
