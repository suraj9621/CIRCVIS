"""
Persistent prediction logging using SQLite.
"""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..utils.helpers import ImageProcessor


class PredictionLog:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._ensure_db()

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    internal_class_name TEXT NOT NULL,
                    display_class_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    processing_time_ms REAL NOT NULL,
                    model_name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    filename TEXT,
                    source_url TEXT
                )
                """
            )
            conn.commit()

    def log_prediction(
        self,
        internal_class_name: str,
        display_class_name: str,
        confidence: float,
        processing_time_ms: float,
        model_name: str = "circvis",
        source: str = "upload",
        filename: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> None:
        created_at = datetime.utcnow().isoformat() + "Z"
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO predictions (
                        created_at,
                        internal_class_name,
                        display_class_name,
                        confidence,
                        processing_time_ms,
                        model_name,
                        source,
                        filename,
                        source_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        created_at,
                        internal_class_name,
                        display_class_name,
                        confidence,
                        processing_time_ms,
                        model_name,
                        source,
                        filename,
                        source_url,
                    ),
                )
                conn.commit()

    def get_class_distribution(self) -> Dict[str, int]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT display_class_name, COUNT(*) AS count FROM predictions GROUP BY display_class_name"
            )
            return {row["display_class_name"]: int(row["count"]) for row in cursor.fetchall()}

    def get_total_predictions(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("SELECT COUNT(*) AS total FROM predictions")
            row = cursor.fetchone()
            return int(row["total"] or 0)

    def get_recent_predictions(self, limit: int = 20) -> List[Dict[str, str]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT created_at, display_class_name, confidence, processing_time_ms, model_name, source, filename, source_url
                FROM predictions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def has_demo_data(self) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) AS count FROM predictions WHERE source = 'demo'"
            )
            row = cursor.fetchone()
            return int(row["count"] or 0) > 0

    def seed_demo_data(self) -> None:
        if self.has_demo_data():
            return

        sample_entries = [
            {
                "internal_class_name": "plastic",
                "display_class_name": ImageProcessor.get_display_class_name("plastic"),
                "confidence": 0.93,
                "processing_time_ms": 85.4,
                "model_name": "circvis",
                "source": "demo",
                "filename": "plastic_bottle.jpg",
            },
            {
                "internal_class_name": "glass",
                "display_class_name": ImageProcessor.get_display_class_name("glass"),
                "confidence": 0.88,
                "processing_time_ms": 78.1,
                "model_name": "circvis",
                "source": "demo",
                "filename": "glass_jar.png",
            },
            {
                "internal_class_name": "paper_cardboard",
                "display_class_name": ImageProcessor.get_display_class_name("paper_cardboard"),
                "confidence": 0.92,
                "processing_time_ms": 90.7,
                "model_name": "circvis",
                "source": "demo",
                "filename": "cardboard_box.jpg",
            },
            {
                "internal_class_name": "metal",
                "display_class_name": ImageProcessor.get_display_class_name("metal"),
                "confidence": 0.81,
                "processing_time_ms": 82.5,
                "model_name": "circvis",
                "source": "demo",
                "filename": "tin_can.jpg",
            },
            {
                "internal_class_name": "organic",
                "display_class_name": ImageProcessor.get_display_class_name("organic"),
                "confidence": 0.79,
                "processing_time_ms": 88.9,
                "model_name": "circvis",
                "source": "demo",
                "source_url": "https://example.com/food_scraps.jpg",
            },
            {
                "internal_class_name": "textile",
                "display_class_name": ImageProcessor.get_display_class_name("textile"),
                "confidence": 0.86,
                "processing_time_ms": 91.2,
                "model_name": "circvis",
                "source": "demo",
                "source_url": "https://example.com/textile_rag.png",
            },
            {
                "internal_class_name": "miscellaneous",
                "display_class_name": ImageProcessor.get_display_class_name("miscellaneous"),
                "confidence": 0.84,
                "processing_time_ms": 80.3,
                "model_name": "circvis",
                "source": "demo",
            },
            {
                "internal_class_name": "plastic",
                "display_class_name": ImageProcessor.get_display_class_name("plastic"),
                "confidence": 0.95,
                "processing_time_ms": 77.6,
                "model_name": "circvis",
                "source": "demo",
                "filename": "water_bottle.jpg",
            },
        ]

        for entry in sample_entries:
            self.log_prediction(**entry)
