export const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export function getToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("token") || "";
}

export function clearAuth() {
  if (typeof window !== "undefined") localStorage.removeItem("token");
}

export async function apiFetch(path: string, init: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(init.headers || {});
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(`${API}${path}`, { ...init, headers });
}

export async function readError(res: Response, fallback = "Something went wrong") {
  try {
    const data = await res.json();
    return data?.detail || data?.message || fallback;
  } catch {
    return fallback;
  }
}

export function roleHome(role?: string) {
  switch (role) {
    case "EMPLOYER": return "/employer";
    case "TRAINING_PROVIDER": return "/provider";
    case "GOVERNMENT_ADMIN": return "/admin";
    default: return "/profile";
  }
}
