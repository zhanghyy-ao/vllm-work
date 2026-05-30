from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List


def extract_video_keyframes(url: str, out_root: str = "runs/keyframes", max_frames: int = 3, timeout_sec: int = 45) -> Dict[str, Any]:
    """Best-effort video key-frame extraction.

    This is an optional multimodal enhancement. The browser/video workflow must
    keep working when local media tools are absent, so failures are returned as
    structured status instead of exceptions.
    """
    if not url:
        return {"ok": False, "status": "unavailable", "reason": "missing_video_url", "frames": []}
    ytdlp = shutil.which("yt-dlp")
    ffmpeg = shutil.which("ffmpeg")
    if not ytdlp:
        return {"ok": False, "status": "unavailable", "reason": "yt-dlp_not_installed", "frames": []}
    if not ffmpeg:
        return {"ok": False, "status": "unavailable", "reason": "ffmpeg_not_installed", "frames": []}

    run_dir = Path(out_root) / uuid.uuid4().hex[:10]
    run_dir.mkdir(parents=True, exist_ok=True)
    video_path = run_dir / "source.%(ext)s"
    download_cmd = [
        ytdlp,
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        "--download-sections",
        "*0:00-0:25",
        "-f",
        "bv*[height<=480]+ba/b[height<=480]/worst",
        "-o",
        str(video_path),
        url,
    ]
    try:
        completed = subprocess.run(download_cmd, check=False, capture_output=True, text=True, timeout=timeout_sec)
    except Exception as exc:
        return {"ok": False, "status": "failed", "reason": "yt-dlp_exception", "detail": str(exc), "frames": [], "output_dir": str(run_dir)}
    if completed.returncode != 0:
        return {
            "ok": False,
            "status": "failed",
            "reason": "yt-dlp_failed",
            "detail": (completed.stderr or completed.stdout)[-800:],
            "frames": [],
            "output_dir": str(run_dir),
        }

    source_files = [path for path in run_dir.iterdir() if path.is_file() and path.name.startswith("source.")]
    if not source_files:
        return {"ok": False, "status": "failed", "reason": "downloaded_video_not_found", "frames": [], "output_dir": str(run_dir)}
    source = source_files[0]
    frame_pattern = run_dir / "frame-%02d.jpg"
    fps = max(1, int(max_frames)) / 25
    ffmpeg_cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-vf",
        f"fps={fps},scale=640:-1",
        "-frames:v",
        str(max(1, min(max_frames, 6))),
        str(frame_pattern),
    ]
    try:
        completed = subprocess.run(ffmpeg_cmd, check=False, capture_output=True, text=True, timeout=timeout_sec)
    except Exception as exc:
        return {"ok": False, "status": "failed", "reason": "ffmpeg_exception", "detail": str(exc), "frames": [], "output_dir": str(run_dir)}
    frames = sorted(str(path) for path in run_dir.glob("frame-*.jpg"))
    if completed.returncode != 0 or not frames:
        return {
            "ok": False,
            "status": "failed",
            "reason": "ffmpeg_failed_or_no_frames",
            "detail": (completed.stderr or completed.stdout)[-800:],
            "frames": frames,
            "output_dir": str(run_dir),
        }
    return {
        "ok": True,
        "status": "available",
        "reason": "keyframes_extracted",
        "frames": frames[:max_frames],
        "output_dir": str(run_dir),
        "tools": {"yt-dlp": ytdlp, "ffmpeg": ffmpeg},
    }


def visual_inputs_from_video_digest(digest: Dict[str, Any]) -> List[str]:
    inputs: List[str] = []
    screenshot = digest.get("screenshot_path")
    if isinstance(screenshot, str) and screenshot:
        inputs.append(screenshot)
    keyframes = digest.get("keyframes")
    if isinstance(keyframes, dict):
        frames = keyframes.get("frames")
        if isinstance(frames, list):
            inputs.extend(str(frame) for frame in frames if frame)
    seen = set()
    deduped = []
    for item in inputs:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped
