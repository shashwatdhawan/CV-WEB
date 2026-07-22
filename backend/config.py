import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - keeps startup friendly before deps are installed.
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent.parent

if load_dotenv:
    load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    discord_client_id: str | None = os.getenv("DISCORD_CLIENT_ID")
    discord_client_secret: str | None = os.getenv("DISCORD_CLIENT_SECRET")
    discord_redirect_uri: str | None = os.getenv("DISCORD_REDIRECT_URI")
    session_secret: str | None = os.getenv("SESSION_SECRET")
    admin_setup_code: str | None = os.getenv("ADMIN_SETUP_CODE", "jassibhaiilassipeetahai2rskifirhagtehai4baar")
    bot_api_secret: str | None = os.getenv("BOT_API_SECRET")

    @property
    def missing_auth_values(self) -> list[str]:
        missing: list[str] = []
        if not self.discord_client_id:
            missing.append("DISCORD_CLIENT_ID")
        if not self.discord_client_secret:
            missing.append("DISCORD_CLIENT_SECRET")
        if not self.discord_redirect_uri:
            missing.append("DISCORD_REDIRECT_URI")
        if not self.session_secret:
            missing.append("SESSION_SECRET")
        return missing

    @property
    def cookie_secure(self) -> bool:
        return bool(self.discord_redirect_uri and self.discord_redirect_uri.startswith("https://"))


settings = Settings()
