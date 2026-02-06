import json
import os
import random
import string
from datetime import datetime
from typing import List, Dict

DB_FILE = "bot_data.json"

class Database:
    def __init__(self):
        self.data = self._load()
        self._init_defaults()
    
    def _load(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save(self):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def _init_defaults(self):
        if "users" not in self.data:
            self.data["users"] = {}
        if "sellers" not in self.data:
            self.data["sellers"] = {
                "seller_1": {"name": "🔥 Mega Keys", "price": 2.0, "keys": []},
                "seller_2": {"name": "⚡ Pro Keys", "price": 3.0, "keys": []},
                "seller_3": {"name": "💎 Elite Keys", "price": 4.0, "keys": []}
            }
        if "reviews" not in self.data:
            self.data["reviews"] = []
        if "tickets" not in self.data:
            self.data["tickets"] = {}
        if "pending_payments" not in self.data:
            self.data["pending_payments"] = {}
        self._save()
    
    # === ПОЛЬЗОВАТЕЛИ ===
    def add_user(self, user_id: int, username: str = None):
        if str(user_id) not in self.data["users"]:
            self.data["users"][str(user_id)] = {
                "username": username,
                "joined": datetime.now().isoformat(),
                "purchases": []
            }
            self._save()
    
    def get_users_count(self) -> int:
        return len(self.data["users"])
    
    def get_all_users(self) -> Dict:
        return self.data["users"]
    
    # === ПРОДАВЦЫ ===
    def get_sellers(self) -> Dict:
        return self.data["sellers"]
    
    def add_seller(self, seller_id: str, name: str, price: float):
        self.data["sellers"][seller_id] = {"name": name, "price": price, "keys": []}
        self._save()
    
    def remove_seller(self, seller_id: str):
        if seller_id in self.data["sellers"]:
            del self.data["sellers"][seller_id]
            self._save()
            return True
        return False
    
    def generate_keys(self, seller_id: str, count: int = 10):
        """Генерирует ключи формата XXXXXXXXXX:xxxxxxxx"""
        keys = []
        for _ in range(count):
            part1 = ''.join(random.choices(string.ascii_uppercase, k=10))
            part2 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            keys.append(f"{part1}:{part2}")
        
        self.data["sellers"][seller_id]["keys"].extend(keys)
        self._save()
        return keys
    
    def get_key(self, seller_id: str) -> str:
        """Выдает один ключ и удаляет его"""
        keys = self.data["sellers"][seller_id]["keys"]
        if keys:
            key = keys.pop(0)
            self._save()
            return key
        return None
    
    def get_keys_count(self, seller_id: str) -> int:
        return len(self.data["sellers"][seller_id]["keys"])
    
    # === ОТЗЫВЫ ===
    def add_review(self, user_id: int, text: str, username: str = None):
        review = {
            "id": len(self.data["reviews"]) + 1,
            "user_id": user_id,
            "username": username,
            "text": text,
            "date": datetime.now().isoformat()
        }
        self.data["reviews"].append(review)
        self._save()
        return review["id"]
    
    def delete_review(self, review_id: int):
        self.data["reviews"] = [r for r in self.data["reviews"] if r["id"] != review_id]
        self._save()
    
    def edit_review(self, review_id: int, new_text: str):
        for r in self.data["reviews"]:
            if r["id"] == review_id:
                r["text"] = new_text
                r["edited"] = datetime.now().isoformat()
                self._save()
                return True
        return False
    
    def get_reviews(self) -> List[Dict]:
        return self.data["reviews"][-20:]  # Последние 20
    
    def get_review_by_id(self, review_id: int) -> Dict:
        for r in self.data["reviews"]:
            if r["id"] == review_id:
                return r
        return None
    
    # === ТЕХПОДДЕРЖКА ===
    def create_ticket(self, user_id: int, message: str) -> int:
        ticket_id = len(self.data["tickets"]) + 1
        self.data["tickets"][ticket_id] = {
            "user_id": user_id,
            "message": message,
            "status": "open",
            "created": datetime.now().isoformat(),
            "responses": []
        }
        self._save()
        return ticket_id
    
    def get_ticket(self, ticket_id: int) -> Dict:
        return self.data["tickets"].get(ticket_id)
    
    def add_response(self, ticket_id: int, admin_id: int, text: str):
        if ticket_id in self.data["tickets"]:
            self.data["tickets"][ticket_id]["responses"].append({
                "admin_id": admin_id,
                "text": text,
                "date": datetime.now().isoformat()
            })
            self._save()
    
    def close_ticket(self, ticket_id: int):
        if ticket_id in self.data["tickets"]:
            self.data["tickets"][ticket_id]["status"] = "closed"
            self._save()
    
    def get_open_tickets(self) -> Dict:
        return {k: v for k, v in self.data["tickets"].items() if v["status"] == "open"}
    
    # === ПЛАТЕЖИ ===
    def create_payment(self, user_id: int, seller_id: str, amount: float, quantity: int) -> str:
        payment_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        self.data["pending_payments"][payment_id] = {
            "user_id": user_id,
            "seller_id": seller_id,
            "amount": amount,
            "quantity": quantity,
            "status": "pending",
            "created": datetime.now().isoformat()
        }
        self._save()
        return payment_id
    
    def get_payment(self, payment_id: str) -> Dict:
        return self.data["pending_payments"].get(payment_id)
    
    def confirm_payment(self, payment_id: str):
        if payment_id in self.data["pending_payments"]:
            self.data["pending_payments"][payment_id]["status"] = "confirmed"
            self._save()
    
    def add_purchase(self, user_id: int, seller_id: str, keys: list, amount: float):
        purchase = {
            "seller_id": seller_id,
            "keys": keys,
            "amount": amount,
            "date": datetime.now().isoformat()
        }
        self.data["users"][str(user_id)]["purchases"].append(purchase)
        self._save()

db = Database()