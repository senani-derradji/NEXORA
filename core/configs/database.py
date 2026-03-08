def init(url_env: str = "DATABASE_URL"):
    import os
    from dotenv import load_dotenv
    from nexora_db.configs.database import init_database, init_db_tables

    env_path = os.path.join(os.path.dirname(__file__), ".env") ; load_dotenv(dotenv_path=env_path)

    url = os.getenv(url_env)
    if not url: raise ValueError(f"Environment variable '{url_env}' is not set or empty.")

    init_database(url) ; init_db_tables()