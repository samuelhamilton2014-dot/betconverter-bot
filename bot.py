import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")
API = "https://api.managebetcodes.app/v1/convert"

SLUGS = ["bet9ja", "sportybet", "1xbet", "betking", "msport", "stake", "betway", "betpawa", "football", "sportpesa", "betika", "odibets", "pepeta", "1win", "betano", "paripesa", "22bet", "betjam", "melbet", "megapari", "dbbet", "linebet", "fansport", "betwinner", "bangbet", "goldpari", "lilbet", "helabet", "secretbet", "planbet", "paripulse", "1xbit", "afropari", "888starz", "xparibet", "luckypari", "betandyou", "winwinbet", "fastpari", "spinbetter"]
API_MAP = {"1xbet": "1xng", "football": "football.com"}

def api_slug(s):
    if s in API_MAP:
        return API_MAP[s]
    return s

def show(s):
    return s.capitalize()

def grid(prefix, exclude=None):
    rows = []
    row = []
    for s in SLUGS:
        if s == exclude:
            continue
        row.append(InlineKeyboardButton(show(s), callback_data=prefix + "|" + s))
        if len(row) == 3:
            rows.append(row)
            row = []
    if len(row) > 0:
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def dash():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Convert Code", callback_data="MENU|convert")],
        [InlineKeyboardButton("Combine Codes", callback_data="MENU|merge"), InlineKeyboardButton("Split Code", callback_data="MENU|split")],
        [InlineKeyboardButton("Contact Admin", callback_data="MENU|contact")],
    ])

def done_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Convert Another", callback_data="DONE|again")],
        [InlineKeyboardButton("Convert Back", callback_data="DONE|back"), InlineKeyboardButton("Share Code", callback_data="DONE|share")],
        [InlineKeyboardButton("Main Menu", callback_data="DONE|menu")],
    ])

async def start(u, c):
    c.user_data.clear()
    name = u.effective_user.first_name
    if not name:
        name = "Samuel"
    await u.message.reply_text("Elite Dashboard\n\n" + name + ". Tap on your next move:", reply_markup=dash())

async def do_convert(frm, to, code):
    try:
        r = requests.post(API, json={"code": code, "from": api_slug(frm), "to": api_slug(to)}, headers={"X-API-Key": MBC_KEY, "Content-Type": "application/json"}, timeout=30)
        if r.status_code != 200:
            return None, "API said " + str(r.status_code) + ". Check code is fresh and from " + show(frm) + "."
        j = r.json()
        if isinstance(j, dict):
            if "error" in j:
                msg = j["error"].get("message", "Conversion failed")
                return None, msg
        nc = None
        if isinstance(j, dict):
            if isinstance(j.get("target"), dict):
                nc = j["target"].get("code")
            if not nc:
                nc = j.get("converted_code")
            if not nc:
                nc = j.get("new_code")
            if not nc:
                nc = j.get("code")
        if not nc:
            return None, "API replied but no new code. Code may be expired."
        return nc, None
    except Exception as e:
        return None, "Error: " + str(e)[:200]

async def btn(u, c):
    q = u.callback_query
    await q.answer()
    parts = q.data.split("|", 1)
    kind = parts[0]
    val = ""
    if len(parts) > 1:
        val = parts[1]
    if kind == "MENU":
        if val == "convert":
            c.user_data["mode"] = "convert"
            c.user_data.pop("f", None)
            c.user_data.pop("t", None)
            await q.message.reply_text("Pick FROM:", reply_markup=grid("F"))
        elif val == "merge":
            c.user_data["mode"] = "merge"
            c.user_data.pop("f", None)
            c.user_data.pop("t", None)
            await q.message.reply_text("Combine: Pick FROM:", reply_markup=grid("F"))
        elif val == "split":
            c.user_data["mode"] = "split"
            c.user_data.pop("f", None)
            c.user_data.pop("t", None)
            await q.message.reply_text("Split: Pick FROM:", reply_markup=grid("F"))
        elif val == "contact":
            await q.message.reply_text("Contact Admin: @autoscoutng")
        return
    if kind == "DONE":
        if val == "again":
            c.user_data["mode"] = "convert"
            c.user_data.pop("f", None)
            c.user_data.pop("t", None)
            await q.message.reply_text("Pick FROM:", reply_markup=grid("F"))
        elif val == "back":
            f = c.user_data.get("f")
            t = c.user_data.get("t")
            nc = c.user_data.get("last_new")
            if not f or not t or not nc:
                await q.message.reply_text("Nothing to convert back. Type /start")
                return
            c.user_data["f"] = t
            c.user_data["t"] = f
            c.user_data["mode"] = "convert"
            await q.message.reply_text("Converting back " + nc + "...")
            new_code, err = await do_convert(t, f, nc)
            if new_code:
                c.user_data["last_new"] = new_code
                await q.message.reply_text("Done!\nFrom: " + show(t) + "\nTo: " + show(f) + "\nNew Code: " + new_code, reply_markup=done_kb())
            else:
                await q.message.reply_text("Failed: " + err, reply_markup=done_kb())
        elif val == "share":
            nc = c.user_data.get("last_new", "")
            await q.message.reply_text("Share this code:\n" + nc)
        elif val == "menu":
            await q.message.reply_text("Elite Dashboard\nTap on your next move:", reply_markup=dash())
        return
    if kind == "F":
        c.user_data["f"] = val
        await q.message.reply_text("From: " + show(val) + "\nNow pick TO:", reply_markup=grid("T", exclude=val))
    elif kind == "T":
        c.user_data["t"] = val
        mode = c.user_data.get("mode", "convert")
        if mode == "merge":
            await q.message.reply_text("From " + show(c.user_data["f"]) + " to " + show(val) + ".\nSend 2 codes separated by comma, like:\nCODE1, CODE2")
        elif mode == "split":
            await q.message.reply_text("From " + show(c.user_data["f"]) + " to " + show(val) + ".\nSend your code to split:")
        else:
            await q.message.reply_text("From " + show(c.user_data["f"]) + " to " + show(val) + ". Send your code now:")

async def code(u, c):
    txt = u.message.text.strip()
    mode = c.user_data.get("mode", "convert")
    if "f" not in c.user_data:
        await u.message.reply_text("Type /start first")
        return
    f = c.user_data["f"]
    if "t" not in c.user_data:
        await u.message.reply_text("Pick TO first")
        return
    t = c.user_data["t"]
    if mode == "merge":
        if "," in txt:
            codes = [x.strip().upper() for x in txt.split(",") if x.strip()]
            await u.message.reply_text("Converting both...")
            out = []
            for cd in codes:
                nc, err = await do_convert(f, t, cd)
                if nc:
                    out.append(cd + " -> " + nc)
                else:
                    out.append(cd + " -> FAILED")
            await u.message.reply_text("
