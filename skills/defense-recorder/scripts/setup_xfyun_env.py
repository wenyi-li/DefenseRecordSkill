#!/usr/bin/env python3
"""Create defense-recorder/.env for iFlytek RAASR transcription credentials."""

from __future__ import annotations

import argparse
import getpass
from pathlib import Path


def parse_args() -> argparse.Namespace:
    default_env = Path(__file__).resolve().parents[1] / ".env"
    parser = argparse.ArgumentParser(
        description=(
            "Set up iFlytek 录音文件转写/RAASR credentials for defense-recorder. "
            "Do not use spark_zh_iat APIKey/APISecret here."
        )
    )
    parser.add_argument(
        "--output",
        default=str(default_env),
        help="Where to write credentials. Default: defense-recorder/.env.",
    )
    parser.add_argument("--appid", default="", help="iFlytek APP ID from the RAASR-enabled app.")
    parser.add_argument(
        "--secret-key",
        default="",
        help="iFlytek 录音文件转写/RAASR SecretKey, not spark_zh_iat APIKey/APISecret.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("Configure credentials for iFlytek 录音文件转写/RAASR.")
    print("Use the RAASR service page SecretKey. Do not enter spark_zh_iat APIKey or APISecret.")
    print("If you have not created credentials yet, see:")
    print("https://www.xfyun.cn/doc/asr/ifasr_new/API.html")
    appid = args.appid.strip() or input("XFYUN_APP_ID (RAASR-enabled app): ").strip()
    secret_key = args.secret_key.strip() or getpass.getpass("XFYUN_SECRET_KEY (RAASR SecretKey): ").strip()

    if not appid or not secret_key:
        print("APP ID and Secret Key are required.")
        return 2

    output = Path(args.output).expanduser().resolve()
    if output.exists():
        old = output.read_text(encoding="utf-8")
        kept_lines = [
            line
            for line in old.splitlines()
            if not line.startswith("XFYUN_APP_ID=") and not line.startswith("XFYUN_SECRET_KEY=")
        ]
    else:
        kept_lines = []

    kept_lines.extend(
        [
            f'XFYUN_APP_ID="{appid}"',
            f'XFYUN_SECRET_KEY="{secret_key}"',
        ]
    )
    output.write_text("\n".join(kept_lines).strip() + "\n", encoding="utf-8")
    output.chmod(0o600)
    print(f"Wrote credentials to {output}")
    print("This file is local-only. Do not commit it. Publish the skill without real credentials.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
