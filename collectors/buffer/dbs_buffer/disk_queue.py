from sqlalchemy import create_engine, Select, inspect
from sqlalchemy.orm import sessionmaker
from collectors.buffer.dbs_buffer.database_model import SqlMetrics, Base


class DatabaseBuffer:

    def __init__(self, db_url="sqlite:///buffer.db"):
        self.engine = create_engine(db_url)
        self.inspector = inspect(self.engine)
        self.tables = self.inspector.get_table_names()

        if "buffer_metrics" not in self.tables: Base.metadata.create_all(bind=self.engine)

        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def store_buffer(self, data: dict):

        b_m = SqlMetrics(
            device=data["device"].get("hostname", "unknown"),
            metric_type=data["device"].get("device_type", "unknown"),
            ots=data["timestamp"],
            payload=data,
            sent=False
        )
        self.session.add(b_m); self.session.commit(); self.session.close()
        return True

    def fetch_unsent(self, limit=100):
        session = self.Session()
        rows = session.execute(Select(SqlMetrics).where(SqlMetrics.sent == False).limit(limit)).scalars().all() ; session.close()
        if not rows: return False
        return rows


    def fetch_all_unsent(self):
        session = self.Session()
        rows = session.execute(
            Select(SqlMetrics).where(SqlMetrics.sent == False)
        ).scalars().all()
        session.close()
        if not rows: return False
        return rows


    def mark_sent(self, id_):
        session = self.Session()
        try:
            row = session.get(SqlMetrics, id_)
            if not row:
                return False

            row.sent = 1
            session.commit()
            return True

        finally:
            session.close()