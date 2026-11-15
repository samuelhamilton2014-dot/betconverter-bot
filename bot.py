import os, requests, base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")
def D(s): return base64.b64decode(s).decode()
CODES = ["QmV0OWph", "U3BvcnR5QmV0", "MXhCZXQ=", "QmV0S2luZw==", "TVNwb3J0", "U3Rha2U=", "QmV0d2F5", "QmV0UGF3YQ==", "QmV0YW5v", "MjJCZXQ=", "TWVsQmV0", "QmV0V2lubmVy"]
NAMES = [D(c) for c in CODES]
SLUGS = [n.lower().replace(" ", "") for n in NAMES]
MAP = dict(zip(NAMES, SLUGS))

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
    # try 3 possible API shapes
    tries=[
        ("https://api.managebetcodes.com/v1/convert", {"from_bookmaker": s, "to_bookmaker": d, "code": cd}),
        ("https://api.managebetcodes.com/api/v1/convert", {"from_bookmaker": s, "to_bookmaker": d, "code": cd}),
        ("https://managebetcodes.com/api/v1/convert", {"from_bookmaker": s, "to_bookmaker": d, "code": cd}),
    ]
    last=""
    for url,payload in tries:
        try:
            r=requests.post(url, json=payload, headers={"Authorization": f"Bearer {MBC_KEY}", "Content-Type": "application/json", "X-API-Key": MBC_KEY}, timeout=15)
            txt=r.text[:600]
            last=f"URL {url} -> Status {r.status_code} -> {txt}"
            if r.status_code==200:
                j=r.json()
                nc=None
                if isinstance(j,dict):
                    nc=j.get("converted_code") or j.get("new_code") or j.get("code")
                    if not nc and isinstance(j.get("data"),dict): nc=j["data"].get("converted_code") or j["data"].get("code")
                if nc:
                    await u.message.reply_text(f"Done!\nFrom: {c.user_data['f']}\nTo: {c.user_data['t']}\nNew Code: {nc}"); return
                await u.message.reply_text(f"API replied but no code in it:\n{last}\n\nType /start and try a fresh code."); return
        except Exception as e:
            last=f"URL {url} -> Error: {type(e).__name__}: {str(e)[:300]}"
            continue
    await u.message.reply_text(f"All API tries failed.\n\n{last}\n\nThis means the API address in the code is wrong. Check your ManageBetCodes dashboard for the correct API URL and send me a screenshot of it (hide your key).")

app=ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, code))
app.run_polling()
