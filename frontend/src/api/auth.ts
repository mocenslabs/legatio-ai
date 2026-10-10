import { apiClient } from '@/api/client'
import type {
  ChangePasswordPayload,
  LoginPayload,
  LoginResponse,
  ProfileUpdatePayload,
  RegisterPayload,
  TwoFactorSetupResponse,
  User,
} from '@/types/auth'

export async function loginRequest(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/auth/login/', payload)
  return data
}

export async function login2faRequest(payload: {
  email: string
  password: string
  code: string
}): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/auth/login/2fa/', payload)
  return data
}

export async function registerRequest(payload: RegisterPayload): Promise<LoginResponse | User> {
  const { data } = await apiClient.post<LoginResponse | User>('/auth/register/', payload)
  return data
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>('/auth/me/')
  return data
}

export async function updateProfile(payload: ProfileUpdatePayload): Promise<User> {
  const { data } = await apiClient.patch<User>('/auth/me/', payload)
  return data
}

export async function changePassword(payload: ChangePasswordPayload): Promise<{ message?: string }> {
  const { data } = await apiClient.post<{ message?: string }>('/auth/change-password/', payload)
  return data
}

export async function enable2fa(): Promise<TwoFactorSetupResponse> {
  const { data } = await apiClient.post<TwoFactorSetupResponse>('/auth/2fa/enable/')
  return data
}

export async function confirm2fa(code: string): Promise<{ message?: string }> {
  const { data } = await apiClient.post<{ message?: string }>('/auth/2fa/confirm/', { code })
  return data
}

export async function disable2fa(code: string): Promise<{ message?: string }> {
  const { data } = await apiClient.post<{ message?: string }>('/auth/2fa/disable/', { code })
  return data
}
