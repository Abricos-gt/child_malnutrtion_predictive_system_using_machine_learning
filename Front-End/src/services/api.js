import axios from "axios";

const apiClient = axios.create({
  baseURL: `http://${window.location.hostname}:5000`,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

export const login = (payload) => {
  return apiClient.post("/login", {
    username: payload.username,
    password: payload.password,
  });
};

export const predict = (payload) => {
  return apiClient.post("/predict", {
    patient_name: payload.patient_name,
    age_months: payload.age_months,
    weight_kg: payload.weight_kg,
    height_cm: payload.height_cm,
    gender: payload.gender,
    diarrhea: payload.diarrhea,
    anemia: payload.anemia,
    malaria: payload.malaria,
  });
};

export const getCHWDashboard = () => {
  return apiClient.get("/chw/dashboard");
};

export const getAdminDashboard = () => {
  return apiClient.get("/admin/dashboard");
};

export const getCHWStats = () => {
  return apiClient.get("/admin/chw_stats");
};

export const createCHW = (payload) => {
  return apiClient.post("/admin/create-chw", {
    username: payload.username,
    email: payload.email,
    password: payload.password,
  });
};

export default apiClient;
