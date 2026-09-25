import { apiRequest } from "./client";

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export async function register(
  data: RegisterData
): Promise<User> {
  return apiRequest<User>("/auth/register", {
    method: "POST",
    body: data,
  });
}

export async function login(
  data: LoginData
): Promise<AuthTokens> {
  return apiRequest<AuthTokens>("/auth/login", {
    method: "POST",
    body: data,
  });
}

export async function getCurrentUser(
  accessToken: string
): Promise<User> {
  return apiRequest<User>("/auth/me", {
    method: "GET",
    accessToken,
  });
}

export async function logout(
  accessToken: string,
  refreshToken: string
): Promise<void> {
  return apiRequest<void>("/auth/logout", {
    method: "POST",
    accessToken,
    body: {
      refresh_token: refreshToken,
    },
  });
}