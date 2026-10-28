class AIError(Exception):
    """Base error for AI provider failures.

    `public_message` is safe to return to API clients. Internal/provider details
    stay in `internal_message` and must never be serialized into a response.
    """

    kind = "ai_error"
    http_status = 502
    public_message = "The AI provider could not complete the request."

    def __init__(self, internal_message: str = ""):
        self.internal_message = internal_message
        super().__init__(internal_message or self.public_message)


class AINotConfigured(AIError):
    kind = "ai_not_configured"
    http_status = 503
    public_message = "AI generation is not configured on this server."


class AIQuotaExceeded(AIError):
    kind = "ai_quota_exceeded"
    http_status = 429
    public_message = (
        "The AI provider's quota or rate limit was reached. Please try again later."
    )


class AIRateLimited(AIError):
    kind = "ai_rate_limited"
    http_status = 429
    public_message = "The AI provider is rate limiting requests. Please try again later."


class AITimeout(AIError):
    kind = "ai_timeout"
    http_status = 504
    public_message = "The AI provider timed out. Please try again."


class AIInvalidResponse(AIError):
    kind = "ai_invalid_response"
    http_status = 502
    public_message = "The AI provider returned an invalid or incomplete response."


class AIProviderError(AIError):
    kind = "ai_provider_error"
    http_status = 502
    public_message = "The AI provider is currently unavailable. Please try again later."
