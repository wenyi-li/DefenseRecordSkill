#!/usr/bin/env python3
"""Transcribe defense audio/video with iFlytek Long Form ASR.

Credentials are read from:
  - XFYUN_APP_ID
  - XFYUN_SECRET_KEY
  - or defense-recorder/.env

The script uploads a local media file to iFlytek's recorded-audio
transcription API, polls for completion, and writes normalized transcript
files for the defense-recorder skill.

This script intentionally targets iFlytek 录音文件转写 / RAASR, not the
spark_zh_iat 中英识别大模型 endpoint. The IAT endpoint is a WebSocket
streaming API for audio up to 60 seconds and uses APIKey/APISecret based
authorization; RAASR is the appropriate API for full defense recordings.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import math
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional


UPLOAD_URL = "https://raasr.xfyun.cn/v2/api/upload"
RESULT_URL = "https://raasr.xfyun.cn/v2/api/getResult"


def normalize_credential(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip().lstrip("\ufeff").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()
    return value or None


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = normalize_credential(value)
        if key and value:
            values[key] = value
    return values


def load_credentials(media_arg: str) -> tuple[Optional[str], Optional[str], Optional[Path]]:
    skill_env = Path(__file__).resolve().parents[1] / ".env"
    search_paths = [
        skill_env,
        Path.cwd() / ".env",
        Path(media_arg).expanduser().resolve().parent / ".env",
    ]
    for path in search_paths:
        values = parse_dotenv(path)
        appid = normalize_credential(os.environ.get("XFYUN_APP_ID")) or values.get("XFYUN_APP_ID")
        secret_key = normalize_credential(os.environ.get("XFYUN_SECRET_KEY")) or values.get("XFYUN_SECRET_KEY")
        if appid and secret_key:
            return appid, secret_key, path
    return normalize_credential(os.environ.get("XFYUN_APP_ID")), normalize_credential(
        os.environ.get("XFYUN_SECRET_KEY")
    ), None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe audio/video through iFlytek recorded-audio transcription API."
    )
    parser.add_argument("media", help="Path to audio or video file.")
    parser.add_argument(
        "--service",
        default="raasr",
        choices=["raasr", "iat"],
        help=(
            "iFlytek service to use. raasr is the recorded-audio transcription API "
            "for long files. iat is only documented here as unsupported for defense "
            "recordings because it accepts audio up to 60 seconds."
        ),
    )
    parser.add_argument("-o", "--output-dir", default="transcript_output", help="Output directory.")
    parser.add_argument("--appid", default=None, help="iFlytek APP ID. Defaults to env/.env.")
    parser.add_argument(
        "--secret-key",
        default=None,
        help=(
            "iFlytek 录音文件转写/RAASR SecretKey. Do not pass the IAT APISecret "
            "or APIKey here. Defaults to env/.env."
        ),
    )
    parser.add_argument("--language", default="cn", help="Language code, e.g. cn, en.")
    parser.add_argument(
        "--role-type",
        default="1",
        choices=["0", "1"],
        help="Enable role separation: 1 enabled, 0 disabled. Requires account permission.",
    )
    parser.add_argument(
        "--role-num",
        default="0",
        help="Expected speaker count, 0 for blind separation, range 0-10.",
    )
    parser.add_argument(
        "--pd",
        default="edu",
        help="Domain parameter, e.g. edu, tech, medical. Default: edu.",
    )
    parser.add_argument(
        "--language-type",
        default="1",
        help="For cn: 1 auto CN/EN, 2 Chinese with some English, 4 pure Chinese.",
    )
    parser.add_argument("--hotword", default="", help="Hot words separated by |.")
    parser.add_argument(
        "--duration",
        default="auto",
        help=(
            "Audio duration parameter in seconds. Default: auto-detect with ffprobe. "
            "Use a number to override."
        ),
    )
    parser.add_argument("--poll-interval", type=int, default=30, help="Polling interval in seconds.")
    parser.add_argument("--max-polls", type=int, default=100, help="Maximum result polling attempts.")
    parser.add_argument(
        "--auth-debug",
        action="store_true",
        help="Print non-secret authentication diagnostics before upload.",
    )
    parser.add_argument(
        "--auth-check",
        action="store_true",
        help="Print non-secret authentication diagnostics and exit without uploading.",
    )
    return parser.parse_args()


def sign(appid: str, secret_key: str, ts: str) -> str:
    base = (appid + ts).encode("utf-8")
    md5 = hashlib.md5(base).hexdigest().encode("utf-8")
    digest = hmac.new(secret_key.encode("utf-8"), md5, hashlib.sha1).digest()
    return base64.b64encode(digest).decode("utf-8")


def request_json(
    url: str,
    params: dict[str, str],
    data: Optional[bytes] = None,
    content_type: Optional[str] = None,
    method: Optional[str] = None,
) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    request_url = f"{url}?{query}"
    headers = {}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(
        request_url,
        data=data,
        headers=headers,
        method=method or ("POST" if data else "GET"),
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Non-JSON response: {body[:500]}") from exc


def auth_params(appid: str, secret_key: str) -> dict[str, str]:
    ts = str(int(time.time()))
    return {"appId": appid, "ts": ts, "signa": sign(appid, secret_key, ts)}


def auth_error_hint(response: dict[str, Any]) -> str:
    response_text = json.dumps(response, ensure_ascii=False)
    if "signa verify fail" not in response_text and "签名" not in response_text:
        return ""
    return (
        "\nAuthentication hint: iFlytek returned a signature verification error. "
        "This script calls 录音文件转写/RAASR at raasr.xfyun.cn and signs requests with "
        "signa=base64(HmacSHA1(MD5(appId+ts), SecretKey)). Use the SecretKey shown "
        "on the RAASR service page, not the spark_zh_iat APIKey/APISecret; make sure "
        "APPID and RAASR SecretKey belong to the same iFlytek app, and re-run "
        "scripts/setup_xfyun_env.py if .env was edited manually."
    )


def print_auth_debug(appid: str, secret_key: str) -> None:
    sample_signa = sign("595f23df", "d9f4aa7ea6d94faca62cd88a28fd5234", "1512041814")
    print(
        "Auth debug: "
        f"appid_len={len(appid)}, secret_key_len={len(secret_key)}, "
        f"official_sample_ok={sample_signa == 'IrrzsJeOFk1NGfJHW6SkHUoN9CU='}",
        file=sys.stderr,
    )


def probe_duration_seconds(media: Path) -> Optional[float]:
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(media),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def validate_service_choice(args: argparse.Namespace, media: Path) -> None:
    duration = probe_duration_seconds(media)
    duration_note = ""
    if duration is not None:
        duration_note = f" Detected media duration: {duration:.2f}s."

    if args.service == "iat":
        raise RuntimeError(
            "The spark_zh_iat 中英识别大模型 endpoint is not supported by this script for "
            "defense recordings. That endpoint is a WebSocket streaming API with a 60s "
            "audio limit and uses APIKey/APISecret authorization, while this skill needs "
            "long-file transcription with timestamps and optional role separation."
            f"{duration_note} Use --service raasr with the 录音文件转写/RAASR SecretKey."
        )

    if duration is not None and duration <= 60:
        print(
            "Note: media is 60s or shorter. This script still uses RAASR because "
            "defense-recorder expects file transcription outputs; spark_zh_iat uses "
            "a different WebSocket protocol and credential type.",
            file=sys.stderr,
        )


def upload(args: argparse.Namespace, media: Path) -> tuple[str, int]:
    params = auth_params(args.appid, args.secret_key)
    duration = args.duration
    if str(duration).lower() == "auto":
        probed_duration = probe_duration_seconds(media)
        duration = str(max(1, math.ceil(probed_duration))) if probed_duration else "1"
    params.update(
        {
            "fileName": media.name,
            "fileSize": str(media.stat().st_size),
            "duration": str(duration),
            "language": args.language,
            "roleType": args.role_type,
            "roleNum": args.role_num,
            "pd": args.pd,
            "languageType": args.language_type,
            "audioMode": "fileStream",
        }
    )
    if args.hotword:
        params["hotWord"] = args.hotword

    response = request_json(UPLOAD_URL, params, media.read_bytes(), "application/octet-stream")
    if response.get("code") != "000000":
        raise RuntimeError(f"Upload failed: {json.dumps(response, ensure_ascii=False)}{auth_error_hint(response)}")
    content = response.get("content") or {}
    order_id = content.get("orderId")
    if not order_id:
        raise RuntimeError(f"Upload response missing orderId: {json.dumps(response, ensure_ascii=False)}")
    estimate_ms = int(content.get("taskEstimateTime") or 0)
    return str(order_id), estimate_ms


def get_result(args: argparse.Namespace, order_id: str) -> dict[str, Any]:
    params = auth_params(args.appid, args.secret_key)
    params.update({"orderId": order_id, "resultType": "transfer"})
    response = request_json(RESULT_URL, params, method="GET")
    if response.get("code") != "000000":
        code = response.get("code")
        if code == "26605":
            return response
        raise RuntimeError(
            f"getResult failed: {json.dumps(response, ensure_ascii=False)}{auth_error_hint(response)}"
        )
    return response


def wait_for_result(args: argparse.Namespace, order_id: str, estimate_ms: int) -> dict[str, Any]:
    initial_sleep = min(max(estimate_ms / 1000, args.poll_interval), 120) if estimate_ms else args.poll_interval
    print(f"Order created: {order_id}", file=sys.stderr)
    print(f"Waiting {int(initial_sleep)}s before first result poll.", file=sys.stderr)
    time.sleep(initial_sleep)

    for attempt in range(1, args.max_polls + 1):
        response = get_result(args, order_id)
        content = response.get("content") or {}
        order_info = content.get("orderInfo") or {}
        status = order_info.get("status")
        fail_type = order_info.get("failType")
        print(f"Poll {attempt}/{args.max_polls}: status={status}, failType={fail_type}", file=sys.stderr)
        if status == 4:
            return response
        if status == -1:
            raise RuntimeError(f"Transcription failed: {json.dumps(response, ensure_ascii=False)}")
        time.sleep(args.poll_interval)
    raise TimeoutError(f"Result not ready after {args.max_polls} polls. orderId={order_id}")


def seconds_from_ms(value: Any) -> float:
    try:
        return float(value) / 1000.0
    except (TypeError, ValueError):
        return 0.0


def fmt_time(seconds: float) -> str:
    seconds = max(0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def words_from_st(st: dict[str, Any]) -> str:
    chunks: list[str] = []
    for rt in st.get("rt", []):
        for ws in rt.get("ws", []):
            for cw in ws.get("cw", []):
                word = str(cw.get("w", ""))
                if word:
                    chunks.append(word)
    return "".join(chunks).strip()


def parse_order_result(content: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    raw_order_result = content.get("orderResult")
    if not raw_order_result:
        return [], {}
    order_result = json.loads(raw_order_result) if isinstance(raw_order_result, str) else raw_order_result
    lattice = order_result.get("lattice2") or order_result.get("lattice") or []
    segments: list[dict[str, str]] = []

    for index, item in enumerate(lattice, start=1):
        raw_best = item.get("json_1best")
        best = json.loads(raw_best) if isinstance(raw_best, str) else raw_best
        st = (best or {}).get("st", {})
        begin = item.get("begin") or item.get("bg") or st.get("bg")
        end = item.get("end") or item.get("ed") or st.get("ed")
        speaker = item.get("spk") or st.get("rl") or st.get("pa") or "SPEAKER_UNKNOWN"
        if speaker and not str(speaker).startswith("SPEAKER") and not str(speaker).startswith("段落"):
            speaker = f"SPEAKER_{speaker}"
        text = words_from_st(st)
        if not text:
            continue
        segments.append(
            {
                "index": str(index),
                "start": fmt_time(seconds_from_ms(begin)),
                "end": fmt_time(seconds_from_ms(end)),
                "speaker": str(speaker),
                "text": text,
            }
        )
    return segments, order_result


def write_outputs(segments: list[dict[str, str]], raw_response: dict[str, Any], raw_order_result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "raw_response.json").write_text(
        json.dumps(raw_response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "raw_order_result.json").write_text(
        json.dumps(raw_order_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "transcript.json").write_text(
        json.dumps(segments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with (output_dir / "transcript.md").open("w", encoding="utf-8") as f:
        f.write("# Transcript\n\n")
        for seg in segments:
            f.write(f"[{seg['start']} - {seg['end']}] {seg['speaker']}: {seg['text']}\n\n")

    with (output_dir / "transcript.srt").open("w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = seg["start"].replace(".", ",")
            end = seg["end"].replace(".", ",")
            f.write(f"{i}\n{start} --> {end}\n{seg['speaker']}: {seg['text']}\n\n")

    print(f"Wrote transcript files to {output_dir}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    dotenv_appid, dotenv_secret_key, dotenv_path = load_credentials(args.media)
    args.appid = normalize_credential(args.appid) or dotenv_appid
    args.secret_key = normalize_credential(args.secret_key) or dotenv_secret_key
    if not args.appid or not args.secret_key:
        print("Missing iFlytek credentials.", file=sys.stderr)
        print(
            "Run setup once, or set environment variables for 录音文件转写/RAASR before transcription:",
            file=sys.stderr,
        )
        print("  python3 defense-recorder/scripts/setup_xfyun_env.py", file=sys.stderr)
        print("This writes credentials to defense-recorder/.env by default.", file=sys.stderr)
        print("If .env does not exist, follow the iFlytek RAASR API docs first:", file=sys.stderr)
        print("  https://www.xfyun.cn/doc/asr/ifasr_new/API.html", file=sys.stderr)
        print('  export XFYUN_APP_ID="your_app_id"', file=sys.stderr)
        print('  export XFYUN_SECRET_KEY="your_raasr_secret_key"', file=sys.stderr)
        print("Do not use spark_zh_iat APIKey/APISecret for XFYUN_SECRET_KEY.", file=sys.stderr)
        return 2
    if dotenv_path:
        print(f"Loaded iFlytek credentials from {dotenv_path}", file=sys.stderr)
    if args.auth_debug or args.auth_check:
        print_auth_debug(args.appid, args.secret_key)
    if args.auth_check:
        return 0

    media = Path(args.media).expanduser().resolve()
    if not media.exists():
        print(f"Media file not found: {media}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir).expanduser().resolve()
    try:
        validate_service_choice(args, media)
        order_id, estimate_ms = upload(args, media)
        response = wait_for_result(args, order_id, estimate_ms)
        content = response.get("content") or {}
        segments, raw_order_result = parse_order_result(content)
        if not segments:
            raise RuntimeError("No transcript segments parsed from iFlytek result.")
        write_outputs(segments, response, raw_order_result, output_dir)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
