def init(url_env="DATABASE_URL"):
    
    import os
    from dotenv import load_dotenv
    from nexora_db.configs.database import init_database, init_db_tables

    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".env")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", ".env")),
    ]

    for path in candidates:
        if os.path.exists(path):
            load_dotenv(path)
            print(f"Loaded .env from: {path}")
            break

    url = os.getenv(url_env)
    if not url:
        temp_path = os.path.join(os.getcwd(), "temp.db")
        url = f"sqlite:///{temp_path}"
        print(f"{url_env} not found. Using default SQLite at {temp_path}")

    init_database(url) ; init_db_tables()
    print(f"Database initialized: {url}")