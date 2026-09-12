#!/usr/bin/env python3
"""
Pyrogram v2 Session String Generator
=====================================

Generates a Pyrogram session string for a user account (userbot) or bot
account. The session string lets you reuse a login without re-entering
phone/OTP/2FA every time — useful for deploying bots/userbots to servers,
Docker containers, CI pipelines, etc.

Requirements:
    pip install -r requirements.txt

Credentials can come from (in priority order):
    1. Command-line arguments (--api-id, --api-hash, --bot-token)
    2. A .env file in the current directory (see .env.example)
    3. Interactive prompts (fallback if nothing else is set)

Usage:
    Interactive:
        python3 generate_session.py

    Non-interactive bot session (fully scriptable, no prompts needed
    beyond credentials):
        python3 generate_session.py --bot --api-id 123456 \
            --api-hash abcdef... --bot-token 123:ABC...

    User session with .env credentials already set:
        python3 generate_session.py --user

IMPORTANT SECURITY NOTE:
    A session string grants full access to the account it was generated
    for. Treat it like a password — never share it, never commit it to
    git, and store it in an environment variable or secrets manager, not
    in plain source code.
"""

import argparse
import asyncio
import os
import sys

try:
    from pyrogram import Client
    from pyrogram.errors import (
        ApiIdInvalid,
        PhoneNumberInvalid,
        AccessTokenInvalid,
        FloodWait,
        RPCError,
    )
except ImportError:
    sys.exit(
        "Pyrogram is not installed. Install dependencies first with:\n"
        "    pip install -r requirements.txt"
    )

try:
    from dotenv import load_dotenv
    load_dotenv()  # silently no-ops if no .env file is present
except ImportError:
    pass  # python-dotenv is optional; CLI args / prompts still work


def prompt(text: str) -> str:
    return input(text).strip()


def prompt_int(text: str) -> int:
    while True:
        val = prompt(text)
        if val.isdigit():
            return int(val)
        print("Please enter a numeric value.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Pyrogram v2 session string for a user or bot account."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--user", action="store_true", help="Generate a user-account session.")
    mode.add_argument("--bot", action="store_true", help="Generate a bot-account session.")
    parser.add_argument("--api-id", type=int, default=None, help="Telegram api_id (overrides .env / prompt).")
    parser.add_argument("--api-hash", type=str, default=None, help="Telegram api_hash (overrides .env / prompt).")
    parser.add_argument("--bot-token", type=str, default=None, help="Bot token from @BotFather (bot mode only).")
    parser.add_argument("--output", type=str, default=None, help="Path to save the session string to, e.g. session_string.txt.")
    parser.add_argument("--quiet", action="store_true", help="Suppress the save-to-file prompt; requires --output to actually save.")
    return parser.parse_args()


async def generate_user_session(api_id: int, api_hash: str) -> str:
    """
    Generates a session string for a regular Telegram user account.
    Pyrogram's Client, when given no session name/in-memory mode, walks
    you through phone number -> OTP -> (optional) 2FA password
    interactively on the terminal.
    """
    async with Client(
        name="user_session_gen",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
    ) as app:
        me = await app.get_me()
        session_string = await app.export_session_string()
        print(f"\nLogged in as: {me.first_name} (@{me.username or 'no-username'}, id={me.id})")
        return session_string


async def generate_bot_session(api_id: int, api_hash: str, bot_token: str) -> str:
    """
    Generates a session string for a bot account using a bot token
    from @BotFather.
    """
    async with Client(
        name="bot_session_gen",
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token,
        in_memory=True,
    ) as app:
        me = await app.get_me()
        session_string = await app.export_session_string()
        print(f"\nLogged in as bot: {me.first_name} (@{me.username}, id={me.id})")
        return session_string


def resolve_credentials(args):
    """Resolve api_id/api_hash from CLI args -> .env/os.environ -> interactive prompt."""
    api_id = args.api_id or (int(os.environ["API_ID"]) if os.environ.get("API_ID") else None)
    if not api_id:
        api_id = prompt_int("API ID: ")

    api_hash = args.api_hash or os.environ.get("API_HASH")
    if not api_hash:
        api_hash = prompt("API Hash: ")

    return api_id, api_hash


def resolve_bot_token(args):
    bot_token = args.bot_token or os.environ.get("BOT_TOKEN")
    if not bot_token:
        bot_token = prompt("Bot Token: ")
    return bot_token


def main():
    args = parse_args()

    print("=" * 60)
    print(" Pyrogram v2 Session String Generator")
    print("=" * 60)
    print("\nGet api_id / api_hash from https://my.telegram.org/apps\n")

    api_id, api_hash = resolve_credentials(args)

    is_bot = args.bot
    if not args.bot and not args.user:
        print("\nSession type:")
        print("  1) User account (personal/userbot session)")
        print("  2) Bot account (via BotFather token)")
        is_bot = prompt("Choose [1/2]: ").strip() == "2"

    try:
        if is_bot:
            bot_token = resolve_bot_token(args)
            session_string = asyncio.run(generate_bot_session(api_id, api_hash, bot_token))
        else:
            session_string = asyncio.run(generate_user_session(api_id, api_hash))
    except ApiIdInvalid:
        sys.exit(
            "\nError: API_ID_INVALID — your api_id/api_hash pair is wrong or "
            "mismatched. Re-copy both from https://my.telegram.org/apps."
        )
    except PhoneNumberInvalid:
        sys.exit(
            "\nError: PHONE_NUMBER_INVALID — include the country code with a "
            "leading '+', no spaces (e.g. +14155552671)."
        )
    except AccessTokenInvalid:
        sys.exit(
            "\nError: ACCESS_TOKEN_INVALID — the bot token was mistyped or "
            "revoked. Get a fresh one from @BotFather -> /mybots -> API Token."
        )
    except FloodWait as e:
        sys.exit(
            f"\nError: FLOOD_WAIT_{e.value} — Telegram is rate-limiting login "
            f"attempts. Wait {e.value} seconds before retrying."
        )
    except RPCError as e:
        sys.exit(f"\nTelegram API error: {e}\nSee https://core.telegram.org/api/errors for details.")

    print("\n" + "=" * 60)
    print(" SESSION STRING GENERATED")
    print("=" * 60)
    print(session_string)
    print("=" * 60)
    print(
        "\nStore this securely (e.g. as an environment variable "
        "SESSION_STRING). Anyone with this string has full access "
        "to the account.\n"
    )

    output_path = args.output
    if not output_path and not args.quiet:
        save = prompt("Save to session_string.txt? [y/N]: ").lower()
        if save == "y":
            output_path = "session_string.txt"

    if output_path:
        with open(output_path, "w") as f:
            f.write(session_string)
        print(f"Saved to {output_path} — make sure it's listed in .gitignore.")


if __name__ == "__main__":
    main()
