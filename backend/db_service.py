import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager


class DatabaseService:
    def __init__(self, db_path="vacation.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database and create tables."""
        with self.get_connection() as conn:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
            conn.commit()

    @contextmanager
    def get_connection(self):
        """Get a database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    # User Operations
    def get_user_by_username(self, username):
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    def get_user_by_id(self, user_id):
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    def get_user_roles(self, user_id):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT r.name FROM roles r JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = ?",
                (user_id,)
            ).fetchall()

    def create_user(self, username, email, full_name, manager_id=None):
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO users (username, email, full_name, manager_id) VALUES (?, ?, ?, ?)",
                    (username, email, full_name, manager_id)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def assign_role_to_user(self, user_id, role_name):
        with self.get_connection() as conn:
            role = conn.execute("SELECT id FROM roles WHERE name = ?", (role_name,)).fetchone()
            if role:
                conn.execute(
                    "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
                    (user_id, role['id'])
                )
                conn.commit()

    def get_subordinates(self, manager_id):
        """Get all users managed by a specific manager."""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE manager_id = ? AND is_active = 1",
                (manager_id,)
            ).fetchall()

    def get_all_users(self):
        """Get all active users."""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE is_active = 1"
            ).fetchall()

    def update_user_manager(self, user_id, manager_id):
        """Update a user's manager."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET manager_id = ? WHERE id = ?",
                (manager_id, user_id)
            )
            conn.commit()

    def delete_user(self, user_id):
        """Soft delete a user by deactivating them."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET is_active = 0 WHERE id = ?",
                (user_id,)
            )
            conn.commit()

    # Vacation Request Operations
    def create_vacation_request(self, user_id, start_date, end_date, hours_requested, reason, request_type='FULL_DAY', start_time='09:00:00', end_time='17:00:00'):
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO vacation_requests 
                   (user_id, start_date, end_date, start_time, end_time, hours_requested, reason, status, requested_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)""",
                (user_id, start_date, end_date, start_time, end_time, hours_requested, reason, user_id)
            )
            conn.commit()
            return cursor.lastrowid

    def get_vacation_request(self, request_id):
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM vacation_requests WHERE id = ?", (request_id,)).fetchone()

    def get_user_vacation_requests(self, user_id):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM vacation_requests WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ).fetchall()

    def get_pending_requests_for_manager(self, manager_id):
        """Get all pending requests for users managed by this manager."""
        with self.get_connection() as conn:
            subordinates = conn.execute(
                "SELECT id FROM users WHERE manager_id = ?",
                (manager_id,)
            ).fetchall()
            sub_ids = [s['id'] for s in subordinates]
            if not sub_ids:
                return []
            placeholders = ','.join('?' * len(sub_ids))
            return conn.execute(
                f"SELECT * FROM vacation_requests WHERE user_id IN ({placeholders}) AND status = 'PENDING' ORDER BY created_at DESC",
                sub_ids
            ).fetchall()

    def approve_request(self, request_id, manager_id):
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE vacation_requests 
                   SET status = 'APPROVED', reviewed_by = ?, reviewed_at = ?
                   WHERE id = ?""",
                (manager_id, datetime.now().isoformat(), request_id)
            )
            # Deduct from balance
            request = conn.execute("SELECT * FROM vacation_requests WHERE id = ?", (request_id,)).fetchone()
            if request:
                year = datetime.strptime(request['start_date'], '%Y-%m-%d').year
                conn.execute(
                    """UPDATE vacation_balances 
                       SET used_hours = used_hours + ?
                       WHERE user_id = ? AND year = ?""",
                    (request['hours_requested'], request['user_id'], year)
                )
            conn.commit()

    def reject_request(self, request_id, manager_id):
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE vacation_requests 
                   SET status = 'REJECTED', reviewed_by = ?, reviewed_at = ?
                   WHERE id = ?""",
                (manager_id, datetime.now().isoformat(), request_id)
            )
            conn.commit()

    # Vacation Balance Operations
    def get_vacation_balance(self, user_id, year=None):
        if year is None:
            year = datetime.now().year
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM vacation_balances WHERE user_id = ? AND year = ?",
                (user_id, year)
            ).fetchone()

    def create_vacation_balance(self, user_id, year, balance_hours):
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO vacation_balances (user_id, year, balance_hours, used_hours) VALUES (?, ?, ?, 0)",
                    (user_id, year, balance_hours)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def update_vacation_balance(self, user_id, year, balance_hours):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE vacation_balances SET balance_hours = ? WHERE user_id = ? AND year = ?",
                (balance_hours, user_id, year)
            )
            conn.commit()
