# -*- coding: utf-8 -*-
"""
main.py – Crypto Signal Bot 🔥 gestión avanzada multi-suscripciones
– Google Sheets como base de datos (usuarios, planes, fechas)
– Avisos −5 min y expulsión a 0 min (7/15/30/365 días según plan), sin ban
– Mensajes de aviso/expiración con botón de renovación
– /start <token> → selección idioma → enlace único + imagen de bienvenida
– Bienvenida automática en cada grupo al añadir un usuario
– Comando /misdatos con menú de idioma y sub-menú de renovación
– Tabla HTML /usuarios-activos
– Chequeo de suscripciones cada minuto (APScheduler)
– /ping para mantener la app despierta
"""

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import json, logging, requests, base64, os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ───────────────────────────────────────── CONFIG ─────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "7457058289:AAF-VN0UWiduteBV79VdKxgIT2yeg9wa-LQ")
FIRE_IMG    = "https://cryptosignalbot.com/wp-content/uploads/2025/02/Fire-Scalping-Senales-de-Trading-para-Ganar-Mas-en-Cripto-3.png"
ELITE_IMG   = "https://cryptosignalbot.com/wp-content/uploads/2025/02/ELITE-Scalping-Intradia-Senales-en-Tiempo-Real.png"
DELTA_IMG   = "https://cryptosignalbot.com/wp-content/uploads/2025/03/delta-swing-trading-crypto-signal.png"
RENEWAL_URL = "https://cryptosignalbot.com/mi-cuenta"
LOG_FILE    = "csb_events.log"

PLANS = {
    # FIRE
    "GRATIS_ES":       {"duration_min":  7*24*60,  "group_id_es":"-1002470074373", "group_id_en":"-1002371800315"},
    "MES_ES":          {"duration_min": 30*24*60,  "group_id_es":"-1002470074373", "group_id_en":"-1002371800315"},
    "ANIO_ES":         {"duration_min":365*24*60,  "group_id_es":"-1002470074373", "group_id_en":"-1002371800315"},
    # ÉLITE
    "GRATIS_ES_ELITE": {"duration_min":15*24*60,   "group_id_es":"-1002437381292", "group_id_en":"-1002432864193"},
    "MES_ES_ELITE":    {"duration_min":30*24*60,   "group_id_es":"-1002437381292", "group_id_en":"-1002432864193"},
    "ANIO_ES_ELITE":   {"duration_min":365*24*60,  "group_id_es":"-1002437381292", "group_id_en":"-1002432864193"},
    # DELTA
    "GRATIS_ES_DELTA": {"duration_min":30*24*60,   "group_id_es":"-1002299713092", "group_id_en":"-1002428632182"},
    "MES_ES_DELTA":    {"duration_min":30*24*60,   "group_id_es":"-1002299713092", "group_id_en":"-1002428632182"},
    "ANIO_ES_DELTA":   {"duration_min":365*24*60,  "group_id_es":"-1002299713092", "group_id_en":"-1002428632182"},
}

LABELS = {
    "GRATIS_ES":       "𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠 · Gratis 7 días",
    "MES_ES":          "𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠 · Mensual",
    "ANIO_ES":         "𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠 · Anual",
    "GRATIS_ES_ELITE": "𝐄𝐋𝐈𝐓𝐄 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠 𝐏𝐑𝐎 · Gratis 15 días",
    "MES_ES_ELITE":    "𝐄𝐋𝐈𝐓𝐄 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠 𝐏𝐑𝐎 · Mensual",
    "ANIO_ES_ELITE":   "𝐄𝐋𝐈𝐓𝐄 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠 𝐏𝐑𝐎 · Anual",
    "GRATIS_ES_DELTA": "𝐃𝐄𝐋𝐓𝐀 𝐒𝐰𝐢𝐧𝐠 · Gratis 30 días",
    "MES_ES_DELTA":    "𝐃𝐄𝐋𝐓𝐀 𝐒𝐰𝐢𝐧𝐠 · Mensual",
    "ANIO_ES_DELTA":   "𝐃𝐄𝐋𝐓𝐀 𝐒𝐰𝐢𝐧𝐠 · Anual",
}

