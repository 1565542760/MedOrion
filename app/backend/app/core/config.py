from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'MedOrion Backend'
    app_env: str = 'development'
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    api_v1_prefix: str = '/api/v1'

    database_url: str = 'postgresql+psycopg://medorion:medorion@127.0.0.1:5432/medorion'
    redis_url: str = 'redis://127.0.0.1:6379/0'
    s3_endpoint_url: str = 'http://127.0.0.1:9000'
    model_service_url: str = 'http://127.0.0.1:8100'
    log_level: str = 'INFO'

    jwt_secret_key: str = 'CHANGE_ME_stage18_jwt_secret'
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    password_hash_algorithm: str = 'argon2id'


settings = Settings()
