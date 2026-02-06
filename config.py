import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    # Переменные окружения (Railway их подставит)
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    
    # Цены в USDT
    PRICES = {
        "seller_1": 2.0,
        "seller_2": 3.0,
        "seller_3": 4.0
    }
    
    # Кошелёк для оплаты
    USDT_WALLET: str = os.getenv("USDT_WALLET", "")

cfg = Config()

# import os
# from dataclasses import dataclass

# @dataclass(frozen=True)
# class Config:
#     BOT_TOKEN: str = "8446452942:AAH-_TMVV1mjvL6DZYzyXjIWqNzJ3pVmBIc"
#     ADMIN_ID: int = 8226794980  # Твой Telegram ID
    
#     # Цены в USDT
#     PRICES = {
#         "seller_1": 2.0,
#         "seller_2": 3.0, 
#         "seller_3": 4.0
#     }
    
#     # Кошелек для оплаты
#     USDT_WALLET = "YTGQbQdq6Guhegpz1fDGQQjnWavc86m7agR"

# cfg = Config()