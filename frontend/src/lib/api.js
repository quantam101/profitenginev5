import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
export const api = axios.create({ baseURL: API, headers: { "Content-Type": "application/json" } });

// Marketing
export const getStats = () => api.get("/stats").then((r) => r.data);
export const joinWaitlist = (b) => api.post("/waitlist", b).then((r) => r.data);

// Agents + cycle + sovereign
export const getAgents = () => api.get("/agents").then((r) => r.data);
export const getFleetStats = () => api.get("/agents/fleet-stats").then((r) => r.data);
export const executeAgent = (id) => api.post(`/agents/${id}/execute`).then((r) => r.data);
export const getCycleStatus = () => api.get("/cycle/status").then((r) => r.data);
export const getSovereignStatus = () => api.get("/sovereign/status").then((r) => r.data);
export const getSovereignDecisions = () => api.get("/sovereign/decisions").then((r) => r.data);

// Approvals + advisor
export const getApprovals = () => api.get("/approvals").then((r) => r.data);
export const decideApproval = (id, decision) => api.post(`/approvals/${id}/decide`, { decision }).then((r) => r.data);
export const askAdvisor = (q) => api.post("/advisor/ask", { question: q }).then((r) => r.data);

// Content
export const getContent = () => api.get("/content/recent").then((r) => r.data);

// Revenue + ledger
export const getRevenue = (days = 30) => api.get(`/revenue/series?days=${days}`).then((r) => r.data);
export const getRevenueStreams = () => api.get("/revenue/streams").then((r) => r.data);
export const getRevenueStats = () => api.get("/revenue/stats").then((r) => r.data);
export const getLedgerProgress = () => api.get("/ledger/progress").then((r) => r.data);

// Operations
export const getScoutOpps = () => api.get("/scout/opportunities").then((r) => r.data);
export const getDeployments = () => api.get("/deployments").then((r) => r.data);
export const getBuilds = () => api.get("/builds").then((r) => r.data);
export const getAudit = () => api.get("/audit").then((r) => r.data);
export const getBooks = () => api.get("/books").then((r) => r.data);
export const getProposals = () => api.get("/proposals").then((r) => r.data);
export const getSecrets = () => api.get("/secrets").then((r) => r.data);
export const getCost = () => api.get("/cost").then((r) => r.data);
export const getProofOfWork = () => api.get("/proof-of-work").then((r) => r.data);
export const getDistillation = () => api.get("/distillation/status").then((r) => r.data);
export const getAnalytics = () => api.get("/analytics").then((r) => r.data);

// Code merger
export const postMerge = (b) => api.post("/merge", b).then((r) => r.data);
export const getDemoReport = () => api.get("/demo").then((r) => r.data);
