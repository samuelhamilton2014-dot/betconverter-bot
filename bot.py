import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")
API = "https://api.managebetcodes.app/v1/convert"
VIEW_API = "https://api.managebetcodes.app/v1/view"

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
        [InlineKeyboardButton("View Code", callback_data="MENU|view"), InlineKeyboardButton("Predict", callback_data="MENU|predict")],
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

async def start(u, c):
    c.user_data.clear()
    name = u.effective_user.first_name
    if not name:
        name = "Samuel"
    await u.message.reply_text("Elite Dashboard\n\n" + name + ". Tap on your next move:", reply_markup=dash())

async def do_convert(frm, to, code):
    try:
        r = requests.post(API, json={"code": code, "from": api_slug(frm), "to": api_slug(to)}, headers={"X-API-Key": MBC_KEY, "Content-Type": "application/json"}, timeout=45)
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

def extract_games(j):
    try:
        for key in ["games", "selections", "items", "legs"]:
            if isinstance(j, dict):
                if isinstance(j.get(key), list):
                    if len(j.get(key)) > 0:
                        out = []
                        for g in j[key][:15]:
                            if isinstance(g, dict):
                                home = g.get("home") or g.get("home_team") or ""
                                away = g.get("away") or g.get("away_team") or ""
                                market = g.get("market") or g.get("name") or ""
                                sel = g.get("selection") or g.get("pick") or ""
                                out.append("- " + str(home) + " vs " + str(away) + " : " + str(market) + " " + str(sel))
                            else:
                                out.append("- " + str(g)[:100])
                        return "\n".join(out)
        if isinstance(j, dict):
            if isinstance(j.get("data"), dict):
                d = j["data"]
                for key in ["games", "selections", "items", "legs"]:
                    if isinstance(d.get(key), list):
                        if len(d.get(key)) > 0:
                            return "\n".join(["- " + str(g)[:100] for g in d[key][:15]])
    except Exception:
        pass
    return None

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
        elif val == "view":
            c.user_data["mode"] = "view"
            c.user_data.pop("f", None)
            c.user_data.pop("t", None)
            await q.message.reply_text("Pick FROM only - no TO needed:", reply_markup=grid("F"))
        elif val == "predict":
            c.user_data["mode"] = "predict"
            c.user_data.pop("f", None)
            c.user_data.pop("t", None)
            await q.message.reply_text("Pick FROM only - no TO needed:", reply_markup=grid("F"))
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
        elif val == "book":
            c.user_data["mode"] = "book"
            await q.message.reply_text("Book My Picks: Send your picks, one per line.")
        elif val == "contact":
            await q.message.reply_text("Contact Admin: @autoscoutng")
        elif val == "settings":
            await q.message.reply_text("Settings:\n- Language: English\n\nType /start to go back.")
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
        mode = c.user_data.get("mode", "convert")
        if mode == "view":
            c.user_data["t"] = val
            await q.message.reply_text("From: " + show(val) + ".\nSend your code now - no TO needed:")
            return
        if mode == "predict":
            c.user_data["t"] = val
            await q.message.reply_text("From: " + show(val) + ".\nSend your code now - no TO needed:")
            return
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
    if mode == "book":
        c.user_data["picks"] = txt
        c.user_data["mode"] = "convert"
        await u.message.reply_text("Picks saved. Now pick FROM:", reply_markup=grid("F"))
        return
    if "f" not in c.user_data:
        await u.message.reply_text("Type /start first")
        return
    f = c.user_data["f"]
    t = c.user_data.get("t", f)
    if mode == "view":
        await u.message.reply_text("Reading code...")
        try:
            r = requests.post(VIEW_API, json={"code": txt.upper(), "from": api_slug(f)}, headers={"X-API-Key": MBC_KEY, "Content-Type": "application/json"}, timeout=30)
            if r.status_code != 200:
                await u.message.reply_text("Could not read code. Check it is a fresh " + show(f) + " code and not expired.", reply_markup=done_kb())
                return
            j = r.json()
            if isinstance(j, dict):
                if "error" in j:
                    await u.message.reply_text("Could not read code: " + str(j["error"].get("message", "Code invalid or expired")), reply_markup=done_kb())
                    return
            games = extract_games(j)
            if games:
                await u.message.reply_text("Games in " + txt.upper() + " from " + show(f) + ":\n" + games, reply_markup=done_kb())
            else:
                await u.message.reply_text("Code " + txt.upper() + " is valid from " + show(f) + ".", reply_markup=done_kb())
        except Exception as e:
            await u.message.reply_text("Could not read code: " + str(e)[:200], reply_markup=done_kb())
        return
    if mode == "predict":
        await u.message.reply_text("Reading code...")
        try:
            r = requests.post(VIEW_API, json={"code": txt.upper(), "from": api_slug(f)}, headers={"X-API-Key": MBC_KEY, "Content-Type": "application/json"}, timeout=30)
            if r.status_code != 200:
                await u.message.reply_text("Could not read code. Check it is a fresh " + show(f) + " code and not expired.", reply_markup=done_kb())
                return
            j = r.json()
            if isinstance(j, dict):
                if "error" in j:
                    await u.message.reply_text("Could not read code: " + str(j["error"].get("message", "Code invalid or expired")), reply_markup=done_kb())
                    return
            games = extract_games(j)
            if games:
                await u.message.reply_text("Prediction check for " + txt.upper() + ":\n" + games + "\n\nForm-based analysis only, not a sure win.", reply_markup=done_kb())
            else:
                await u.message.reply_text("Code " + txt.upper() + " is valid.\nPrediction: Check form on " + show(f) + " app. Not a sure win.", reply_markup=done_kb())
        except Exception as e:
            await u.message.reply_text("Could not read code: " + str(e)[:200], reply_markup=done_kb())
        return
    if "t" not in c.user_data:
        await u.message.reply_text("Pick TO first")
        return
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
            await u.message.reply_text("Combine Done:\n" + "\n".join(out), reply_markup=done_kb())
            return
    cd = txt.upper()
    await u.message.reply_text("Converting...")
    nc, err = await do_convert(f, t, cd)
    if not nc:
        await u.message.reply_text("Failed: " + err, reply_markup=done_kb())
        return
    c.user_data["last_new"] = nc
    c.user_data["last_old"] = cd
    await u.message.reply_text("Done!\nFrom: " + show(f) + "\nTo: " + show(t) + "\nOld Code: " + cd + "\nNew Code: " + nc, reply_markup=done_kb())

async def cmd_convert(u, c):
    c.user_data["mode"] = "convert"
    await u.message.reply_text("Pick FROM:", reply_markup=grid("F"))

async def cmd_merge(u, c):
    c.user_data["mode"] = "merge"
    await u.message.reply_text("Combine: Pick FROM:", reply_markup=grid("F"))

async def cmd_split(u, c):
    c.user_data["mode"] = "split"
    await u.message.reply_text("Split: Pick FROM:", reply_markup=grid("F"))

async def cmd_contact(u, c):
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
