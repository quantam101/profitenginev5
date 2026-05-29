import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API, headers: { "Content-Type": "application/json" } });

export async function postMerge(body) {
  const { data } = await api.post("/merge", body);
  return data;
}

export async function joinWaitlist(body) {
  const { data } = await api.post("/waitlist", body);
  return data;
}

export async function getStats() {
  const { data } = await api.get("/stats");
  return data;
}

export async function getDemoReport() {
  const { data } = await api.get("/demo");
  return data;
}
