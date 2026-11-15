import os, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")

# Names built in 2 parts so copy does not break
SB = "Spo" + "rtyBet"
B9 = "【entity-Bet¦canonical_name=Bet】" + "9ja"
X1 = "1x" + "【entity-Bet¦canonical_name=Bet】"
MS = "Ms" + "port"
BK = ["SB", "B9", "X1", "MS"]
NAMES = {"SB": SB, "B9": B9, "X1": X1, "MS": MS}
API = {"SB": SB.lower(), "B9": "bet9ja", "X1": "1xbet", "MS": "msport"}

def kb_for(prefix, exclude=None):
    rows = []
    for k in BK:
        if k == exclude: continue
        rows.append([InlineKeyboardButton(NAMES[k], callback_data=f"{prefix}:{k}")])
    return InlineKeyboardMarkup(rows)

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    c.user_data.clear()
    await u.message.reply_text("From which app is your code?", reply_markup=kb_for("FROM"))

async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    kind, val = q.data.split(":")
    if kind == "FROM":
        c.user_data["from"] = val
        await q.message.reply_text(f"From: {NAMES[val]}. Now - To which app?", reply_markup=kb_for("TO", exclude=val))
    else:
        c.user_data["to"] = val
        await q.message.reply_text(f"From {NAMES[c.user_data['from']]} to {NAMES[val]}. Send your code now:")

async def code(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if "from" not in c.user_data or "to" not in c.user_data:
        await u.message.reply_text("Type /start first and pick From and To")
        return
    cd = u.message.text.strip().upper()
    s = API[c.user_data["from"]]; d = API[c.user_data["to"]]
    await u.message.reply_text("Converting...")
    try:
        r = requests.post("https://api.managebetcodes.com/v1/convert", json={"from_bookmaker": s, "to_bookmaker": d, "code": cd}, headers={"Authorization": f"Bearer {MBC_KEY}", "Content-Type": "application/json"}, timeout=30)
        j = r.json()
        nc = j.get("converted_code") or j.get("data", {}).get("converted_code") if isinstance(j.get("data"), dict) else j.get("converted_code")
        if not nc: nc = j.get("code") or j.get("new_code")
        if not nc:
            await u.message.reply_text(f"Failed. API said: {str(j)[:300]}. Check code is correct for {NAMES[c.user_data['from']]}. Type /start to try again.")
            return
        await u.message.reply_text(f"Done!\nFrom: {NAMES[c.user_data['from']]}\nTo: {NAMES[c.user_data['to']]}\nNew Code: {nc}\n\nType /start for another")
    except Exception as e:
        await u.message.reply_text(f"Failed - API did not respond in time. Code may be invalid for {NAMES[c.user_data['from']]} or API is slow. Type /start and try again.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, code))
app.run_polling()
