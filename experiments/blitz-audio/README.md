# Blitz audio probe (isolated test)
This container only tests whether yt-dlp can retrieve YouTube metadata and audio format information. It **does not download, convert, store or stream audio**. This prevents unexpected bandwidth usage while testing provider access.

Docker build context must be the **repository root**, Dockerfile path `experiments/blitz-audio/Dockerfile`. Run on the branch `test-audio-url-import-2026-10-10`, not main.

Health endpoint: `GET /health`
Test endpoint: `GET /probe/mfJhMfOPWdE`
Expected successful response contains `audio_formats > 0`; otherwise YouTube extraction may be blocked.

Before production use: add rate limits, authentication, constrained download size/time, and verify platform rules and costs. No live Ringtone Creator changes.
