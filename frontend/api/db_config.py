import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DatabaseConfig:
    database: str = os.getenv("DB_NAME", "cybersecurity.db")
    
    @property
    def connection_string(self):
        db_path = Path(__file__).parent.parent / self.database
        return f"sqlite:///{db_path}"

db_config = DatabaseConfig()