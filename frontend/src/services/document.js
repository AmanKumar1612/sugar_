import api from "./api";

export const getDocuments = async () => {
  const res = await api.get("/documents/");
  return res.data;
};

export const getDocument = async (documentId) => {
  const res = await api.get(`/documents/${documentId}`);
  return res.data;
};

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  // Content-Type is handled automatically by the Axios interceptor in api.js
  // when it detects FormData — it removes the default application/json header
  // so the browser can set multipart/form-data with the correct boundary.
  const res = await api.post("/documents/upload", formData);
  return res.data;
};

export const addWebsite = async (url) => {
  const res = await api.post("/documents/add-website", { url });
  return res.data;
};

export const deleteDocument = async (documentId) => {
  const res = await api.delete(`/documents/${documentId}`);
  return res.data;
};
