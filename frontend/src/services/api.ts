import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auto-refresh token on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh/`, {
            refresh,
          });
          localStorage.setItem("access_token", data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ─── Types ───
export interface ConnectionInput {
  name: string;
  db_type: string;
  host: string;
  port: number;
  username: string;
  password: string;
  database: string;
}

export interface SubmitDataInput {
  connection_id: number;
  table_name: string;
  data: Record<string, unknown>[];
  original_data: Record<string, unknown>[];
  export_format: string;
}

// ─── Auth ───
export const authService = {
  login: (username: string, password: string) =>
    api.post("/auth/login/", { username, password }),

  register: (data: {
    username: string;
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) => api.post("/auth/register/", data),

  getProfile: () => api.get("/auth/profile/"),
};

// ─── Connections ───
export const connectionService = {
  list: () => api.get("/connections/"),
  create: (data: ConnectionInput) => api.post("/connections/", data),
  update: (id: number, data: Partial<ConnectionInput>) => api.put(`/connections/${id}/`, data),
  delete: (id: number) => api.delete(`/connections/${id}/`),
  test: (id: number) => api.post(`/connections/${id}/test/`),
  getTables: (id: number) => api.get(`/connections/${id}/tables/`),
  getColumns: (id: number, table: string) =>
    api.get(`/connections/${id}/tables/${table}/columns/`),
};

// ─── Extraction ───
export const extractionService = {
  extract: (data: {
    connection_id: number;
    table_name: string;
    batch_size: number;
    offset: number;
  }) => api.post("/extraction/extract/", data),

  getJobs: () => api.get("/extraction/jobs/"),
};

// ─── Storage ───
export const storageService = {
  submit: (data: SubmitDataInput) => api.post("/storage/submit/", data),
  getJobStatus: (jobId: number) => api.get(`/storage/jobs/${jobId}/`),

  getRecords: () => api.get("/storage/records/"),
  getFiles: () => api.get("/storage/files/"),
  downloadFile: (fileId: number) =>
    api.get(`/storage/files/${fileId}/download/`, { responseType: "blob" }),
  shareFile: (fileId: number) =>
    api.post(`/storage/files/${fileId}/share/`),
};