TYPE_LABELS = {"Fire":"🔥 Fire Scaling", "Élite":"💎 Élite Scaling PRO", "Delta":"🪙 Delta Swing"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
log = logging.getLogger("CSB")

# ─────────────────────────────────────── Google Sheets helpers ───────────────────────────────────────
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(os.environ["GS_CREDENTIALS_JSON"]), scope
    )
    client = gspread.authorize(creds)
    return client.open_by_key(os.environ["GS_SHEET_ID"]).sheet1

def load_users():
    rows = get_sheet().get_all_records()
    users = {}
    for r in rows:
        email = r["email"]
        stype = get_sub_type(r["plan"])
        users.setdefault(email, {"chat_id":r["chat_id"], "lang":r["lang"], "suscripciones":{}})
        users[email]["suscripciones"][stype] = {
            "plan":r["plan"], "ingreso":r["ingreso"], "expira":r["expira"],
            "avisado":False, "invite_link":None
        }
    return users

def save_users(users):
    data = [["chat_id","email","plan","lang","ingreso","expira"]]
    for email,info in users.items():
        for sub in info["suscripciones"].values():
            data.append([
                info["chat_id"], email, sub["plan"], info["lang"],
                sub["ingreso"], sub["expira"]
            ])
    sh = get_sheet()
    sh.clear()
    sh.update(data)

def get_sub_type(plan):
    if plan.endswith("_ELITE"): return "Élite"
    if plan.endswith("_DELTA"): return "Delta"
    return "Fire"

def enlace_unico(group_id):
    try:
        expire_ts = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/createChatInviteLink",
            json={"chat_id":group_id,"member_limit":1,"expire_date":expire_ts},
            timeout=10
        ).json()
        link = resp.get("result", {}).get("invite_link")
        if not link:
            log.error(f"No invite link in response: {resp}")
        return link
    except Exception as e:
        log.error(f"createChatInviteLink failed: {e}")
        return None

# ───────────────────────────────────── chequear suscripciones ─────────────────────────────────────
def check_subscriptions():
    users = load_users()
    now = datetime.utcnow()
    modified = False

    for email,info in list(users.items()):
        cid = info.get("chat_id")
        lang = info.get("lang","ES")
        for stype,sub in list(info["suscripciones"].items()):
            try:
                exp_dt = datetime.fromisoformat(sub["expira"])
            except:
                continue
            secs = (exp_dt - now).total_seconds()

            # Aviso 5 min antes
            if secs <= 300 and not sub["avisado"]:
                text = (
                    f"⏳ Tu suscripción {TYPE_LABELS[stype]} expira en 24 horas. "
                    "Renueva para no perder acceso."
                    if lang=="ES" else
                    f"⏳ Your {TYPE_LABELS[stype]} subscription expires in 24 hours. "
                    "Renew to keep access."
                )
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id":cid,
                        "text":text,
                        "reply_markup":{"inline_keyboard":[[
                            {"text":"🔄 Renovar","callback_data":f"renovar_menu|{stype}"}
                        ]]}
                    },
                    timeout=10
                )
                sub["avisado"] = True
                modified = True

            # Expiración
            if secs <= 0:
                grp = PLANS[sub["plan"]][f"group_id_{lang.lower()}"]
                if sub["invite_link"]:
                    try:
                        requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/revokeChatInviteLink",
                            json={"chat_id":grp,"invite_link":sub["invite_link"]},
                            timeout=10
                        )
                    except Exception as e:
                        log.error(f"Error revoking invite link: {e}")
                text = (
                    f"❌ Tu suscripción {TYPE_LABELS[stype]} ha expirado."
                    if lang=="ES" else
                    f"❌ Your {TYPE_LABELS[stype]} subscription has expired."
                )
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id":cid,
                        "text":text,
                        "reply_markup":{"inline_keyboard":[[
                            {"text":"🔄 Renovar","callback_data":f"renovar_menu|{stype}"}
                        ]]}
                    },
                    timeout=10
                )
                # Expulsar y desbanear
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/kickChatMember",
                    json={"chat_id":grp,"user_id":cid}, timeout=10
                )
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/unbanChatMember",
                    json={"chat_id":grp,"user_id":cid}, timeout=10
                )
                del info["suscripciones"][stype]
                modified = True

        if not info["suscripciones"]:
            del users[email]
            modified = True

    if modified:
        save_users(users)

    BackgroundScheduler().add_job(check_subscriptions, "interval", minutes=1).start()

