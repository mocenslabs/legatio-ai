export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  is_verified?: boolean
  two_factor_enabled?: boolean
  preferred_language?: string
  preferred_timezone?: string
  date_joined?: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  password: string
  first_name?: string
  last_name?: string
}

export interface AuthTokens {
  access: string
  refresh?: string
}

export interface LoginResponse extends AuthTokens {
  user?: User
  requires_2fa?: boolean
}

export interface ProfileUpdatePayload {
  first_name?: string
  last_name?: string
  preferred_language?: string
  preferred_timezone?: string
}

export interface ChangePasswordPayload {
  current_password: string
  new_password: string
}

export interface TwoFactorSetupResponse {
  secret: string
  uri: string
  qr_code_url: string
}
