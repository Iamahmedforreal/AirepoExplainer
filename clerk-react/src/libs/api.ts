// lib/api.ts
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

export function setupInterceptor(getToken: () => Promise<string | null>) {
  const interceptor = api.interceptors.request.use(async (config) => {
    const token = await getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  return () => api.interceptors.request.eject(interceptor); 
}

export default api;