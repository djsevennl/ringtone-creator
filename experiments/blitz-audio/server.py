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

@app.get("/probe-alt/{video_id}")
async def probe_alternative(video_id: str):
    """Try alternate official YouTube player clients; metadata only, no cookies."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise HTTPException(status_code=400, detail="Invalid video ID")
    results = []
    for client in ("web_safari", "ios"):
        def attempt():
            with yt_dlp.YoutubeDL({
                "quiet": True, "no_warnings": True, "skip_download": True,
                "socket_timeout": 5, "retries": 0, "noplaylist": True,
                "extractor_args": {"youtube": {"player_client": [client]}}
            }) as ydl:
                info = ydl.extract_info(
                    "https://www.youtube.com/watch?v=" + video_id, download=False)
            audio = [f for f in info.get("formats", [])
                     if f.get("acodec") not in (None, "none") and f.get("url")]
            return {"client": client, "ok": bool(audio),
                    "audio_formats": len(audio)}
        try:
            result = await asyncio.wait_for(asyncio.to_thread(attempt), timeout=9)
            results.append(result)
            if result["ok"]:
                break
        except Exception as exc:
            # Do not expose cookies, full upstream URLs, or internal tracebacks.
            reason = "youtube_bot_challenge" if ("not a bot" in str(exc).lower() or "sign in to confirm" in str(exc).lower()) else ("upstream_forbidden" if "403" in str(exc) else ("rate_limited" if "429" in str(exc) else ("timeout" if "timed out" in str(exc).lower() else "other")))
            results.append({"client": client, "ok": False,
                            "error_type": type(exc).__name__, "reason": reason})
    return {"ok": any(r["ok"] for r in results), "results": results,
            "downloads": False, "cookies": False}
