#!/usr/bin/env python3
"""
Session String Validator
=========================

Quick sanity check that a Pyrogram session string actually logs in.
Connects using the session string, prints basic account info and a
recent-chats count, then disconnects. Useful right after generating a
session, or before deploying it somewhere, to confirm it hasn't expired
or been revoked.

Usage:
    python3 validate_session.py                     # reads SESSION_STRING from .env/env
    python3 validate_session.py --session "AgD..."   # pass it directly
    python3 validate_session.py --file session_string.txt
"""

import argparse
import asyncio
import os
import sys

try:
    from pyrogram import Client
    from pyrogram.errors import RPCError, AuthKeyUnregistered, UserDeactivated
except ImportError:
    sys.exit(
        "Pyrogram is not installed. Install dependencies first with:\n"
        "    pip install -r requirements.txt"
    )

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def parse_args():
    parser = argparse.ArgumentParser(description="Validate a Pyrogram session string.")
    parser.add_argument("--session", type=str, default=None, help="Session string (overrides file/env).")
    parser.add_argument("--file", type=str, default=None, help="Path to a file containing the session string.")
    parser.add_argument("--api-id", type=int, default=None, help="Telegram api_id (falls back to .env).")
    parser.add_argument("--api-hash", type=str, default=None, help="Telegram api_hash (falls back to .env).")
    return parser.parse_args()


def resolve_session_string(args) -> str:
    if args.session:
        return args.session.strip()
    if args.file:
        with open(args.file) as f:
            return f.read().strip()
    if os.environ.get("SESSION_STRING"):
        return os.environ["SESSION_STRING"].strip()
    sys.exit(
        "No session string provided. Pass --session, --file, or set "
        "SESSION_STRING in your environment/.env."
    )


async def validate(api_id: int, api_hash: str, session_string: str):
    async with Client(
        name="session_validator",
        api_id=api_id,
        api_hash=api_hash,
        session_string=session_string,
        in_memory=True,
    ) as app:
        me = await app.get_me()
        print("Session is valid.\n")
        print(f"  Account: {me.first_name} {me.last_name or ''}".rstrip())
        print(f"  Username: @{me.username}" if me.username else "  Username: (none)")
        print(f"  User ID: {me.id}")
        print(f"  Is bot: {me.is_bot}")
        print(f"  Phone: {me.phone_number}" if getattr(me, 'phone_number', None) else "  Phone: (hidden or bot account)")

        chat_count = 0
        async for _ in app.get_dialogs(limit=50):
            chat_count += 1
        suffix = "+" if chat_count == 50 else ""
        print(f"  Visible chats (first 50 checked): {chat_count}{suffix}")


def main():
    args = parse_args()

    api_id = args.api_id or (int(os.environ["API_ID"]) if os.environ.get("API_ID") else None)
    api_hash = args.api_hash or os.environ.get("API_HASH")

    if not api_id or not api_hash:
        sys.exit(
            "api_id / api_hash not found. Pass --api-id/--api-hash or set "
            "API_ID/API_HASH in your environment/.env."
        )

    session_string = resolve_session_string(args)

    try:
        asyncio.run(validate(api_id, api_hash, session_string))
    except AuthKeyUnregistered:
        sys.exit(
            "\nError: AUTH_KEY_UNREGISTERED — this session has been revoked "
            "or logged out (check Telegram Settings -> Devices). Generate a new one."
        )
    except UserDeactivated:
        sys.exit("\nError: USER_DEACTIVATED — the account this session belongs to has been deleted or banned.")
    except RPCError as e:
        sys.exit(f"\nTelegram API error: {e}\nSee https://core.telegram.org/api/errors for details.")


if __name__ == "__main__":
    main()
