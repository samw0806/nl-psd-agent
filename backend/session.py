"""
session.py — Session 管理：文件存储、版本快照、undo/redo
"""
import json
import shutil
import uuid
from pathlib import Path

SESSIONS_DIR = Path(__file__).parent.parent / "sessions"


def sessions_dir() -> Path:
    SESSIONS_DIR.mkdir(exist_ok=True)
    return SESSIONS_DIR


def create_session() -> dict:
    sid = str(uuid.uuid4())
    base = sessions_dir() / sid
    (base / "history").mkdir(parents=True)
    (base / ".tmp").mkdir()
    state = {
        "version": -1,
        "undo_stack": [],
        "redo_stack": [],
        "filename": None,
        "conversation_history": []
    }
    _write_state(sid, state)
    return {"session_id": sid}


def get_session_path(sid: str) -> Path:
    return sessions_dir() / sid


def get_current_psd(sid: str) -> Path:
    return get_session_path(sid) / "current.psd"


def get_preview_path(sid: str) -> Path:
    return get_session_path(sid) / ".tmp" / "preview.png"


def _state_path(sid: str) -> Path:
    return get_session_path(sid) / "state.json"


def _read_state(sid: str) -> dict:
    p = _state_path(sid)
    if not p.exists():
        raise FileNotFoundError(f"Session {sid} not found")
    return json.loads(p.read_text())


def _write_state(sid: str, state: dict):
    _state_path(sid).write_text(json.dumps(state, ensure_ascii=False, indent=2))


def get_state(sid: str) -> dict:
    state = _read_state(sid)
    return {
        "session_id": sid,
        "version": state["version"],
        "filename": state.get("filename"),
        "can_undo": len(state["undo_stack"]) > 0,
        "can_redo": len(state["redo_stack"]) > 0,
        "has_file": get_current_psd(sid).exists(),
    }


def save_uploaded_file(sid: str, content: bytes, filename: str) -> Path:
    """保存上传的 PSD 文件，初始化版本历史"""
    base = get_session_path(sid)
    current = base / "current.psd"
    current.write_bytes(content)

    state = _read_state(sid)
    state["version"] = 0
    state["filename"] = filename
    state["undo_stack"] = []
    state["redo_stack"] = []
    # 保存 v0 快照
    shutil.copy(current, base / "history" / "v0.psd")
    _write_state(sid, state)
    return current


def snapshot_before_edit(sid: str):
    """在修改前拍快照，清空 redo stack，版本号 +1"""
    state = _read_state(sid)
    current = get_current_psd(sid)
    if not current.exists():
        return

    old_version = state["version"]
    new_version = old_version + 1
    base = get_session_path(sid)

    # 先把当前文件存入 undo 历史
    shutil.copy(current, base / "history" / f"v{old_version}.psd")
    state["undo_stack"].append(old_version)
    state["redo_stack"] = []
    state["version"] = new_version
    _write_state(sid, state)


def undo(sid: str) -> bool:
    state = _read_state(sid)
    if not state["undo_stack"]:
        return False

    base = get_session_path(sid)
    current = get_current_psd(sid)

    restore_version = state["undo_stack"].pop()
    state["redo_stack"].append(state["version"])
    state["version"] = restore_version
    shutil.copy(base / "history" / f"v{restore_version}.psd", current)
    _write_state(sid, state)
    return True


def redo(sid: str) -> bool:
    state = _read_state(sid)
    if not state["redo_stack"]:
        return False

    base = get_session_path(sid)
    current = get_current_psd(sid)

    restore_version = state["redo_stack"].pop()
    state["undo_stack"].append(state["version"])
    state["version"] = restore_version
    shutil.copy(base / "history" / f"v{restore_version}.psd", current)
    _write_state(sid, state)
    return True


def delete_session(sid: str):
    base = get_session_path(sid)
    if base.exists():
        shutil.rmtree(base)


# ──────────────── Conversation History ────────────────


def get_conversation_history(sid: str) -> list:
    """获取对话历史"""
    state = _read_state(sid)
    return state.get("conversation_history", [])


def save_conversation_history(sid: str, messages: list):
    """保存对话历史"""
    state = _read_state(sid)
    state["conversation_history"] = messages
    _write_state(sid, state)


def clear_conversation_history(sid: str):
    """清空对话历史"""
    state = _read_state(sid)
    state["conversation_history"] = []
    _write_state(sid, state)

