"""Vercel entrypoint: GET /api/location."""
from app import Handler

class handler(Handler):
    """Explicit Vercel HTTP handler; inherits the shared API routes."""
    pass
