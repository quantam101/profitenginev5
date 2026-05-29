import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  headers: { "Content-Type": "application/json" },
});

export const postMerge = (body) => api.post("/merge", body).then((r) => r.data);
export const joinWaitlist = (body) => api.post("/waitlist", body).then((r) => r.data);
export const getStats = () => api.get("/stats").then((r) => r.data);
export const getDemoReport = () => api.get("/demo").then((r) => r.data);
export const getAgents = () => api.get("/agents").then((r) => r.data);
export const getApprovals = () => api.get("/approvals").then((r) => r.data);
export const getContent = () => api.get("/content/recent").then((r) => r.data);
export const getRevenue = (days = 30) =>
  api.get(`/revenue/series?days=${days}`).then((r) => r.data);
export const getCycleStatus = () => api.get("/cycle/status").then((r) => r.data);
