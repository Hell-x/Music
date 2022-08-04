from typing import Dict
from ..helper import queue
from .. import PyCalls, client
from pytgcalls import GroupCallFactory


instances: Dict[int, GroupCallFactory] = {}
active_chats: Dict[int, Dict[str, bool]] = {}


def init_instance(chat_id: int):
    if chat_id not in instances:
        instances[chat_id] = PyCalls
    instance = instances[chat_id]

    @instance.on_playout_ended
    async def ___(__, _):
        queue.task_done(chat_id)
        if queue.is_empty(chat_id):
            await stop(chat_id)
        else:
            instance.input_filename = queue.get(chat_id)["file"]


def remove(chat_id: int):
    if chat_id in instances:
        del instances[chat_id]
    if not queue.is_empty(chat_id):
        queue.clear(chat_id)
    if chat_id in active_chats:
        del active_chats[chat_id]


def get_instance(chat_id: int) -> GroupCallFactory:
    init_instance(chat_id)
    return instances[chat_id]


async def start(chat_id: int):
    await get_instance(chat_id).start(chat_id)
    active_chats[chat_id] = {"playing": True, "muted": False}


async def stop(chat_id: int):
    await get_instance(chat_id).stop()
    if chat_id in active_chats:
        del active_chats[chat_id]


async def set_stream(chat_id: int, file: str):
    if chat_id not in active_chats:
        await start(chat_id)
    get_instance(chat_id).input_filename = file


def pause(chat_id: int) -> bool:
    if chat_id not in active_chats:
        return False
    elif not active_chats[chat_id]["playing"]:
        return False
    get_instance(chat_id).pause_playout()
    active_chats[chat_id]["playing"] = False
    return True


def resume(chat_id: int) -> bool:
    if chat_id not in active_chats:
        return False
    elif active_chats[chat_id]["playing"]:
        return False
    get_instance(chat_id).resume_playout()
    active_chats[chat_id]["playing"] = True
    return True


def mute(chat_id: int) -> int:
    if chat_id not in active_chats:
        return 2
    elif active_chats[chat_id]["muted"]:
        return 1
    get_instance(chat_id).set_is_mute(True)
    active_chats[chat_id]["muted"] = True
    return 0


def unmute(chat_id: int) -> int:
    if chat_id not in active_chats:
        return 2
    elif not active_chats[chat_id]["muted"]:
        return 1
    get_instance(chat_id).set_is_mute(False)
    active_chats[chat_id]["muted"] = False
    return 0
