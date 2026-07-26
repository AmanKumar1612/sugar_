import api from "./api";

export const getOverview = async () => {
  const res = await api.get("/analytics/overview");
  return res.data;
};

export const getTopSearches = async () => {
  const res = await api.get("/analytics/top-searches");
  return res.data;
};

export const getFailedSearches = async () => {
  const res = await api.get("/analytics/failed-searches");
  return res.data;
};
