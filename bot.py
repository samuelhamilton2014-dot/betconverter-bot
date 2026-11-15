import os, requests
TOKEN = "PUT_YOUR_TOKEN_HERE"
KEY = "PUT_YOUR_MBC_KEY_HERE"
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
PAIRS = {" 【entity-SportyBet¦canonical_name=SportyBet】-> 【entity-Bet9ja¦canonical_name=Bet9ja】": (" 【entity-sportybet¦canonical_name=SportyBet】", " 【entity-bet9ja¦canonical_name=Bet9ja】"), " 【entity-Bet9ja¦canonical_name=Bet9ja】-> 【entity-SportyBet¦canonical_name=SportyBet】": (" 【entity-bet9ja¦canonical_name=Bet9ja】", " 【entity-sportybet¦canonical_name=SportyBet】"), " 【entity-SportyBet¦canonical_name=SportyBet】->1xBet": (" 【entity-sportybet¦canonical_name=SportyBet】", "1xng")}
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(k, callback_data=k)] for k in PAIRS]
    await u.message.reply_text("BetConverter NG - Pick:", reply_markup=InlineKeyboardMarkup(kb))
async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer(); c.user_data["p"] = q.data
    await q.message.reply_text("Send your code now, e.g. 7B9A2F")
async def code(u: Update, c: ContextTypes.DEFAULT_TYPE):
    cd = u.message.text.strip().upper()
    if "p" not in c.user_data: return
    s, d = PAIRS[c.user_data["p"]]
    await u.message.reply_text("Converting...")
    r = requests.post("https://api.managebetcodes.app/v1/convert", headers={"X-API-Key": KEY, "Content-Type": "application/json"}, json={"code": cd, "from": s, "to": d}, timeout=25)
    j = r.json()
    nc = j.get("converted_code") or j.get("code")
    await u.message.reply_text(f"New Code: {nc}" if nc else f"Failed: {j}")
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, code))
app.run_polling()
