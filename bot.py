import os, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")

SB = "spo" + "rtybet"
B9 = "bet" + "9ja"
X1 = "1x" + "ng"
PAIRS = {"A->B": (SB, B9), "B->A": (B9, SB), "A->C": (SB, X1)}

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(k, callback_data=k) for k in PAIRS.keys()]]
    await u.message.reply_text("BetConverter NG - Choose pair:", reply_markup=InlineKeyboardMarkup(kb))

async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    c.user_data["p"] = q.data
    await q.message.reply_text("Send your code now")

async def code(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if "p" not in c.user_data: return
    cd = u.message.text.strip().upper()
    s, d = PAIRS[c.user_data["p"]]
    await u.message.reply_text("Converting...")
    r = requests.post("https://api.managebetcodes.com/v1/convert", json={"from_bookmaker": s, "to_bookmaker": d, "code": cd}, headers={"Authorization": f"Bearer {MBC_KEY}"}, timeout=20)
    j = r.json()
    nc = j.get("converted_code") or j.get("code") or str(j)
    await u.message.reply_text(f"New Code: {nc}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, code))
app.run_polling()
