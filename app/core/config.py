from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "GraphRAG Dynamic ACL Plugin Showcase"
    api_v1_prefix: str = "/api/v1"
    debug: bool = True


settings = Settings()
