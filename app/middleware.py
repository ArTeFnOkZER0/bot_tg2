from aiogram import BaseMiddleware
from aiogram.types import Message
import logging


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, message: Message, data: dict):
        logging.info(f"User {message.from_user.username or message.from_user.first_name} написал: {message.text}")
        return await handler(message,data)
