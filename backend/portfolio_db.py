"""
Portfolio Database Manager
Isolated database for saving custom categories and stocks.
Database File: backend/portfolio.db
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "portfolio.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Categories Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TEXT
    )
    ''')
    
    # Stocks Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        ticker TEXT NOT NULL,
        added_at TEXT,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE,
        UNIQUE(category_id, ticker)
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[PortfolioDB] Database initialized at {DB_PATH}")

# --- Category Operations ---

def create_category(name: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO categories (name, created_at) VALUES (?, ?)',
            (name, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Already exists
        return -1
    finally:
        conn.close()

def get_categories() -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append(dict(row))
    return result

def delete_category(category_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()

# --- Stock Operations ---

def add_stock(category_id: int, ticker: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    ticker = ticker.upper().strip()
    try:
        cursor.execute(
            'INSERT INTO stocks (category_id, ticker, added_at) VALUES (?, ?, ?)',
            (category_id, ticker, datetime.now().isoformat())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Already exists in this category
        return False
    finally:
        conn.close()

def get_stocks(category_id: int) -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ticker FROM stocks WHERE category_id = ?', (category_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row['ticker'] for row in rows]

def delete_stock(category_id: int, ticker: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM stocks WHERE category_id = ? AND ticker = ?',
        (category_id, ticker.upper())
    )
    conn.commit()
    conn.close()

# Initialize DB on module import
init_db()
