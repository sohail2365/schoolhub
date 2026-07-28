import { api } from "./api.js";

export async function login(email, password) {
  const data = await api.login({ email, password });
  localStorage.setItem("access_token", data.access_token);
  return data;
}
