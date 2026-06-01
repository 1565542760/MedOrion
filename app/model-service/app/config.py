from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', protected_namespaces=('settings_',))

    model_service_env: str = 'dev'
    model_service_host: str = '127.0.0.1'
    model_service_port: int = 8100
    model_service_log_level: str = 'INFO'
    model_service_cpu_only: bool = True
    model_service_max_concurrency: int = 1
    model_service_default_batch_size: int = 1
    model_service_default_timeout_ms: int = 15000


settings = Settings()
