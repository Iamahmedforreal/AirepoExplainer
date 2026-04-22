import axios from "axios";
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

export function setupInterceptor(getToken: () => Promise<string | null>) {
  const interceptor = api.interceptors.request.use(async (config) => {
    console.log("🔵 Interceptor running...")
    const token = await getToken();
    console.log("🟢 Token:", token)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    else{
      console.log("🔴 Token is null!");
    }
    return config;
  });

  return () => api.interceptors.request.eject(interceptor); 
}

export default api;