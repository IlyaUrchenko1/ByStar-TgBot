import sqlite3
from typing import Optional, Tuple, Dict, Any, List, Union
import json
from datetime import datetime

class Database:
    def __init__(self, db_name="data/services.db"):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_name, check_same_thread=False)
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")

    def ensure_connection(self):
        try:
            self.cursor.execute("SELECT 1")
        except (sqlite3.OperationalError, AttributeError):
            self.connect()

    def create_tables(self):
        self.ensure_connection()
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT,
                balance INTEGER DEFAULT 0,
                referral_telegram_id TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                discount INTEGER DEFAULT 0,
                amount_money INTEGER DEFAULT 0,
                max_uses INTEGER,
                uses INTEGER DEFAULT 0,
                is_used BOOLEAN DEFAULT 0
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount_star INTEGER,
                amount_ruble INTEGER,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.commit()

    #region Users
    
    def get_user(self, telegram_id: str) -> Optional[Dict]:
        self.ensure_connection()
        self.cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        user = self.cursor.fetchone()
        return dict(zip(['id', 'telegram_id', 'balance', 'referral_telegram_id'], user)) if user else None

    def create_user(self, telegram_id: str, referral_telegram_id: Optional[str] = None) -> Dict:
        self.ensure_connection()
        self.cursor.execute(
            "INSERT INTO users (telegram_id, referral_telegram_id) VALUES (?, ?)",
            (telegram_id, referral_telegram_id)
        )
        self.connection.commit()
        return self.get_user(telegram_id)

    def update_user_balance(self, telegram_id: str, amount: int) -> bool:
        self.ensure_connection()
        self.cursor.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id = ?",
            (amount, telegram_id)
        )
        self.connection.commit()
        return self.cursor.rowcount > 0
      
    def amount_refferal_by_tg_id(self, telegram_id: str) -> int:
        self.ensure_connection()
        self.cursor.execute("SELECT referral_telegram_id FROM users WHERE telegram_id = ?", (telegram_id,))
        referral_telegram_id = self.cursor.fetchone()
        return referral_telegram_id[0] if referral_telegram_id else None
      
      
    #endregion

    #region Promocodes

    def get_promocode(self, code: str) -> Optional[Dict]:
        self.ensure_connection()
        self.cursor.execute("SELECT * FROM promocodes WHERE code = ?", (code,))
        promo = self.cursor.fetchone()
        return dict(zip(['id', 'code', 'discount', 'amount_money', 'max_uses', 'uses', 'is_used'], promo)) if promo else None

    def create_promocode(self, code: str, discount: int, amount_money: int, max_uses: int) -> Dict:
        self.ensure_connection()
        self.cursor.execute(
            "INSERT INTO promocodes (code, discount, amount_money, max_uses) VALUES (?, ?, ?, ?)",
            (code, discount, amount_money, max_uses)
        )
        self.connection.commit()
        return self.get_promocode(code)

    def use_promocode(self, code: str) -> bool:
        self.ensure_connection()
        self.cursor.execute(
            "UPDATE promocodes SET uses = uses + 1, is_used = CASE WHEN uses + 1 >= max_uses THEN 1 ELSE 0 END WHERE code = ?",
            (code,)
        )
        self.connection.commit()
        return self.cursor.rowcount > 0

    #endregion

    #region Orders

    def create_order(self, user_id: int, amount_star: int, amount_ruble: int, status: str) -> int:
        self.ensure_connection()
        self.cursor.execute(
            "INSERT INTO orders (user_id, amount_star, amount_ruble, status) VALUES (?, ?, ?, ?)",
            (user_id, amount_star, amount_ruble, status)
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def get_order(self, order_id: int) -> Optional[Dict]:
        self.ensure_connection()
        self.cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = self.cursor.fetchone()
        return dict(zip(['id', 'user_id', 'amount_star', 'amount_ruble', 'status', 'created_at'], order)) if order else None

    def update_order_status(self, order_id: int, status: str) -> bool:
        self.ensure_connection()
        self.cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def get_user_orders(self, user_id: int) -> List[Dict]:
        self.ensure_connection()
        self.cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        orders = self.cursor.fetchall()
        return [dict(zip(['id', 'user_id', 'amount_star', 'amount_ruble', 'status', 'created_at'], order)) for order in orders]

    #endregion
