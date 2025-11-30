import hashlib
import hmac
import json
from urllib.parse import parse_qsl
from typing import Dict, Any, Optional
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TEST_TOKEN_HERE") 

def validate_init_data(init_data: str, bot_token: str = BOT_TOKEN) -> Optional[Dict[str, Any]]:
    """
    Валидирует данные initData от Telegram Mini App.
    Возвращает словарь с данными пользователя или None, если проверка не прошла.
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
        if "hash" not in parsed_data:
            return None

        received_hash = parsed_data.pop("hash")
        
        # Сортировка ключей по алфавиту
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )
        
        # Вычисление HMAC-SHA256
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        if calculated_hash == received_hash:
            # Парсим user объект из строки JSON
            user_data = json.loads(parsed_data.get("user", "{}"))
            return user_data
        return None
    except Exception as e:
        print(f"Auth error: {e}")
        return None

