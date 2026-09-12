# Pyrogram v2 Session String Generator

A small toolkit that logs into a Telegram **user account** or **bot
account** and exports a reusable **session string** — so you don't have
to re-enter your phone number, OTP, and 2FA password every time you
deploy a bot or userbot.

## Files

| File                  | Purpose                                                        |
|------------------------|-----------------------------------------------------------------|
| `generate_session.py`  | Interactive or scriptable session generator (user or bot mode) |
| `validate_session.py`  | Sanity-checks that a session string still works                |
| `requirements.txt`     | Python dependencies                                             |
| `.env.example`         | Template for credentials — copy to `.env`                      |
| `.gitignore`           | Keeps secrets and generated sessions out of git                |

---

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Interactive mode](#interactive-mode)
  - [Non-interactive / CLI mode](#non-interactive--cli-mode)
  - [Using a .env file](#using-a-env-file)
  - [Validating a session string](#validating-a-session-string)
- [Using the session string in your own code](#using-the-session-string-in-your-own-code)
- [Security notes](#security-notes)
- [Troubleshooting](#troubleshooting)
  - [`externally-managed-environment`](#error-externally-managed-environment)
  - [`python: command not found`](#error-python-command-not-found)
  - [`ModuleNotFoundError: No module named 'pyrogram'`](#error-modulenotfounderror-no-module-named-pyrogram)
  - [`tgcrypto` fails to build / install](#error-tgcrypto-fails-to-build--install)
  - [`API_ID_INVALID`](#error-api_id_invalid)
  - [`PHONE_NUMBER_INVALID`](#error-phone_number_invalid)
  - [`PHONE_CODE_INVALID` / `PHONE_CODE_EXPIRED`](#error-phone_code_invalid--phone_code_expired)
  - [`SESSION_PASSWORD_NEEDED`](#error-session_password_needed)
  - [`FLOOD_WAIT_X`](#error-flood_wait_x)
  - [`ACCESS_TOKEN_INVALID` (bot mode)](#error-access_token_invalid-bot-mode)
  - [`AUTH_KEY_UNREGISTERED` (when validating)](#error-auth_key_unregistered-when-validating)
  - [`USER_DEACTIVATED` (when validating)](#error-user_deactivated-when-validating)
  - [Connection / timeout errors on a VPS](#connection--timeout-errors-on-a-vps)
  - [`Permission denied` when running the script](#error-permission-denied-when-running-the-script)
  - [Script hangs with no prompt](#issue-script-hangs-with-no-prompt)

---

## Requirements

- Python 3.9 or newer
- An `api_id` and `api_hash` from https://my.telegram.org/apps
- For a **user session**: the Telegram account's phone number, access to
  receive the OTP code (via the Telegram app or SMS), and your 2FA/cloud
  password if you have one set
- For a **bot session**: a bot token from [@BotFather](https://t.me/BotFather)

---

## Installation

Pick **one** of the following. A virtual environment is recommended if
you'll keep working with this project; the other two options are faster
for a one-off run.

### Option 1 — Virtual environment (recommended)

```bash
python3 -m venv ~/pyrogram-env
source ~/pyrogram-env/bin/activate
pip install -r requirements.txt
```

You'll need to run `source ~/pyrogram-env/bin/activate` again in any new
terminal session before using the script.

### Option 2 — Install directly (override PEP 668 protection)

```bash
pip install -r requirements.txt --break-system-packages
```

Safe enough on a personal VPS you fully control; avoid on shared or
production systems where apt-managed Python packages matter.

### Option 3 — pipx (isolated but less ideal for library imports)

```bash
sudo apt install pipx
pipx install pyrogram
```

Not generally recommended here since Pyrogram is a library you `import`
into a script rather than a standalone CLI tool — Options 1 or 2 fit
better.

---

## Usage

### Interactive mode

```bash
python3 generate_session.py
```

(If you're inside an activated venv, plain `python` works too.)

You'll be prompted for:
1. Your `api_id` and `api_hash`
2. Session type — user account or bot account
3. Depending on type: phone number + OTP (+ 2FA password if enabled), or
   a bot token

At the end, the script prints the session string and offers to save it to
`session_string.txt`.

### Non-interactive / CLI mode

Useful for scripting or CI. Flags skip their corresponding prompts:

```bash
# Bot session, fully non-interactive
python3 generate_session.py --bot \
  --api-id 123456 \
  --api-hash your_api_hash \
  --bot-token 123456789:AAExampleTokenString \
  --output session_string.txt --quiet

# User session — still needs phone/OTP/2FA typed at the terminal,
# but api_id/api_hash are supplied up front
python3 generate_session.py --user --api-id 123456 --api-hash your_api_hash
```

Run `python3 generate_session.py --help` for the full flag list.

### Using a `.env` file

Copy the template and fill in your values so you're not retyping
credentials every run:

```bash
cp .env.example .env
# then edit .env with your API_ID / API_HASH / BOT_TOKEN
python3 generate_session.py --bot
```

The script loads `.env` automatically via `python-dotenv` if it's
installed (it's included in `requirements.txt`). CLI flags always take
priority over `.env` values if both are given.

### Validating a session string

After generating one, confirm it actually works (and check it again
later if you suspect it's expired or been revoked):

```bash
python3 validate_session.py --session "AgD...your_string..."
# or, if SESSION_STRING/API_ID/API_HASH are in your .env:
python3 validate_session.py
```

It logs in, prints the account name/ID/username, and counts visible
chats as a basic health check.

---

## Using the session string in your own code

```python
import os
from pyrogram import Client

app = Client(
    name="my_bot",
    api_id=YOUR_API_ID,
    api_hash="YOUR_API_HASH",
    session_string=os.environ["SESSION_STRING"],
    in_memory=True,
)

with app:
    app.send_message("me", "Session restored, no login needed!")
```

Load the string from an environment variable, `.env` file, or secrets
manager — not hardcoded in your source.

---

## Security notes

- A session string is equivalent to a **password** for the account it was
  generated from. Anyone who has it can log in as that account, read
  messages, and send messages on its behalf.
- Never commit `session_string.txt` to git. Add it to `.gitignore`.
- Regenerate (and revoke the old one via **Settings → Devices** in
  Telegram) if you ever suspect a string has leaked.
- Prefer bot sessions over user sessions when possible — a compromised
  bot token has a smaller blast radius than a compromised personal
  account.

---

## Troubleshooting

### Error: `externally-managed-environment`

**Full message:**
```
error: externally-managed-environment
× This environment is externally managed
```

**Cause:** Recent Debian/Ubuntu images block system-wide `pip install` to
protect the OS's own Python (PEP 668).

**Fix:** Use a virtual environment (Option 1 above), or run:
```bash
pip install pyrogram tgcrypto --break-system-packages
```

---

### Error: `python: command not found`

**Cause:** Debian/Ubuntu ship only `python3` by default; `python` isn't
aliased.

**Fix:**
```bash
python3 generate_session.py
```
Or make `python` resolve permanently:
```bash
sudo apt install python-is-python3
```
If you're using a venv, activate it first — `python` works automatically
inside an activated venv even without the symlink above.

---

### Error: `ModuleNotFoundError: No module named 'pyrogram'`

**Cause:** Pyrogram isn't installed in the Python environment you're
running the script with — often because it was installed in a venv that
isn't currently activated, or installed for a different Python version.

**Fix:**
```bash
# Check which python/pip you're using
which python3
which pip3

# Reinstall in that same environment
pip3 install pyrogram tgcrypto
```
If you use a venv, confirm it's activated (`source ~/pyrogram-env/bin/activate`)
before running the script — your terminal prompt should show `(pyrogram-env)`.

---

### Error: `tgcrypto` fails to build / install

**Cause:** `tgcrypto` compiles a C extension; the build fails if compiler
tools or Python headers are missing.

**Fix:**
```bash
sudo apt update
sudo apt install build-essential python3-dev
pip install tgcrypto --break-system-packages   # or inside your venv
```
`tgcrypto` is optional — Pyrogram works without it, just with slower
encryption. If it keeps failing and you want to move on, remove the
`tgcrypto` line from `requirements.txt` and reinstall with just
`pip install pyrogram python-dotenv`.

---

### Error: `API_ID_INVALID`

**Cause:** The `api_id`/`api_hash` pair is wrong, mismatched, or copied
with extra spaces.

**Fix:** Re-copy both values fresh from https://my.telegram.org/apps
(login with the phone number you plan to use). Make sure `api_id` is
entered as a plain integer, no quotes or spaces.

---

### Error: `PHONE_NUMBER_INVALID`

**Cause:** Phone number format is wrong.

**Fix:** Always include the country code with a leading `+`, no spaces or
dashes, e.g. `+14155552671`, not `4155552671` or `+1 415 555 2671`.

---

### Error: `PHONE_CODE_INVALID` / `PHONE_CODE_EXPIRED`

**Cause:** The OTP code was typed wrong, or too much time passed before
entering it.

**Fix:** Re-run the script and enter the code as soon as it arrives —
codes typically expire within a couple of minutes. Double check you're
reading the code from the Telegram app itself (it may arrive as a message
from "Telegram", not SMS, if you're already logged in elsewhere).

---

### Error: `SESSION_PASSWORD_NEEDED`

**Cause:** Two-factor authentication (cloud password) is enabled on the
account, and the script needs it after the OTP step.

**Fix:** This is expected behavior — Pyrogram will prompt for the
password automatically after the code. Just enter your 2FA password when
asked. If you forgot it, reset it in **Telegram Settings → Privacy and
Security → Two-Step Verification**.

---

### Error: `FLOOD_WAIT_X`

**Cause:** Telegram is rate-limiting login attempts (`X` = seconds to
wait) after too many tries in a short period.

**Fix:** Wait out the specified number of seconds before retrying. Avoid
repeatedly cancelling and restarting the login flow.

---

### Error: `ACCESS_TOKEN_INVALID` (bot mode)

**Cause:** The bot token was mistyped, revoked, or regenerated.

**Fix:** Get a fresh token from [@BotFather](https://t.me/BotFather) via
`/mybots` → select your bot → **API Token**, and paste it exactly
(format is `123456789:AAExampleTokenString`).

---

### Error: `AUTH_KEY_UNREGISTERED` (when validating)

**Cause:** The session has been logged out, revoked (via **Settings →
Devices** in Telegram), or the account's authorization was reset.

**Fix:** No way to recover the old session — generate a new one with
`generate_session.py`.

---

### Error: `USER_DEACTIVATED` (when validating)

**Cause:** The account the session belongs to has been deleted, banned,
or deactivated by Telegram.

**Fix:** Not recoverable via this tool. You'd need to work through
Telegram's account-recovery/appeal process, or use a different account.

---

### Connection / timeout errors on a VPS

**Symptoms:** The script hangs, or raises timeout/connection-reset errors
before you even get to enter a phone number.

**Cause:** Some VPS providers/regions have Telegram's data centers
blocked or throttled by the hosting network or local ISP-level filtering.

**Fix:**
- Confirm outbound access isn't blocked by a firewall:
  ```bash
  curl -v https://api.telegram.org
  ```
- If your provider/region restricts Telegram's IP ranges, you may need a
  proxy. Pyrogram supports one via the `proxy` parameter on `Client`:
  ```python
  Client(
      ...,
      proxy=dict(scheme="socks5", hostname="1.2.3.4", port=1080,
                 username="user", password="pass"),
  )
  ```

---

### Error: `Permission denied` when running the script

**Cause:** The file isn't marked executable, or you're trying to run it
as `./generate_session.py` without the interpreter.

**Fix:** Run it via the interpreter instead of executing it directly:
```bash
python3 generate_session.py
```
Or make it executable:
```bash
chmod +x generate_session.py
./generate_session.py
```

---

### Issue: Script hangs with no prompt

**Cause:** Usually a slow/blocked connection to Telegram's servers (see
[Connection / timeout errors](#connection--timeout-errors-on-a-vps)
above), or the terminal is waiting on input that scrolled off-screen.

**Fix:** Press Enter to check if a prompt is just waiting; check network
connectivity with `curl -v https://api.telegram.org`; if using SSH, make
sure your session hasn't silently disconnected.

---

## Still stuck?

Re-run with the full traceback visible and check the exact Pyrogram
error name (all caps, e.g. `PHONE_NUMBER_INVALID`) — these map directly
to Telegram's API error list, which you can cross-reference at
https://core.telegram.org/api/errors for anything not covered above.