# ───────────────────────────────────── util: enviar invitación ─────────────────────────────────────
def send_invite(info,email,cid,lang,stype):
    sub = info["suscripciones"][stype]
    plan = sub["plan"]
    grp = PLANS[plan][f"group_id_{lang.lower()}"]
    link = enlace_unico(grp)
    if not link:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id":cid,"text":"⚠️ Error creando enlace. Intenta de nuevo."},
            timeout=10
        )
        return
    sub["invite_link"] = link
    users = load_users()
    users[email] = info
    save_users(users)

    img = FIRE_IMG if get_sub_type(plan)=="Fire" else ELITE_IMG if get_sub_type(plan)=="Élite" else DELTA_IMG
    caption = (
        "🚀 ¡Pulsa aquí para acceder a VIP o renovar!"
        if lang=="ES" else
        "🚀 Tap here to access VIP or renew!"
    )
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        json={
            "chat_id":cid,
            "photo":img,
            "caption":caption,
            "reply_markup":{"inline_keyboard":[[
                {"text":"🏆 Acceso VIP","url":link}
            ]]}
        },
        timeout=10
    )

# ───────────────────────────────────────── ping ────────────────────────────────────────
@app.route("/ping")
def ping():
    return "pong", 200

# ───────────────────────────────── registrar suscripciones ─────────────────────────────────
def _agregar_sub():
    d = request.get_json(force=True) or {}
    email = d.get("email")
    plan  = d.get("plan")
    if not email or plan not in PLANS:
        return jsonify({"status":"error"}), 400

    users = load_users()
    now = datetime.utcnow()
    info = users.get(email, {"suscripciones":{}})
    stype = get_sub_type(plan)
    old = info["suscripciones"].get(stype)

    base = now
    ingreso = now.isoformat()
    if old:
        try:
            exp_old = datetime.fromisoformat(old["expira"])
            if exp_old > now: base = exp_old
        except: pass
        ingreso = old["ingreso"]

    exp_new = (base + timedelta(minutes=PLANS[plan]["duration_min"])).isoformat()
    info["suscripciones"].update({
        stype: {
            "plan": plan,
            "ingreso": ingreso,
            "expira": exp_new,
            "avisado": False,
            "invite_link": old and old["invite_link"]
        }
    })
    info["pending_sub"] = stype
    users[email] = info
    save_users(users)

    return jsonify({"status":"ok","expira":exp_new}), 200

app.add_url_rule("/agregar-suscripción", "add_sub_tilde", _agregar_sub, methods=["POST"])
app.add_url_rule("/agregar-suscripcion",  "add_sub_notilde", _agregar_sub, methods=["POST"])

# ───────────────────────────────── tabla usuarios activos ─────────────────────────────────
@app.route("/usuarios-activos")
def usuarios_activos():
    users = load_users()
    now = datetime.utcnow()
    rows = []
    for email,info in users.items():
        lang = info.get("lang","ES")
        for stype,sub in info["suscripciones"].items():
            grp = PLANS[sub["plan"]][f"group_id_{lang.lower()}"]
            try:
                rem = f"{(datetime.fromisoformat(sub['expira']) - now).total_seconds()/60:.1f} min"
            except:
                rem = "—"
            rows.append((
                info.get("chat_id"), email, stype, sub["plan"],
                lang, grp, sub["ingreso"], sub["expira"], rem
            ))
    rows.sort(key=lambda x: float(x[8].split()[0]) if "min" in x[8] else 999)
    return render_template_string("""
<html><body><h2>Usuarios activos</h2><table border=1>
<tr>
  <th>Chat ID</th><th>Email</th><th>Tipo</th><th>Plan</th><th>Idioma</th>
  <th>Grupo</th><th>Ingreso</th><th>Expira</th><th>Restante</th>
</tr>
{% for r in rows %}
<tr>
  {% for c in r %}<td>{{c}}</td>{% endfor %}
</tr>
{% endfor %}
</table></body></html>
""", rows=rows)

