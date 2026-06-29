from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    model_name: str = "gpt-4"
    database_url: str = "sqlite:///./data/campaign_assistant.db"
    data_directory: str = "./data"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
