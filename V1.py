
import csv
import os
import time
import datetime
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv

load_dotenv()

PLEX_URL = os.getenv("PLEX_URL", "http://127.0.0.1:32400").rstrip("/")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LOG_PATH = os.getenv("LOG_PATH", "./plex_sessions.csv")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))

HEADERS = {
    "X-Plex-Token": PLEX_TOKEN
}

def iso_now():
    # Includes timezone offset for readability in AU/Sydney
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=11))).isoformat()

def ensure_csv(path):
    exists = os.path.exists(path)
    if not exists:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp","user","device","title",
                "transcode_video","transcode_audio","decision",
                "video_resolution","video_codec","audio_codec",
                "bitrate_kbps","reasons"
            ])

def get_sessions():
    url = urljoin(PLEX_URL + "/", "status/sessions")
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()

def parse_session(media_container):
    """
    Plex returns a 'MediaContainer' with 'Metadata' list.
    Each item can have 'Player', 'User', 'TranscodeSession', 'Media', etc.
    """
    results = []
    md_list = media_container.get("MediaContainer", {}).get("Metadata", [])
    if not isinstance(md_list, list):
        md_list = [md_list] if md_list else []

    for md in md_list:
        user = (md.get("User") or {}).get("title", "Unknown")
        player = (md.get("Player") or {}).get("title", (md.get("Player") or {}).get("product", "Unknown"))
        title = md.get("title") or md.get("grandparentTitle") or "Unknown"

        # Decision: directplay/directstream/transcode
        decision = (md.get("Media", [{}])[0].get("Part", [{}])[0].get("Decision") or
                    (md.get("TranscodeSession") or {}).get("videoDecision") or "unknown").lower()

        t_session = md.get("TranscodeSession") or {}
        t_video = bool(t_session.get("videoDecision") == "transcode")
        t_audio = bool(t_session.get("audioDecision") == "transcode")

        media = (md.get("Media") or [{}])[0]
        video_res = f'{media.get("width","?")}x{media.get("height","?")}'
        video_codec = media.get("videoCodec", "?")
        audio_codec = (media.get("audioCodec") or
                       ((media.get("Part") or [{}])[0].get("Stream") or [{}])[0].get("codec", "?"))

        bitrate = media.get("bitrate") or (t_session.get("bitrate") and int(int(t_session["bitrate"]) / 1000))
        if isinstance(bitrate, str):
            try:
                bitrate = int(bitrate)
            except:
                bitrate = ""

        reasons = t_session.get("transcodeHwRequestedReason") or t_session.get("transcodeHwDecoding")
        # Fallback to reason codes from Part/Stream if available
        if not reasons:
            reasons = (media.get("Part") or [{}])[0].get("decision", "")

        results.append({
            "user": user,
            "device": player,
            "title": title,
            "transcode_video": str(t_video).lower(),
            "transcode_audio": str(t_audio).lower(),
            "decision": decision,
            "video_resolution": video_res,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "bitrate_kbps": bitrate if bitrate is not None else "",
            "reasons": reasons or ""
        })
    return results

def append_rows(rows):
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow([
                iso_now(),
                r["user"],
                r["device"],
                r["title"],
                r["transcode_video"],
                r["transcode_audio"],
                r["decision"],
                r["video_resolution"],
                r["video_codec"],
                r["audio_codec"],
                r["bitrate_kbps"],
                r["reasons"]
            ])

def main():
    if not PLEX_TOKEN:
        raise SystemExit("Missing PLEX_TOKEN. Set it in .env")

    ensure_csv(LOG_PATH)
    print(f"[plex-transcode-watchdog] Polling {PLEX_URL} every {POLL_SECONDS}s. Logging to {LOG_PATH}.")

    try:
        while True:
            try:
                data = get_sessions()
                rows = parse_session(data)
                if rows:
                    append_rows(rows)
                    print(f"{iso_now()} Logged {len(rows)} session(s).")
                else:
                    print(f"{iso_now()} No active sessions.")
            except Exception as e:
                print(f"{iso_now()} Error: {e}")
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == "__main__":
    main()
