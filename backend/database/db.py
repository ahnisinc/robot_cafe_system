import sqlite3

from backend.config import (
    DATABASE_PATH,
)


def get_connection():

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row

    return connection


def init_database():
    connection = get_connection()

    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS orders (

                id INTEGER PRIMARY KEY
                    AUTOINCREMENT,

                order_id TEXT UNIQUE
                    NOT NULL,

                recipe_id TEXT NOT NULL,

                recipe_name TEXT,

                status TEXT
                    NOT NULL DEFAULT 'QUEUED',

                progress REAL
                    NOT NULL DEFAULT 0,

                current_step TEXT,

                created_at DATETIME
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at DATETIME
                    DEFAULT CURRENT_TIMESTAMP
            );


            CREATE TABLE IF NOT EXISTS
            robot_status (

                id INTEGER PRIMARY KEY
                    CHECK (id = 1),

                system TEXT,

                mode TEXT,

                state TEXT,

                servo_on INTEGER,

                connected INTEGER,

                alarm TEXT,

                updated_at DATETIME
                    DEFAULT CURRENT_TIMESTAMP
            );


            CREATE TABLE IF NOT EXISTS
            coffee_process_status (

                id INTEGER PRIMARY KEY
                    CHECK (id = 1),

                order_id TEXT,

                recipe_id TEXT,

                state TEXT,

                current_step TEXT,

                current_step_index INTEGER,

                total_steps INTEGER,

                progress REAL,

                message TEXT,

                updated_at DATETIME
                    DEFAULT CURRENT_TIMESTAMP
            );
            """)

        connection.commit()

    finally:
        connection.close()


def save_order(order_id, recipe_id, recipe_name):

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO orders (
                order_id,
                recipe_id,
                recipe_name,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (order_id, recipe_id, recipe_name, "QUEUED"),
        )

        connection.commit()

    finally:
        connection.close()


def update_order_progress(order_id, status, progress, current_step):

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE orders

            SET status = ?,
                progress = ?,
                current_step = ?,
                updated_at =
                    CURRENT_TIMESTAMP

            WHERE order_id = ?
            """,
            (status, progress, current_step, order_id),
        )

        connection.commit()

    finally:
        connection.close()


def get_order(order_id):

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM orders
            WHERE order_id = ?
            """,
            (order_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def save_process_status(data):

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT OR REPLACE INTO
            coffee_process_status (
                id,
                order_id,
                recipe_id,
                state,
                current_step,
                current_step_index,
                total_steps,
                progress,
                message,
                updated_at
            )
            VALUES (
                1,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                CURRENT_TIMESTAMP
            )
            """,
            (
                data.get("order_id", ""),
                data.get("recipe_id", ""),
                data.get("state", ""),
                data.get("current_step", ""),
                data.get("current_step_index", 0),
                data.get("total_steps", 0),
                data.get("progress", 0.0),
                data.get("message", ""),
            ),
        )

        connection.commit()

    finally:
        connection.close()


def get_process_status():

    connection = get_connection()

    try:
        row = connection.execute("""
            SELECT *
            FROM coffee_process_status
            WHERE id = 1
            """).fetchone()

        return dict(row) if row else {}

    finally:
        connection.close()
