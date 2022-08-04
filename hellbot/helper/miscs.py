import sys
import socket
import traceback
from functools import wraps
from pyrogram import Client
from .. import client, hellbot
from ..config import LOGGER_ID
from pyrogram.types import Message
from html_telegraph_poster import TelegraphPoster
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden


def get_file_id(msg: Message):
    if msg.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "sticker",
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj


def split_limits(text):
    if len(text) < 2048:
        return [text]
    lines = text.splitlines(True)
    small_msg = ""
    result = []
    for line in lines:
        if len(small_msg) + len(line) < 2048:
            small_msg += line
        else:
            result.append(small_msg)
            small_msg = line
    else:
        result.append(small_msg)
    return result


def capture_err(func):
    @wraps(func)
    async def capture(client, message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except ChatWriteForbidden:
            await hellbot.leave_chat(message.chat.id)
            await client.leave_chat(message.chat.id)
            return
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            errors = traceback.format_exception(
                etype=exc_type,
                value=exc_obj,
                tb=exc_tb,
            )
            error_feedback = split_limits(
                "**ERROR** | `{}` | `{}`\n\n```{}```\n\n```{}```\n".format(
                    0 if not message.from_user else message.from_user.id,
                    0 if not message.chat else message.chat.id,
                    message.text or message.caption,
                    "".join(errors),
                ),
            )
            for x in error_feedback:
                await hellbot.send_message(LOGGER_ID, x)
            raise err

    return capture


async def _netcat(host, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(content.encode())
    s.shutdown(socket.SHUT_WR)
    while True:
        data = s.recv(4096).decode("utf-8").strip("\n\x00")
        if not data:
            break
        return data
    s.close()


async def paste(content):
    link = await _netcat("ezup.dev", 9999, content)
    return link


async def clog(name: str, text: str, tag: str):
    log = f"#{name.upper()}  #{tag.upper()}\n\n{text}"
    await hellbot.send_message(LOGGER_ID, text=log)


async def telegraph_paste(page_title, temxt):
    cl1ent = TelegraphPoster(use_api=True)
    auth = "[ †hê Hêllẞø† ]"
    cl1ent.create_api_token(auth)
    post_page = cl1ent.post(
        title=page_title,
        author=auth,
        author_url="https://t.me/its_hellbot",
        text=temxt,
    )
    return post_page["url"]