# ───────────────────────────────── Telegram webhook ─────────────────────────────────
@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    up = request.get_json(force=True)

    # Bienvenida en grupos
    if "message" in up and up["message"].get("new_chat_members"):
        chat_id = up["message"]["chat"]["id"]
        for m in up["message"]["new_chat_members"]:
            if m.get("is_bot"): continue
            user = m.get("first_name","")
            plan_key = None
            lang = "ES"
            for k,d in PLANS.items():
                if d["group_id_es"] == str(chat_id):
                    plan_key, lang = k, "ES"; break
                if d["group_id_en"] == str(chat_id):
                    plan_key, lang = k, "EN"; break
            stype = get_sub_type(plan_key) if plan_key else ""
            lbl = TYPE_LABELS.get(stype, stype)
            txt_es = f"""👋 ¡Bienvenido al plan {lbl}, {user}! ¡Bienvenido al Grupo VIP de Crypto Signal Bot!

📈 Señales en tiempo real | Máxima precisión
🔹 BTC · ETH · XRP · BNB · ADA
🔹 Scalping, intradía y swing
🔗 Acceso rápido en nuestra web
🚀 ¡Impulsa tu trading!"""
            txt_en = f"""👋 Welcome to the {lbl} Plan, {user}! Crypto Signal Bot VIP

📈 Real-time signals | High accuracy
🔹 BTC · ETH · XRP · BNB · ADA
🔹 Scalping, intraday & swing
🔗 Quick access on our website
🚀 Boost your trading!"""
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id":chat_id,"text":(txt_es if lang=="ES" else txt_en)},
                timeout=10
            )
        return jsonify({}), 200

    # /start <token> deep link
    if "message" in up and up["message"].get("text","").startswith("/start "):
        text = up["message"]["text"]; cid = up["message"]["chat"]["id"]
        token = text.split(maxsplit=1)[1]; token += "="*((4-len(token)%4)%4)
        try:
            email = base64.urlsafe_b64decode(token.encode()).decode()
        except:
            return jsonify({}), 200
        users = load_users(); info = users.get(email)
        if not info:
            return jsonify({}), 200
        info["chat_id"] = cid; users[email] = info; save_users(users)
        kb = {"inline_keyboard":[[
            {"text":"🇪🇸 Español","callback_data":f"lang|ES|{email}"},
            {"text":"🇺🇸 English","callback_data":f"lang|EN|{email}"}
        ]]}
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id":cid,"text":"🌐 Selecciona idioma / Select language","reply_markup":kb},
            timeout=10
        )
        return jsonify({}), 200

    # Otros comandos y textos
    if "message" in up:
        msg = up["message"]; cid = msg["chat"]["id"]; text = msg.get("text","").strip()
        if text == "/start":
            kb = {"inline_keyboard":[[{"text":"🌐 Idioma/Language","url":
                  "https://t.me/CriptoSignalBotGestion_bot?start=6848494ba35fe4e8f30495ea"}]]}
            txt = ("🇪🇸 Elige idioma para comenzar.\n\n🇺🇸 Choose language to start.")
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id":cid,"text":txt,"reply_markup":kb}, timeout=10
            )
            return jsonify({}), 200
        if text == "/misdatos":
            kb = {"inline_keyboard":[
                [{"text":"🇪🇸 Español","callback_data":"misdatos_lang|ES"}],
                [{"text":"🇺🇸 English","callback_data":"misdatos_lang|EN"}]
            ]}
            txt_es = "👤 *Cuenta*\nSelecciona idioma para ver tus suscripciones."
            txt_en = "👤 *Account*\nSelect language to view your subscriptions."
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id":cid,"text":txt_es+"\n\n"+txt_en,"parse_mode":"Markdown","reply_markup":kb},
                timeout=10
            )
            return jsonify({}), 200
        # Ignorar texto libre
        if text and not text.startswith("/"):
            return jsonify({}), 200

    # Callbacks
    if "callback_query" in up:
        cq = up["callback_query"]; data = cq["data"]; cid = cq["from"]["id"]
        users = load_users()

        # Selección de idioma tras /start
        if data.startswith("lang|"):
            _,lang,email = data.split("|",2); info = users.get(email)
            if not info or info.get("chat_id") != cid:
                return jsonify({}), 200
            info["lang"] = lang
            stype = info.pop("pending_sub", None)
            if not stype:
                latest = None; fecha = datetime.min
                for st,sub in info["suscripciones"].items():
                    try:
                        f = datetime.fromisoformat(sub["ingreso"])
                    except:
                        continue
                    if f > fecha:
                        fecha, latest = f, st
                stype = latest
            if stype:
                send_invite(info, email, cid, lang, stype)
            return jsonify({}), 200

        # misdatos idioma
        if data.startswith("misdatos_lang|"):
            _,lang = data.split("|",1)
            pair = next(((e,i) for e,i in users.items() if i.get("chat_id")==cid), None)
            if not pair:
                txt = "Usted no posee ninguna suscripción." if lang=="ES" else "You have no active subscriptions."
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id":cid,"text":txt}, timeout=10
                )
                return jsonify({}), 200
            email, info = pair
            name = info.get("nombre","") + " " + info.get("apellido","")
            phone = info.get("telefono","")
            subs = info["suscripciones"]
            if not subs:
                txt = (f"Nombre: {name}\nCorreo: {email}\nTeléfono: {phone}\n\n"
                       "Usted no posee ninguna suscripción.") if lang=="ES" else (
                       f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\n"
                       "You have no active subscriptions.")
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id":cid,"text":txt}, timeout=10
                )
                return jsonify({}), 200
            rep = ("Hola "+name+",\n\n*Tus suscripciones activas:*"
                   if lang=="ES" else
                   "Hello "+name+",\n\n*Your active subscriptions:*")
            keyboard = []
            now = datetime.utcnow()
            for st,sub in subs.items():
                plan = sub["plan"]; plan_lbl = LABELS.get(plan, plan)
                ing = datetime.fromisoformat(sub["ingreso"]).strftime("%Y-%m-%d %H:%M")
                exp_dt = datetime.fromisoformat(sub["expira"])
                exp = exp_dt.strftime("%Y-%m-%d %H:%M")
                delta = exp_dt - now
                total = int(delta.total_seconds())
                months = total // (30*24*3600)
                days = (total // (24*3600)) % 30
                hours = (total // 3600) % 24
                mins = (total // 60) % 60
                if lang=="ES":
                    rep += (
                        f"\n\n• {TYPE_LABELS[st]}: {plan_lbl}\n"
                        f"  - Ingreso: {ing}\n"
                        f"  - Expira: {exp}\n"
                        f"  - Restante: {months} mes, {days} d, {hours} h, {mins} min"
                    )
                    keyboard.append([{"text":f"🔄 Renovar {TYPE_LABELS[st]}","callback_data":f"renovar_menu|{st}"}])
                else:
                    rep += (
                        f"\n\n• {TYPE_LABELS[st]}: {plan_lbl}\n"
                        f"  - Start: {ing}\n"
                        f"  - Expires: {exp}\n"
                        f"  - Remaining: {months} mo, {days} d, {hours} h, {mins} m"
                    )
                    keyboard.append([{"text":f"🔄 Renew {TYPE_LABELS[st]}","callback_data":f"renovar_menu|{st}"}])
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id":cid,"text":rep,"parse_mode":"Markdown","reply_markup":{"inline_keyboard":keyboard}},
                timeout=10
            )
            return jsonify({}), 200

        # Sub-menú renovar
        if data.startswith("renovar_menu|"):
            _,stype = data.split("|",1)
            lang = next((i.get("lang","ES") for i in users.values() if i.get("chat_id")==cid), "ES")
            if stype == "Fire":
                mes,ann = RENEWAL_URL+"?renewal=1", RENEWAL_URL+"?anual=1"
                label = "Fire"
            elif stype == "Élite":
                mes,ann = RENEWAL_URL+"?renewal_elite=1", RENEWAL_URL+"?annual_elite=1"
                label = "Élite"
            elif stype == "Delta":
                mes,ann = RENEWAL_URL+"?renewal_delta=1", RENEWAL_URL+"?annual_delta=1"
                label = "Delta"
            else:
                mes = ann = RENEWAL_URL
                label = stype

            if lang=="ES":
                text = f"Selecciona renovación para {label}:"
                btn1 = {"text":f"🔄 Mes","url":mes}
                btn2 = {"text":"🔄 Año (–30%)","url":ann}
            else:
                text = f"Select renewal for {label}:"
                btn1 = {"text":"🔄 Month","url":mes}
                btn2 = {"text":"🔄 Year (–30%)","url":ann}

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id":cid,"text":text,"reply_markup":{"inline_keyboard":[[btn1],[btn2]]}},
                timeout=10
            )
            return jsonify({}), 200

    return jsonify({}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
