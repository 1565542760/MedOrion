
from uuid import UUID

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
    enable_cap_cop_clinical_mlp_shadow: bool = False
    cap_cop_clinical_mlp_shadow_cpu_only: bool = True
    cap_cop_clinical_mlp_shadow_batch_size: int = 1
    cap_cop_clinical_mlp_shadow_max_concurrency: int = 1
    cap_cop_clinical_mlp_shadow_timeout_seconds: int = 10
    cap_cop_clinical_mlp_shadow_force_no_grad: bool = True
    cap_cop_clinical_mlp_shadow_force_eval_mode: bool = True
    cap_cop_clinical_mlp_shadow_disable_gpu: bool = True
    cap_cop_clinical_mlp_shadow_allowed_model_version_ids: list[UUID] = []
    log_level: str = 'INFO'

    jwt_secret_key: str = 'CHANGE_ME_stage18_jwt_secret'
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    password_hash_algorithm: str = 'argon2id'


settings = Settings()
