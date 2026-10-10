"""
System-wide constants for Legatio AI.

These constants are referenced throughout the codebase and must be
imported from this single source of truth.
"""

# Policy Engine
ENGINE_VERSION: str = "1.0.0"
ENGINE_NAME: str = "legatio-policy-engine"

# Default timeouts (in seconds)
DEFAULT_EXTERNAL_AGENT_TIMEOUT: int = 30
DEFAULT_LLM_TIMEOUT: int = 60
DEFAULT_APPROVAL_EXPIRATION_HOURS: int = 24
DEFAULT_NEGOTIATION_TTL_HOURS: int = 24
DEFAULT_NEGOTIATION_MAX_ROUNDS: int = 10

# Circuit breaker defaults
LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
LLM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT_SECONDS: int = 60

# Audit chain locking
AUDIT_CHAIN_LOCK_KEY: str = "legatio:audit_chain_lock"
AUDIT_CHAIN_LOCK_TTL_SECONDS: int = 10

# Risk thresholds
RISK_HIGH_AMOUNT_THRESHOLD: int = 500
RISK_CRITICAL_AMOUNT_THRESHOLD: int = 1000

# Performance targets
POLICY_ENGINE_MAX_EVALUATION_MS: int = 50
API_MAX_RESPONSE_TIME_MS: int = 200
WEBSOCKET_MAX_LATENCY_MS: int = 100

# Pagination
DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 200

# Reference code prefixes
NEGOTIATION_REFERENCE_PREFIX: str = "NEG"
AGREEMENT_REFERENCE_PREFIX: str = "AGR"

# Credential key prefix
CREDENTIAL_KEY_PREFIX: str = "lgat_"

# 2FA
TOTP_DEFAULT_DIGITS: int = 6
TOTP_DEFAULT_INTERVAL: int = 30

# JWT defaults
JWT_DEFAULT_ACCESS_TOKEN_LIFETIME_MINUTES: int = 15
JWT_DEFAULT_REFRESH_TOKEN_LIFETIME_DAYS: int = 7
