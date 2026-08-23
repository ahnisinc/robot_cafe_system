CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL,
    recipe_id TEXT NOT NULL,
    recipe_name TEXT,
    status TEXT NOT NULL DEFAULT 'QUEUED',
    progress REAL NOT NULL DEFAULT 0,
    current_step TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS robot_status (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    system TEXT,
    mode TEXT,
    state TEXT,
    servo_on INTEGER,
    connected INTEGER,
    alarm TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS coffee_process_status (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    order_id TEXT,
    recipe_id TEXT,
    state TEXT,
    current_step TEXT,
    current_step_index INTEGER,
    total_steps INTEGER,
    progress REAL,
    message TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
