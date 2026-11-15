import os, requests, base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")

def D(s): return base64.b64decode(s).decode()
# names encoded so copy does not break
CODES = ["QmV0OWph", "U3BvcnR5QmV0", "MXhCZXQ=", "QmV0S2luZw==", "TVNwb3J0", "U3Rha2U=", "QmV0d2F5", "QmV0UGF3YQ==", "QmV0YW5v", "MjJCZXQ=", "TWVsQmV0", "QmV0V2lubmVy"]
NAMES = [D(c) for c in CODES]
SLUGS = [n.lower().replace(" ", "") for n in NAMES]
MAP = dict(zip(NAMES, SLUGS))

def grid(prefix, exclude=None):
    rows = []
    row = []
    for n in NAMES:
        if n == exclude: continue
        row.append(InlineKeyboardButton(n, callback_data=f"{prefix}|{n}"))
        if len(row) == 3:
            rows.append(row); row = []
    if row: rows.append(row)
    return InlineKeyboardMarkup(rows)

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    c.user_data.clear()
    await u.message.reply_text("Welcome to Converter NG!\n\nPick FROM:", reply_markup=grid("F"))

async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    kind, val = q.data.split("|", 1)
    if kind == "F":
        c.user_data["f"] = val
        await q.message.reply_text(f"From: {val}\nNow pick TO:", reply_markup=grid("T", exclude=val))
    else:
        c.user_data["t"] = val
        await q.message.reply_text(f"From {c.user_data['f']} to {val}. Send your code now:")

async def code(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if "f" not in c.user_data or "t" not in c.user_data:
        await u.message.reply_text("Type /start first and pick FROM and TO")
        return
    cd = u.message.text.strip().upper()
    s = MAP[c.user_data["f"]]; d = MAP[c.user_data["t"]]
    await u.message.reply_text("Converting...")
    try:
        r = requests.post("https://api.managebetcodes.com/v1/convert", json={"from_bookmaker": s, "to_bookmaker": d, "code": cd}, headers={"Authorization": f"Bearer {MBC_KEY}", "Content-Type": "application/json"}, timeout=30)
        j = r.json()
        nc = None
        if isinstance(j, dict):
            nc = j.get("converted_code") or j.get("new_code") or j.get("code")
            if not nc and isinstance(j.get("data"), dict):
                nc = j["data"].get("converted_code") or j["data"].get("code")
        if not nc:
            await u.message.reply_text(f"API could not convert this code.\nFrom: {c.user_data['f']} To: {c.user_data['t']} Code: {cd}\n\nAPI said: {str(j)[:400]}\n\nThis usually means the code is not from {c.user_data['f']}, or it has expired, or that pair is not supported. Try a fresh code from {c.user_data['f']} and type /start again.")
            return
        await u.message.reply_text(f"Done!\nFrom: {c.user_data['f']}\nTo: {c.user_data['t']}\nNew Code: {nc}\n\nType /start for another")
    except Exception as e:
        await u.message.reply_text(f"API did not respond. Check your code is a real {c.user_data['f']} code and try again. Type /start")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, code))
app.run_polling()
