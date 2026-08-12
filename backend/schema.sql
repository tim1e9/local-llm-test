-- HR Vacation Application Database Schema

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    manager_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,  -- EMPLOYEE, MANAGER, ADMIN
    description TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS vacation_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    balance_hours REAL NOT NULL DEFAULT 0,
    used_hours REAL NOT NULL DEFAULT 0,
    UNIQUE(user_id, year),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS vacation_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME DEFAULT '09:00:00',
    end_time TIME DEFAULT '17:00:00',
    hours_requested REAL NOT NULL,
    request_type TEXT NOT NULL DEFAULT 'FULL_DAY',  -- FULL_DAY, HALF_DAY_MORNING, HALF_DAY_AFTERNOON
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING, APPROVED, REJECTED, CANCELLED
    requested_by INTEGER NOT NULL,
    reviewed_by INTEGER,
    reviewed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (reviewed_by) REFERENCES users(id)
);

-- Seed default roles
INSERT OR IGNORE INTO roles (name, description) VALUES
    ('EMPLOYEE', 'Regular employee who can request vacation'),
    ('MANAGER', 'Manager who can approve/reject vacation requests'),
    ('ADMIN', 'System administrator with full access');
