"""WSGI entrypoint compatible with Render's default ``gunicorn app:app`` command."""

from backend.app import app

__all__ = ["app"]
