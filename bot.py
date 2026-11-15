import os, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")
API = "https://api.managebetcodes.app/v1/convert"

SLUGS = ["bet9ja","sportybet","1xbet","betking","msport","stake","betway","betpawa","football","sportpesa","betika","odibets","pepeta","1win","betano","paripesa","22bet","betjam","melbet","megapari","dbbet","linebet","fansport","betwinner","bangbet","goldpari","lilbet","helabet","secretbet","planbet","paripulse","1xbit","afropari","888starz","xparibet","luckypari","betandyou","winwinbet","fastpari","spinbetter"]
API_MAP = {"1xbet": "1xng", "football": "football.com"}
def api_slug(s): return API_MAP.get(s, s)
def show(s): return s.capitalize()

def grid(prefix, exclude=None):
    rows=[]; row=[]
    for s in SLUGS:
        if s == exclude: continue
        row.append(InlineKeyboardButton(show(s), callback_data=f"{prefix}|{s}"))
        if len(row)==3: rows.append(row); row=[]
    if row: rows.append(row)
    return InlineKeyboardMarkup(rows)

def dash():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Convert Code", callback_data="MENU|convert")],
        [InlineKeyboardButton("Book My Picks to Code", callback_data="MENU|book")],
        [InlineKeyboardButton("Combine Codes", callback_data="MENU|merge"), InlineKeyboardButton("Split Code", callback_data="MENU|split")],
        [InlineKeyboardButton("Contact Admin", callback_data="MENU|contact"), InlineKeyboardButton("Settings", callback_data="MENU|settings")],
    ])

def done_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Convert Another", callback_data="DONE|again")],
        [InlineKeyboardButton("Convert Back", callback_data="DONE|back"), InlineKeyboardButton("Share Code", callback_data="DONE|share")],
        [InlineKeyboardButton("Main Menu", callback_data="DONE|menu")],
    ])

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    c.user_data.clear()
    name = u.effective_user.first_name or "Samuel"
    await u.message.reply_text(f"Elite Dashboard\n\n{name}. Tap on your next move:", reply_markup=dash())

async def do_convert(frm, to, code):
    try:
        r = requests.post(API, json={"code": code, "from": api_slug(frm), "to": api_slug(to)}, headers={"X-API-Key": MBC_KEY, "Content-Type": "application/json"}, timeout=45)
        if r.status_code != 200: return None, f"API said {r.status_code}: {r.text[:300]}"
        j = r.json()
        nc = None
        if isinstance(j, dict):
            if isinstance(j.get("target"), dict): nc = j["target"].get("code")
            if not nc: nc = j.get("converted_code") or j.get("new_code") or j.get("code")
        return nc, None
    except Exception as e:
        return None, f"Error: {str(e)[:300]}"

