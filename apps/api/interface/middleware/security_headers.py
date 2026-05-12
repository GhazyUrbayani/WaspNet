"""
WaspNet — Security Headers Middleware
SEC: Applies security headers to all responses (OWASP best practices).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every HTTP response.
    SEC: Defense-in-depth against XSS, clickjacking, MIME-type sniffing.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # SEC: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # SEC: Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # SEC: XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # SEC: Referrer policy — don't leak full URL
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # SEC: HSTS — force HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # SEC: Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.sim.dune.com; "
            "font-src 'self' https://fonts.gstatic.com"
        )

        # SEC: Permissions Policy — disable unused browser APIs
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        return response
