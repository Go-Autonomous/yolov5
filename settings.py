from pydantic import BaseSettings, PostgresDsn
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    NAME: str = "yolov5 router"
    SAGA_TOKEN: str = "notgonnagetthis"
    SENTRY_DSN: str = "https://sentry.io/organization/project/project-id"
    ENVIRONMENT: str = "production"
    POSTGREST_URL: str = "localhost"


class DatabaseSettings(BaseSettings):
    PG_DSN: PostgresDsn = "postgresql://root:root@localhost:5432/test_db"  # maybe we should just use postgrest


db_settings = DatabaseSettings()
settings = Settings()
