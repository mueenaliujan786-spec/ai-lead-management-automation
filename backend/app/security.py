import secrets

from fastapi import Header, HTTPException

from app.config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Rejects any request that does not send the correct x-api-key header."""
    # compare_digest takes the same time for right and wrong keys,
    # which prevents attackers from guessing the key letter by letter.
    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode("utf-8"), settings.webhook_api_key.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")