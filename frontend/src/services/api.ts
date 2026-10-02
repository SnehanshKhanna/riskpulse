import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
});

export const getMode = async () => (await api.get('/mode')).data;
export const getDashboardOverview = async () => (await api.get('/dashboard/overview')).data;
export const getSignals = async (limit = 50) => (await api.get(`/signals?limit=${limit}`)).data;
export const getSignal = async (id: string) => (await api.get(`/signals/${id}`)).data;
export const getStressRuns = async (limit = 10) => (await api.get(`/stress/runs?limit=${limit}`)).data;
export const getStressRun = async (id: string) => (await api.get(`/stress/runs/${id}`)).data;
export const getReplayStatus = async () => (await api.get('/replay/status')).data;
export const replayStart = async (speed: number) => (await api.post(`/replay/start?speed=${speed}`)).data;
export const replayPause = async () => (await api.post('/replay/pause')).data;
export const replayStop = async () => (await api.post('/replay/stop')).data;
export const replayReset = async () => (await api.post('/replay/reset')).data;
export const analyzeText = async (text: string) => (await api.post('/analyze', { text, source: "manual" })).data;
