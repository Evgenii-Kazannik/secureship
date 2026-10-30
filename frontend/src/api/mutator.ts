const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const fetchClient = async <T>(url: string, options: RequestInit): Promise<T> => {
  const res = await fetch(`${BASE}${url}`, options);
  const body = [204, 205].includes(res.status) ? null : await res.text();
  const data = body ? JSON.parse(body) : {};
  return { data, status: res.status, headers: res.headers } as T;
};
