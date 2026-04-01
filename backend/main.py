"""
main.py — FastAPI 入口
"""
import asyncio
import io
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# 优先加载项目根目录的 .env 文件
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

from backend import session as sess
from backend.agent import run_agent
from backend.tools import run_script

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
VENV_PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python"

app = FastAPI(title="NL-PSD Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────── Sessions ────────────────

@app.post("/api/sessions")
def create_session():
    return sess.create_session()


@app.get("/api/sessions/{sid}")
def get_session(sid: str):
    try:
        return sess.get_state(sid)
    except FileNotFoundError:
        raise HTTPException(404, "Session not found")


@app.delete("/api/sessions/{sid}")
def delete_session(sid: str):
    sess.delete_session(sid)
    return {"ok": True}


@app.post("/api/sessions/{sid}/clear-history")
def clear_history(sid: str):
    """清空对话历史"""
    try:
        sess.get_state(sid)
    except FileNotFoundError:
        raise HTTPException(404, "Session not found")

    sess.clear_conversation_history(sid)
    return {"ok": True}


@app.get("/api/sessions/{sid}/history")
def get_history(sid: str):
    """获取对话历史（用于调试）"""
    try:
        sess.get_state(sid)
    except FileNotFoundError:
        raise HTTPException(404, "Session not found")

    history = sess.get_conversation_history(sid)
    return {"history": history, "count": len(history)}



# ──────────────── File Upload ────────────────

@app.post("/api/sessions/{sid}/upload")
async def upload_psd(sid: str, file: UploadFile = File(...)):
    try:
        sess.get_state(sid)
    except FileNotFoundError:
        raise HTTPException(404, "Session not found")

    content = await file.read()
    psd_path = sess.save_uploaded_file(sid, content, file.filename)

    # 生成初始预览
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _generate_preview, sid, str(psd_path))

    return sess.get_state(sid)


def _generate_preview(sid: str, psd_path: str):
    preview_out = str(sess.get_preview_path(sid))
    run_script("preview.py", [psd_path, "--output", preview_out], timeout=180)


# ──────────────── Preview ────────────────

@app.get("/api/sessions/{sid}/preview")
def get_preview(sid: str, t: str = ""):
    preview = sess.get_preview_path(sid)
    if not preview.exists():
        raise HTTPException(404, "Preview not available")
    return FileResponse(
        str(preview),
        media_type="image/png",
        headers={"Cache-Control": "no-cache, no-store"},
    )


# ──────────────── Undo / Redo ────────────────

@app.post("/api/sessions/{sid}/undo")
async def undo(sid: str):
    try:
        state = sess.get_state(sid)
    except FileNotFoundError:
        raise HTTPException(404, "Session not found")

    ok = sess.undo(sid)
    if not ok:
        raise HTTPException(400, "Nothing to undo")

    psd_path = str(sess.get_current_psd(sid))
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _generate_preview, sid, psd_path)
    return sess.get_state(sid)


@app.post("/api/sessions/{sid}/redo")
async def redo(sid: str):
    try:
        sess.get_state(sid)
    except FileNotFoundError:
        raise HTTPException(404, "Session not found")

    ok = sess.redo(sid)
    if not ok:
        raise HTTPException(400, "Nothing to redo")

    psd_path = str(sess.get_current_psd(sid))
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _generate_preview, sid, psd_path)
    return sess.get_state(sid)


# ──────────────── Export ────────────────

@app.post("/api/sessions/{sid}/export")
async def export_file(sid: str, format: str = Query("png", pattern="^(png|jpg)$")):
    try:
        state = sess.get_state(sid)
    except FileNotFoundError:
        raise HTTPException(404, "Session not found")

    if not state["has_file"]:
        raise HTTPException(400, "No PSD file uploaded")

    psd_path = str(sess.get_current_psd(sid))
    tmp_dir = sess.get_session_path(sid) / ".tmp"
    output_path = str(tmp_dir / f"export.{format}")

    args = [psd_path, output_path]
    if format == "jpg":
        args += ["--quality", "90"]

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: run_script("export.py", args))

    out = Path(output_path)
    if not out.exists():
        raise HTTPException(500, "Export failed")

    media_type = "image/png" if format == "png" else "image/jpeg"
    filename = state.get("filename", "export").rsplit(".", 1)[0] + f".{format}"
    return FileResponse(
        output_path,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ──────────────── SSE Chat ────────────────

@app.get("/api/sessions/{sid}/chat")
async def chat(sid: str, message: str = Query(...)):
    try:
        state = sess.get_state(sid)
    except FileNotFoundError:
        raise HTTPException(404, "Session not found")

    if not state["has_file"]:
        raise HTTPException(400, "No PSD file uploaded")

    async def event_stream():
        async for chunk in run_agent(sid, message):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ──────────────── Static Files (前端) ────────────────

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
