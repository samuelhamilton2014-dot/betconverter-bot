import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")
API = "https://api.managebetcodes.app/v1/convert"

# Names are split with + so chat cannot turn them into links
SLUGS = ["be" + "t9ja", "spo" + "rtybet", "1x" + "bet", "bet" + "king", "msp" + "ort", "sta" + "ke", "bet" + "way", "bet" + "winner", "1x" + "bit", "db" + "bet", "fas" + "tpari", "foot" + "ball", "gol" + "dpari", "hel" + "abet", "lin" + "ebet", "luc" + "kypari", "meg" + "apari", "mel" + "bet", "par" + "ipesa", "par" + "ipulse", "pla" + "nbet", "888" + "starz", "win" + "winbet", "xpa" + "ribet", "afr" + "opari", "22" + "bet", "bet" + "jam"]

MAP = {"1x" + "bet": "1x" + "ng", "foot" + "ball": "foot" + "ball.com"}
ADMIN = "@autoscoutng"

def slug(s):
    s = s.strip().lower()
    if s in MAP:
        return MAP[s]
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
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def dash():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Convert Code", callback_data="MENU|convert")],
        [InlineKeyboardButton("Combine Codes", callback_data="MENU|merge"), InlineKeyboardButton("Split Code", callback_data="MENU|split")],
        [InlineKeyboardButton("Contact Admin", callback_data="MENU|contact")],
    ])

def donekb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Convert Another", callback_data="DONE|again")],
        [InlineKeyboardButton("Convert Back", callback_data="DONE|back"), InlineKeyboardButton("Share Code", callback_data="DONE|share")],
        [InlineKeyboardButton("Main Menu", callback_data="DONE|menu")],
    ])

def convert(frm, to, code):
    frm = frm.strip().lower()
    to = to.strip().lower()
    code = code.strip().upper()
    headers = {"X-API-Key": MBC_KEY, "Content-Type": "application/json"}
    payload = {"code": code, "from": slug(frm), "to": slug(to)}
    try:
        r = requests.post(API, json=payload, headers=headers, timeout=60)
    except Exception as e:
        return None, "Error: " + str(e)[:200]
    if r.status_code == 401:
        return None, "API Key WRONG. Update MBC_KEY in Fly Secrets."
    if r.status_code == 402:
        return None, "No credits left."
    if r.status_code == 422:
        return None, "422: " + r.text[:300]
    if r.status_code != 200:
        return None, "API said " + str(r.status_code) + ": " + r.text[:300]
    try:
        j = r.json()
    except Exception:
        return None, "Bad reply: " + r.text[:200]
    if isinstance(j, dict) and "error" in j:
        err = j["error"]
        if isinstance(err, dict):
            return None, err.get("message", "Failed")
        return None, str(err)
    nc = None
    if isinstance(j, dict):
        t = j.get("target")
        if isinstance(t, dict):
            nc = t.get("code")
        if not nc:
            nc = j.get("converted_code")
        if not nc:
            nc = j.get("new_code")
        if not nc:
            nc = j.get("code")
    if not nc:
        return None, "No new code. Make a FRESH code today."
    return str(nc).strip(), None

async def start(u, c):
    c.user_data.clear()
    name = u.effective_user.first_name or "Samuel"
    await u.message.reply_text("Elite Dashboard\n\n" + name + ", tap on your next move:", reply_markup=dash())

async def cmd_convert(u, c):
    c.user_data["mode"] = "convert"
    c.user_data.pop("f", None)
    c.user_data.pop("t", None)
    await u.message.reply_text("Pick FROM:", reply_markup=grid("F"))

async def cmd_merge(u, c):
    c.user_data["mode"] = "merge"
    c.user_data.pop("f", None)
    c.user_data.pop("t", None)
    await u.message.reply_text("Combine: Pick FROM:", reply_markup=grid("F"))

async def cmd_split(u, c):
    c.user_data["mode"] = "split"
    c.user_data.pop("f", None)
    c.user_data.pop("t", None)
    await u.message.reply_text("Split: Pick FROM:", reply_markup=grid("F"))

async def cmd_contact(u, c):
    await u.message.reply_text("Contact Admin: " + ADMIN)

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
            await q.message.reply_text("Contact Admin: " + ADMIN)
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
            new_code, err = convert(t, f, nc)
            if new_code:
                c.user_data["last_new"] = new_code
                await q.message.reply_text("Done!\nFrom: " + show(t) + "\nTo: " + show(f) + "\nNew Code: " + new_code, reply_markup=donekb())
            else:
                await q.message.reply_text("Failed: " + err, reply_markup=donekb())
        elif val == "share":
            nc = c.user_data.get("last_new", "")
            await q.message.reply_text("Share this code:\n" + nc)
        elif val == "menu":
            await q.message.reply_text("Elite Dashboard\nTap on your next move:", reply_markup=dash())
        return
    if kind == "F":
        c.user_data["f"] = val
        await q.message.reply_text("From: " + show(val) + "\nNow pick TO:", reply_markup=grid("T", exclude=val))
        return
    if kind == "T":
        c.user_data["t"] = val
        mode = c.user_data.get("mode", "convert")
        f = c.user_data["f"]
        if mode == "merge":
            await q.message.reply_text("From " + show(f) + " to " + show(val) + ".\nSend 2 codes separated by comma, like:\nCODE1, CODE2")
        elif mode == "split":
            await q.message.reply_text("From " + show(f) + " to " + show(val) + ".\nSend your code to split:")
        else:
            await q.message.reply_text("From " + show(f) + " to " + show(val) + ". Send your code now:")
        return

async def code(u, c):
    txt = u.message.text.strip()
    mode = c.user_data.get("mode", "convert")
    if "f" not in c.user_data:
        await u.message.reply_text("Type /start first")
        return
    if "t" not in c.user_data:
        await u.message.reply_text("Pick TO first")
        return
    f = c.user_data["f"]
    t = c.user_data["t"]
    if mode == "merge" and "," in txt:
        codes = [x.strip().upper() for x in txt.split(",") if x.strip()]
        if len(codes) < 2:
            await u.message.reply_text("Send 2 codes separated by comma, like:\nCODE1, CODE2")
            return
        await u.message.reply_text("Converting both...")
        out = []
        for cd in codes:
            nc, err = convert(f, t, cd)
            if nc:
                out.append(cd + " -> " + nc)
            else:
                out.append(cd + " -> FAILED: " + err)
        await u.message.reply_text("Combine Done:\n" + "\n".join(out), reply_markup=donekb())
        return
    cd = txt.upper()
    await u.message.reply_text("Converting...")
    nc, err = convert(f, t, cd)
    if not nc:
        await u.message.reply_text("Failed: " + err, reply_markup=donekb())
        return
    c.user_data["last_new"] = nc
    c.user_data["last_old"] = cd
    await u.message.reply_text("Done!\nFrom: " + show(f) + "\nTo: " + show(t) + "\nOld Code: " + cd + "\nNew Code: " + nc, reply_markup=donekb())

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("convert", cmd_convert))
app.add_handler(CommandHandler("merge", cmd_merge))
app.add_handler(CommandHandler("split", cmd_split))
app.add_handler(CommandHandler("contact", cmd_contact))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, code))
app.run_polling()
