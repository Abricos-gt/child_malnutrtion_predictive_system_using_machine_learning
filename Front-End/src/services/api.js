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

export const logout = () => {
  return apiClient.post("/logout");
};

export const registerPatient = (payload) => {
  return apiClient.post("/register-patient", {
    name: payload.name,
    parent_name: payload.parent_name,
    dob: payload.dob,
    gender: payload.gender,
    address: payload.address,
    phone: payload.phone,
  });
};

export const getPatientDetails = (patientId) => {
  return apiClient.get(`/patient/${patientId}`);
};

export const searchPatients = (query) => {
  return apiClient.get("/search-patients", {
    params: { q: query },
  });
};

export const predict = (payload) => {
  return apiClient.post("/predict", {
    patient_id: payload.patient_id,
    weight_kg: payload.weight_kg,
    height_cm: payload.height_cm,
    diarrhea: payload.diarrhea,
    anemia: payload.anemia,
    malaria: payload.malaria,
  });
};

export const getAdminDashboard = () => {
  return apiClient.get("/admin/dashboard");
};

export const createCHW = (payload) => {
  return apiClient.post("/admin/create-chw", {
    username: payload.username,
    email: payload.email,
    password: payload.password,
  });
};

export default apiClient;
