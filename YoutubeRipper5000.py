#!/usr/bin/env python3
"""
YouTube Ripper using yt-dlp as a Python module.

- Prompts for a YouTube URL (or accepts via CLI arg).
- Validates URL format.
- Creates a Downloads folder next to the script.
- Forces overwrite, retries, and saves metadata + thumbnail.
- Logs output to a file for auditability.
- Uses local ffmpeg.exe in the same directory as this script.
"""

import re
import sys
import datetime
from pathlib import Path
import yt_dlp

# -------- Settings (toggles) --------
SETTINGS = {
    "format": "bv*+ba/best",          # Best video+audio
    "merge_output_format": "mp4",     # Final container
    "force_overwrites": True,
    "no_continue": True,
    "ignoreerrors": True,
    "retries": 10,
    "fragment_retries": 10,
    "writethumbnail": True,
    "writeinfojson": True,
    "embedthumbnail": True,
    "restrictfilenames": True,
}

# -------- URL validation --------
YOUTUBE_PATTERNS = [
    r"^https?://(www\.)?youtube\.com/watch\?v=[^&\s]+",
    r"^https?://(www\.)?youtube\.com/playlist\?list=[^&\s]+",
    r"^https?://(m\.)?youtube\.com/watch\?v=[^&\s]+",
    r"^https?://(www\.)?youtu\.be/[^?\s]+",
]

def is_valid_youtube_url(url: str) -> bool:
    return any(re.match(p, url) for p in YOUTUBE_PATTERNS)

# -------- Output folder + logging --------
def get_download_folder() -> Path:
    # Always use a "Downloads" folder next to the script
    script_dir = Path(__file__).resolve().parent
    outdir = script_dir / "Downloads"
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir

def make_log_file(outdir: Path) -> Path:
    return outdir / f"download_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# -------- Main --------
def main():
    # Get URL
    url = sys.argv[1] if len(sys.argv) > 1 else input("Paste a YouTube URL: ").strip()

    if not is_valid_youtube_url(url):
        print("Invalid or unsupported YouTube URL.")
        sys.exit(1)

    # Prepare output folder + log
    outdir = get_download_folder()
    logpath = make_log_file(outdir)

    print(f"Output folder: {outdir}")
    print(f"Log file: {logpath}")

    # Path to ffmpeg.exe in the same directory as this script
    script_dir = Path(__file__).resolve().parent
    ffmpeg_path = script_dir / "ffmpeg.exe"
    if not ffmpeg_path.exists():
        print(f"⚠️ ffmpeg.exe not found in {script_dir}. Please place ffmpeg.exe next to this script.")
        sys.exit(1)

    # yt-dlp options (now correctly indented inside main)
    ydl_opts = {
        "format": SETTINGS["format"],
        "merge_output_format": SETTINGS["merge_output_format"],
        # Save each video in its own subfolder under Downloads
        "outtmpl": str(outdir / "%(title)s" / "%(title)s.%(ext)s"),
        "writethumbnail": SETTINGS["writethumbnail"],
        "writeinfojson": SETTINGS["writeinfojson"],
        "embedthumbnail": SETTINGS["embedthumbnail"],
        "restrictfilenames": SETTINGS["restrictfilenames"],
        "retries": SETTINGS["retries"], 
        "fragment_retries": SETTINGS["fragment_retries"],
        "ignoreerrors": SETTINGS["ignoreerrors"],
        "nooverwrites": not SETTINGS["force_overwrites"],
        "continuedl": not SETTINGS["no_continue"],
        "ffmpeg_location": str(ffmpeg_path),
        "logger": None,
    }

    # Custom logger to also write to file
    class FileLogger:
        def __init__(self, logfile): self.logfile = logfile
        def debug(self, msg): self._write("DEBUG", msg)
        def warning(self, msg): self._write("WARN", msg)
        def error(self, msg): self._write("ERROR", msg)
        def _write(self, level, msg):
            line = f"[{datetime.datetime.now()}] [{level}] {msg}"
            print(line)
            with open(self.logfile, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    ydl_opts["logger"] = FileLogger(logpath)

    # Run download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.download([url])

    if result == 0:
        print("✅ Download complete.")
    else:
        print(f"⚠️ Download finished with exit code {result}. See log for details.")

if __name__ == "__main__":
    main()