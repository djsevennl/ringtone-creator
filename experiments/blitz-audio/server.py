"""Isolated, metadata-only YouTube connectivity probe. No audio downloads or storage."""
import asyncio
import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI(title="Ringtone Audio Probe")
allowed = os.environ.get("ALLOWED_ORIGIN", "https://ringtone-creator-audio-test.vercel.app")
app.add_middleware(CORSMiddleware, allow_origins=[allowed], allow_methods=["GET"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"ok": True, "mode": "metadata-only", "downloads": False}

def probe(video_id: str):
    with yt_dlp.YoutubeDL({
        "quiet": True, "no_warnings": True, "skip_download": True,
        "extract_flat": False, "socket_timeout": 8, "retries": 0,
        "noplaylist": True, "extractor_args": {"youtube": {"player_client": ["android", "web"]}}
    }) as ydl:
        info = ydl.extract_info("https://www.youtube.com/watch?v=" + video_id, download=False)
    formats = info.get("formats", [])
    audio = [f for f in formats if f.get("acodec") not in (None, "none") and f.get("url")]
    return {"ok": bool(audio), "title": str(info.get("title", ""))[:120],
            "audio_formats": len(audio), "downloads": False}

@app.get("/probe/{video_id}")
async def probe_route(video_id: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise HTTPException(status_code=400, detail="Invalid video ID")
    try:
        return await asyncio.wait_for(asyncio.to_thread(probe, video_id), timeout=20)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Probe timed out")
    except Exception:
        raise HTTPException(status_code=502, detail="YouTube extraction unavailable")