async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    parts = q.data.split("|", 1)
    kind = parts[0]; val = parts[1] if len(parts) > 1 else ""
    if kind == "MENU":
        if val == "convert":
            c.user_data["mode"] = "convert"; c.user_data.pop("f", None); c.user_data.pop("t", None)
            await q.message.reply_text("Pick FROM:", reply_markup=grid("F"))
        elif val == "merge":
            c.user_data["mode"] = "merge"; c.user_data.pop("f", None); c.user_data.pop("t", None)
            await q.message.reply_text("Combine: Pick FROM:", reply_markup=grid("F"))
        elif val == "split":
            c.user_data["mode"] = "split"; c.user_data.pop("f", None); c.user_data.pop("t", None)
            await q.message.reply_text("Split: Pick FROM:", reply_markup=grid("F"))
        elif val == "book":
            c.user_data["mode"] = "book"
            await q.message.reply_text("Book My Picks: Send your picks, one per line.\nExample:\nMan City to win\nOver 2.5 in Chelsea game\nThen pick FROM and TO after.")
        elif val == "contact":
            await q.message.reply_text("Contact Admin: @autoscoutng\nSend your message there and we will reply.")
        elif val == "settings":
            await q.message.reply_text("Settings:\n- Language: English\n- Default: Convert\n\nType /start to go back.")
        return
    if kind == "DONE":
        if val == "again":
            c.user_data["mode"] = "convert"; c.user_data.pop("f", None); c.user_data.pop("t", None)
            await q.message.reply_text("Pick FROM:", reply_markup=grid("F"))
        elif val == "back":
            f = c.user_data.get("f"); t = c.user_data.get("t"); nc = c.user_data.get("last_new")
            if not f or not t or not nc:
                await q.message.reply_text("Nothing to convert back. Type /start")
                return
            c.user_data["f"] = t; c.user_data["t"] = f; c.user_data["mode"] = "convert"
            await q.message.reply_text(f"Converting back {nc} from {show(t)} to {show(f)}...")
            new_code, err = await do_convert(t, f, nc)
            if new_code:
                c.user_data["last_new"] = new_code
                await q.message.reply_text(f"Done!\nFrom: {show(t)}\nTo: {show(f)}\nNew Code: {new_code}", reply_markup=done_kb())
            else:
                await q.message.reply_text(f"Failed: {err}", reply_markup=done_kb())
        elif val == "share":
            nc = c.user_data.get("last_new", "")
            await q.message.reply_text(f"Share this code:\n{nc}\n\nForward this message to your friends, or copy the code above.")
        elif val == "menu":
            await q.message.reply_text("Elite Dashboard\nTap on your next move:", reply_markup=dash())
        return
    if kind == "F":
        c.user_data["f"] = val
        mode = c.user_data.get("mode", "convert")
        await q.message.reply_text(f"From: {show(val)}\nNow pick TO:", reply_markup=grid("T", exclude=val))
    elif kind == "T":
        c.user_data["t"] = val
        mode = c.user_data.get("mode", "convert")
        if mode == "merge":
            await q.message.reply_text(f"From {show(c.user_data['f'])} to {show(val)}.\nSend 2 codes separated by comma, like:\nCODE1, CODE2")
        elif mode == "split":
            await q.message.reply_text(f"From {show(c.user_data['f'])} to {show(val)}.\nSend your code to split:")
        else:
            await q.message.reply_text(f"From {show(c.user_data['f'])} to {show(val)}. Send your code now:")

async def code(u: Update, c: ContextTypes.DEFAULT_TYPE):
    txt = u.message.text.strip()
    mode = c.user_data.get("mode", "convert")
    if mode == "book":
        c.user_data["picks"] = txt
        c.user_data["mode"] = "convert"
        await u.message.reply_text("Picks saved. Now pick FROM to book them:", reply_markup=grid("F"))
        return
    if "f" not in c.user_data or "t" not in c.user_data:
        await u.message.reply_text("Type /start first and pick FROM and TO")
        return
    f = c.user_data["f"]; t = c.user_data["t"]
    if mode == "merge" and "," in txt:
        codes = [x.strip().upper() for x in txt.split(",") if x.strip()]
        await u.message.reply_text("Converting both...")
        out = []
        for cd in codes:
            nc, err = await do_convert(f, t, cd)
            out.append(f"{cd} -> {nc if nc else 'FAILED: '+str(err)[:200]}")
        await u.message.reply_text("Combine Done:\n" + "\n".join(out), reply_markup=done_kb())
        return
    cd = txt.upper()
    await u.message.reply_text("Converting...")
    nc, err = await do_convert(f, t, cd)
    if not nc:
        await u.message.reply_text(f"Failed: {err}\nCheck code is real and not expired.", reply_markup=done_kb())
        return
    c.user_data["last_new"] = nc; c.user_data["last_old"] = cd
    picks = c.user_data.get("picks")
    extra = f"\nPicks: {picks[:200]}" if picks else ""
    await u.message.reply_text(f"Done!\nFrom: {show(f)}\nTo: {show(t)}\nOld Code: {cd}\nNew Code: {nc}{extra}", reply_markup=done_kb())

async def cmd_convert(u: Update, c: ContextTypes.DEFAULT_TYPE):
    c.user_data["mode"] = "convert"
    await u.message.reply_text("Pick FROM:", reply_markup=grid("F"))
async def cmd_merge(u: Update, c: ContextTypes.DEFAULT_TYPE):
    c.user_data["mode"] = "merge"
    await u.message.reply_text("Combine: Pick FROM:", reply_markup=grid("F"))
async def cmd_split(u: Update, c: ContextTypes.DEFAULT_TYPE):
    c.user_data["mode"] = "split"
    await u.message.reply_text("Split: Pick FROM:", reply_markup=grid("F"))
async def cmd_contact(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("Contact Admin: @autoscoutng")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("convert", cmd_convert))
app.add_handler(CommandHandler("merge", cmd_merge))
app.add_handler(CommandHandler("split", cmd_split))
app.add_handler(CommandHandler("contact", cmd_contact))
app.add_handler(CallbackQueryHandler(btn))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, code))
app.run_polling()
