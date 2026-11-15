import os, requests, base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")
def D(s): return base64.b64decode(s).decode()
CODES = ["QmV0OWph", "U3BvcnR5QmV0", "MXhCZXQ=", "QmV0S2luZw==", "TVNwb3J0", "U3Rha2U=", "QmV0d2F5", "QmV0UGF3YQ==", "QmV0YW5v", "MjJCZXQ=", "TWVsQmV0", "QmV0V2lubmVy"]
NAMES = [D(c) for c in CODES]
# API slugs - 1x uses 1xng on input, per docs
SLUGS = {"QmV0OWph": "bet9ja", "U3BvcnR5QmV0": "sportybet", "MXhCZXQ=": "1xng", "QmV0S2luZw==": "betking", "TVNwb3J0": "msport", "U3Rha2U=": "stake", "QmV0d2F5": "betway", "QmV0UGF3YQ==": "betpawa", "QmV0YW5v": "betano", "MjJCZXQ=": "22bet", "TWVsQmV0": "melbet", "QmV0V2lubmVy": "betwinner"}
MAP = {}
for c, n in zip(CODES, NAMES): MAP[n] = SLUGS[c]

def grid(prefix, exclude=None):
    rows=[]; row=[]
    for n in NAMES:
        if n == exclude: continue
        row.append(InlineKeyboardButton(n, callback_data=f"{prefix}|{n}"))
        if len(row)==3: rows.append(row); row=[]
    if row: rows.append(row)
    return InlineKeyboardMarkup(rows)

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    c.user_data.clear()
    await u.message.reply_text("Pick FROM:", reply_markup=grid("F"))

async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q=u.callback_query; await q.answer()
    kind,val=q.data.split("|",1)
    if kind=="F":
        c.user_data["f"]=val
        await q.message.reply_text(f"From: {val}\nNow pick TO:", reply_markup=grid("T", exclude=val))
    else:
        c.user_data["t"]=val
        await q.message.reply_text(f"From {c.user_data['f']} to {val}. Send your code now:")

async def code(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if "f" not in c.user_data or "t" not in c.user_data:
        await u.message.reply_text("Type /start first"); return
    cd=u.message.text.strip().upper()
    s=MAP[c.user_data["f"]]; d=MAP[c.user_data["t"]]
    await u.message.reply_text("Converting...")
    try:
        r=requests.post("https://api.managebetcodes.app/v1/convert", json={"code": cd, "from": s, "to": d}, headers={"X-API-Key": MBC_KEY, "Content-Type": "application/json"}, timeout=45)
        txt=r.text[:800]
        if r.status_code != 200:
            await u.message.reply_text(f"API said {r.status_code}:\n{txt}\n\nCheck code is a real {c.user_data['f']} code and has not expired. Type /start to try again."); return
        j=r.json()
        nc=None
        if isinstance(j,dict):
            if isinstance(j.get("target"),dict): nc=j["target"].get("code")
            if not nc: nc=j.get("converted_code") or j.get("new_code") or j.get("code")
            if not nc and isinstance(j.get("data"),dict): nc=j["data"].get("code")
        if not nc:
            await u.message.reply_text(f"API replied but no code:\n{txt}\n\nType /start and try a fresh code."); return
        await u.message.reply_text(f"Done!\nFrom: {c.user_data['f']}\nTo: {c.user_data['t']}\nNew Code: {nc}\n\nType /start for another")
    except Exception as e:
        await u.message.reply_text(f"Error: {type(e).__name__}: {str(e)[:300]}")

app=ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, code))
app.run_polling()
