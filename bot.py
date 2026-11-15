import os, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
MBC_KEY = os.environ.get("MBC_KEY")
API = "https://api.managebetcodes.app/v1/convert"
VIEW_API = "https://api.managebetcodes.app/v1/view"

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

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    c.user_data.clear()
    name = u.effective_user.first_name or "Samuel"
    await u.message.reply_text(f"Elite Dashboard\n\n{name}. Tap on your next move:", reply_markup=dash())

async def do_convert(frm, to, code):
    try:
        r = requests.post(API, json={"code": code, "from": api_slug(frm), "to": api_slug(to)}, headers={"X-API-Key": MBC_KEY, "Content-Type": "application/json"}, timeout=45)
        if r.status_code != 200:
            try:
                j = r.json()
                msg = j.get("error", {}).get("message", "") if isinstance(j, dict) else ""
            except Exception:
                msg = ""
            return None, f"API said {r.status_code}. {msg} Check code is fresh and from {show(frm)}."
        j = r.json()
        if isinstance(j, dict) and "error" in j:
            return None, f"{j['error'].get('message','Conversion failed')}"
        nc = None
        if isinstance(j, dict):
            if isinstance(j.get("target"), dict): nc = j["target"].get("code")
            if not nc: nc = j.get("converted_code") or j.get("new_code") or j.get("code")
        if not nc: return None, "API replied but no new code. Code may be expired."
        return nc, None
    except Exception as e:
        return None, f"Error: {str(e)[:200]}"

def extract_games(j):
    try:
        for key in ["games", "selections", "items", "legs"]:
            if isinstance(j, dict) and isinstance(j.get(key), list) and j.get(key):
                out = []
                for g in j[key][:15]:
                    if isinstance(g, dict):
                        home = g.get("home") or g.get("home_team") or ""
                        away = g.get("away") or g.get("away_team") or ""
                        market = g.get("market") or g.get("name") or ""
                        sel = g.get("selection") or g.get("pick") or ""
                        out.append(f"- {home} vs {away} : {market} {sel}".strip())
                    else:
                        out.append(f"- {str(g)[:100]}")
                return "\n".join(out)
        if isinstance(j, dict) and isinstance(j.get("data"), dict):
            d = j["data"]
            for key in ["games", "selections", "items", "legs"]:
                if isinstance(d.get(key), list) and d.get(key):
                    return "\n".join([f"- {str(g)[:100]}" for g in d[key][:15]])
        if isinstance(j, dict) and isinstance(j.get("target"), dict) and isinstance(j["target"].get("games"), list):
            return "\n".join([f"- {str(g)[:100]}" for g in j["target"]["games"][:15]])
    except Exception:
        pass
    return None

async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    parts = q.data.split("|", 1)
    kind = parts[0]; val = parts[1] if len(parts) > 1 else ""
    if kind == "MENU":
        if val == "convert":
            c.user_data["mode"] = "convert"; c.user_data.pop("f", None); c.user_data.pop("t", None)
            await q.message.reply_text("Pick FROM:", reply_markup=grid("F"))
        elif val == "view" or val == "predict":
            c.user_data["mode"] = val; c.user_data.pop("f", None); c.user_data.pop("t", None)
            await q.message.reply_text("Pick FROM only - no TO needed:", reply_markup=grid("F"))
        elif val == "merge":
            c.user_data["mode"] = "merge"; c.user_data.pop("f", None); c.user_data.pop("t", None)
            await q.message.reply_text("Combine: Pick FROM:", reply_markup=grid("F"))
        elif val == "split":
            c.user_data["mode"] = "split"; c.user_data.pop("f", None); c.user_data.pop("t", None)
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
            c.user_data["mode"] = "convert"; c.user_data.pop("f", None); c.user_data.pop("t", None)
            await q.message.reply_text("Pick FROM:", reply_markup=grid("F"))
        elif val == "back":
            f = c.user_data.get("f"); t = c.user_data.get("t"); nc = c.user_data.get("last_new")
            if not f or not t or not nc:
                await q.message.reply_text("Nothing to convert back. Type /start"); return
            c.user_data["f"] = t; c.user_data["t"] = f; c.user_data["mode"] = "convert"
            await q.message.reply_text(f"Converting back {nc}...")
            new_code, err = await do_convert(t, f, nc)
            if new_code:
                c.user_data["last_new"] = new_code
                await q.message.reply_text(f"Done!\nFrom: {show(t)}\nTo: {show(f)}\nNew Code: {new_code}", reply_markup=done_kb())
            else:
               
