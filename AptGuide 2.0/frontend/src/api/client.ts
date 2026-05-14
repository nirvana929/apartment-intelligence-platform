import axios from "axios";

export const http = axios.create({
  baseURL: import.meta.env.VITE_APTGUIDE_API_BASE || "",
  timeout: 30000
});

export function setBearerToken(token: string | null) {
  if (token) {
    http.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete http.defaults.headers.common.Authorization;
  }
}
