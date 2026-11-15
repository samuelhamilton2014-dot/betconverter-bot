"""
BetConverter NG Bot - Clean Version
Features: Convert, Combine, Split, Contact
API: ManageBetCodes - https://api.managebetcodes.app/v1/convert
"""

import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")
API_URL = "https://api.managebetcodes.app/v1/convert"
TIMEOUT = 30

BOOKMAKERS = [
    "bet9ja", "sportybet", "1xbet", "betking", "msport",
    "stake", "betway", "betpawa", "football", "sportpesa",
    "betika", "odibets", "pepeta", "1win", "betano",
    "paripesa", "22bet", "betjam", "melbet", "megapari",
    "dbbet", "linebet", "fansport", "betwinner", "bangbet",
    "goldpari", "lilbet", "helabet", "secretbet", "planbet",
    "paripulse", "1xbit", "afropari", "888starz", "xparibet",
    "luckypari", "betandyou", "winwinbet", "fastpari", "spinbetter",
]

API_SLUG_MAP = {
    "1xbet": "1xng",
    "football": "football.com",
}

ADMIN_USERNAME = "@autoscoutng"

def api_slug(name: str) -> str:
    return API_SLUG_MAP.get(name, name)

def display_name(name: str) -> str:
    if name in ("1xbet", "1xbit", "888starz", "22bet"):
        return name
    return name.capitalize()

def bookmaker_grid(prefix: str, exclude: str | None = None) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for name in BOOKMAKERS:
        if name == exclude:
            continue
        row.append(InlineKeyboardButton(display_name(name), callback_data=f"{prefix}|{name}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Convert Code", callback_data="MENU|convert")],
        [
            InlineKeyboardButton("Combine Codes", callback_data="MENU|merge"),
            InlineKeyboardButton("Split Code", callback_data="MENU|split"),
        ],
        [InlineKeyboardButton("Contact Admin", callback_data="MENU|contact")],
    ])

def done_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Convert Another", callback_data="DONE|again")],
        [
            InlineKeyboardButton("Convert Back", callback_data="DONE|back"),
            InlineKeyboardButton("Share Code", callback_data="DONE|share"),
        ],
        [InlineKeyboardButton("Main Menu", callback_data="DONE|menu")],
    ])

def convert_code(from_bookmaker: str, to_bookmaker: str, code: str) -> tuple[str | None, str | None]:
    payload = {
        "code": code,
        "from": api_slug(from_bookmaker),
        "to": api_slug(to_bookmaker),
    }
    headers = {
        "X-API-Key": MBC_KEY,
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        return None, "API took too long. Try again in 1 minute."
    except requests.exceptions.ConnectionError:
        return None, "Could not reach ManageBetCodes API. Check API status."
    except Exception as exc:
        logger.exception("Convert request failed")
        return None, f"Error: {str(exc)[:200]}"

    if response.status_code != 200:
        return None, f"API said {response.status_code}. Check code is fresh and from {display_name(from_bookmaker)}."

    try:
        data = response.json()
    except ValueError:
        return None, "API gave an invalid reply. Try again."

    if isinstance(data, dict) and "error" in data:
        error = data["error"]
        if isinstance(error, dict):
            message = error.get("message", "Conversion failed")
        else:
            message = str(error)
        return None, message

    new_code = None
    if isinstance(data, dict):
        target = data.get("target")
        if isinstance(target, dict):
            new_code = target.get("code")
        if not new_code:
            new_code = data.get("converted_code")
        if not new_code:
            new_code = data.get("new_code")
        if not new_code:
            new_code = data.get("code")

    if not new_code:
        return None, "API replied but gave no new code. Code may be expired."

    return str(new_code).strip(), None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    name = update.effective_user.first_name or "Samuel"
    await update.message.reply_text(
        f"Elite Dashboard\n\n{name}, tap on your next move:",
        reply_markup=main_menu_keyboard(),
    )

async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "convert"
    context.user_data.pop("from_bookmaker", None)
    context.user_data.pop("to_bookmaker", None)
    await update.message.reply_text("Pick FROM:", reply_markup=bookmaker_grid("FROM"))

async def merge_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "merge"
    context.user_data.pop("from_bookmaker", None)
    context.user_data.pop("to_bookmaker", None)
    await update.message.reply_text("Combine: Pick FROM:", reply_markup=bookmaker_grid("FROM"))

async def split_command(update: Update, context: ContextTypes.DEFAULT_TYPE) ->
