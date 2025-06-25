# -*- coding: utf-8 -*-
"""
main.py – Crypto Signal Bot 🔥 gestión avanzada multi-suscripciones

• Almacena usuarios y suscripciones en Google Sheets (ya NO usa JSON local)
• Avisos −5 min antes y expulsión al vencer (7/15/30 d según plan), sin ban
• Mensajes de renovación, bienvenida, /misdatos, tabla /usuarios-activos, /ping
• Revisión automática cada minuto con APScheduler
"""

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import os, json, logging, requests, base64, gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ───────── CONFIGURACIÓN ──────────
BOT_TOKEN        = "7457058289:AAF-VN0UWiduteBV79VdKxgIT2yeg9wa-LQ"
FIRE_IMAGE_URL   = "https://cryptosignalbot.com/wp-content/uploads/2025/02/Fire-Scalping-Senales-de-Trading-para-Ganar-Mas-en-Cripto-3.png"
ELITE_IMAGE_URL  = "https://cryptosignalbot.com/wp-content/uploads/2025/02/ELITE-Scalping-Intradia-Senales-en-Tiempo-Real.png"
DELTA_IMAGE_URL  = "https://cryptosignalbot.com/wp-content/uploads/2025/03/delta-swing-trading-crypto-signal.png"
RENEWAL_URL      = "https://cryptosignalbot.com/mi-cuenta"
LOG_FILE         = "csb_events.log"

# Planes y sus tiempos
PLANS = {
    # FIRE
    "GRATIS_ES":        {"duration_min":   7 * 24 * 60,  "group_id_es": "-1002470074373", "group_id_en": "-1002371800315"},
    "MES_ES":           {"duration_min":  30 * 24 * 60,  "group_id_es": "-1002470074373", "group_id_en": "-1002371800315"},
    "ANIO_ES":          {"duration_min": 365 * 24 * 60,  "group_id_es": "-1002470074373", "group_id_en": "-1002371800315"},
    # ÉLITE
    "GRATIS_ES_ELITE":  {"duration_min":  15 * 24 * 60,  "group_id_es": "-1002437381292", "group_id_en": "-1002432864193"},
    "MES_ES_ELITE":     {"duration_min":  30 * 24 * 60,  "group_id_es": "-1002437381292", "group_id_en": "-1002432864193"},
    "ANIO_ES_ELITE":    {"duration_min": 365 * 24 * 60,  "group_id_es": "-1002437381292", "group_id_en": "-1002432864193"},
    # DELTA
    "GRATIS_ES_DELTA":  {"duration_min":  30 * 24 * 60,  "group_id_es": "-1002299713092", "group_id_en": "-1002428632182"},
    "MES_ES_DELTA":     {"duration_min":  30 * 24 * 60,  "group_id_es": "-1002299713092", "group_id_en": "-1002428632182"},
    "ANIO_ES_DELTA":    {"duration_min": 365 * 24 * 60,  "group_id_es": "-1002299713092", "group_id_en": "-1002428632182"},
}

# Etiquetas legibles
LABELS = {
    "GRATIS_ES":        "𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠 · Gratis 7 días",
    "MES_ES":           "𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠 · Mensual",
    "ANIO_ES":          "𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠 · Anual",
    "GRATIS_ES_ELITE":  "𝐄𝐋𝐈𝐓𝐄 · Gratis 15 días",
    "MES_ES_ELITE":     "𝐄𝐋𝐈𝐓𝐄 · Mensual",
    "ANIO_ES_ELITE":    "𝐄𝐋𝐈𝐓𝐄 · Anual",
    "GRATIS_ES_DELTA":  "𝐃𝐄𝐋𝐓𝐀 Swing · Gratis 30 días",
    "MES_ES_DELTA":     "𝐃𝐄𝐋𝐓𝐀 Swing · Mensual",
    "ANIO_ES_DELTA":    "𝐃𝐄𝐋𝐓𝐀 Swing · Anual",
}

TYPE_LABELS = {
    "Fire":  "🔥 𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠",
    "Élite": "💎 𝐄𝐋𝐈𝐓𝐄 𝐒𝐜𝐚𝐥𝐩𝐢𝐧𝐠 𝐏𝐑𝐎",
    "Delta": "🪙 𝐃𝐄𝐋𝐓𝐀 Swing",
}

# ───── LOGGING ─────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
log = logging.getLogger("CSB")

# ───── HELPERS Google Sheets ─────────────────────────────────────────
def get_sheet():
    """Devuelve la pestaña (sheet1) indicada por GS_SHEET_ID."""
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds_json = json.loads(os.environ["GS_CREDENTIALS_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(os.environ["GS_SHEET_ID"]).sheet1


def load_users():
    """Carga todos los usuarios desde la hoja → mismo dict que usaba JSON."""
    rows = get_sheet().get_all_records()
    users = {}
    for row in rows:
        if not row.get("email"):
            continue
        email = row["email"].strip()
        stype = get_sub_type(row["plan"])
        users.setdefault(email, {
            "chat_id":  row["chat_id"],
            "lang":     row.get("lang") or "ES",
            "nombre":   row.get("nombre", ""),
            "apellido": row.get("apellido", ""),
            "telefono": row.get("telefono", ""),
            "suscripciones": {}
        })
        users[email]["suscripciones"][stype] = {
            "plan":        row["plan"],
            "ingreso":     row["ingreso"],
            "expira":      row["expira"],
            "avisado":     str(row.get("avisado")).upper() == "TRUE",
            "invite_link": row.get("invite_link") or None
        }
    return users


def save_users(users):
    """Sobrescribe la hoja con el estado actual del diccionario."""
    data = [["chat_id","email","plan","lang",
             "ingreso","expira","avisado","invite_link",
             "nombre","apellido","telefono"]]
    for email, info in users.items():
        for sub in info["suscripciones"].values():
            data.append([
                info.get("chat_id",""),
                email,
                sub["plan"],
                info.get("lang","ES"),
                sub["ingreso"],
                sub["expira"],
                str(sub.get("avisado", False)),
                sub.get("invite_link") or "",
                info.get("nombre",""),
                info.get("apellido",""),
                info.get("telefono","")
            ])
    sh = get_sheet()
    sh.clear()
    sh.update(data)

# ───── OTROS HELPERS ────────────────────────────────────────────────
def get_sub_type(plan_key: str) -> str:
    if plan_key.endswith("_ELITE"):
        return "Élite"
    if plan_key.endswith("_DELTA"):
        return "Delta"
    return "Fire"


def enlace_unico(group_id: str) -> str | None:
    """Crea un enlace de invitación (1 uso, 24 h) al grupo de Telegram."""
    try:
        expire_ts = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/createChatInviteLink",
            json={"chat_id": group_id, "member_limit": 1, "expire_date": expire_ts},
            timeout=10
        ).json()
        return r.get("result", {}).get("invite_link")
    except Exception as e:
        log.error(f"createChatInviteLink failed: {e}")
        return None

# ───── CHEQUEO DE SUSCRIPCIONES ─────────────────────────────────────
def check_subscriptions():
    users = load_users()
    now   = datetime.utcnow()
    modified = False

    for email, info in list(users.items()):
        cid  = info.get("chat_id")
        lang = info.get("lang", "ES")
        subs = info.get("suscripciones", {})

        for stype, sub in list(subs.items()):
            try:
                exp = datetime.fromisoformat(sub["expira"])
            except ValueError:
                continue
            secs = (exp - now).total_seconds()

            # Aviso 5 min antes
            if secs <= 300 and not sub.get("avisado"):
                text = (
                    "⏳ Tu suscripción "
                    f"{TYPE_LABELS.get(stype, stype)} expira en 24 horas. "
                    "Renueva tu suscripción y mantén el acceso a las señales de trading de Crypto Signal Bot. ¡No pierdas esta oportunidad!"
                    if lang == "ES" else
                    "⏳ Your "
                    f"{TYPE_LABELS.get(stype, stype)} subscription expires in 24 hours. "
                    "Renew now to keep receiving Crypto Signal Bot’s real-time trading signals."
                )
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": cid,
                        "text": text,
                        "reply_markup": {
                            "inline_keyboard": [[
                                {"text": "🔄 Renovar / Renew", "callback_data": f"renovar_menu|{stype}"}
                            ]]
                        }
                    },
                    timeout=10
                )
                sub["avisado"] = True
                modified = True

            # Expiración
            if secs <= 0:
                plan_key = sub["plan"]
                group_id = PLANS[plan_key][f"group_id_{lang.lower()}"]

                # revocar enlace antiguo
                if sub.get("invite_link"):
                    try:
                        requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/revokeChatInviteLink",
                            json={"chat_id": group_id, "invite_link": sub["invite_link"]},
                            timeout=10
                        )
                    except Exception as e:
                        log.warning(f"revokeChatInviteLink: {e}")

                exp_text = (
                    f"❌ Tu suscripción {TYPE_LABELS[stype]} ha expirado."
                    if lang == "ES" else
                    f"❌ Your {TYPE_LABELS[stype]} subscription has expired."
                )
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": cid,
                        "text": exp_text,
                        "reply_markup": {
                            "inline_keyboard": [[
                                {"text": "🔄 Renovar / Renew", "callback_data": f"renovar_menu|{stype}"}
                            ]]
                        }
                    },
                    timeout=10
                )
                # expulsar sin ban
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/kickChatMember",
                              json={"chat_id": group_id, "user_id": cid}, timeout=10)
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/unbanChatMember",
                              json={"chat_id": group_id, "user_id": cid}, timeout=10)

                subs.pop(stype)
                modified = True

        # limpieza si no quedan suscripciones
        if not subs:
            users.pop(email)
            modified = True
        else:
            info["suscripciones"] = subs

    if modified:
        save_users(users)

# ───── Lanzar scheduler ───────────────────────────────────────────
scheduler = BackgroundScheduler()

# 1️⃣ tarea principal: revisar suscripciones cada minuto
scheduler.add_job(check_subscriptions, trigger="interval", minutes=1)

# 2️⃣ AUTO-PING cada 5 min (mantiene Render despierto)
#     - Render define RENDER_EXTERNAL_URL con tu URL pública
#     - Si prefieres forzar otra, crea la env-var SELF_URL_MANUAL
SELF_URL = (
    os.environ.get("SELF_URL_MANUAL") or      # prioridad manual
    os.environ.get("RENDER_EXTERNAL_URL")     # valor automático de Render
)

if SELF_URL:
    SELF_URL = SELF_URL.rstrip("/")

    def self_ping():
        try:
            # usamos la ruta /ping que ya existe en tu app
            requests.get(f"{SELF_URL}/ping", timeout=10)
            log.debug(f"✅ self-ping OK → {SELF_URL}/ping")
        except Exception as e:
            log.warning(f"self-ping failed: {e}")

    # registramos la tarea cada 5 minutos
    scheduler.add_job(self_ping, trigger="interval", minutes=5)
else:
    log.info("No se encontró SELF_URL → auto-ping desactivado")

# ¡Iniciamos el scheduler!
scheduler.start()

# ───── ENDPOINTS ────────────────────────────────────────────────────
@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200


@app.route("/revisar", methods=["GET"])
def revisar():
    check_subscriptions()
    return jsonify({"status": "ok"}), 200


@app.route("/agregar-suscripcion", methods=["POST"])
def agregar_suscripción():
    d = request.get_json(silent=True) or {}
    email    = d.get("email", "").strip()
    plan     = d.get("plan")
    nombre   = d.get("nombre", "")
    apellido = d.get("apellido", "")
    telefono = d.get("telefono", "")

    if not email or plan not in PLANS:
        return jsonify({"status": "error", "msg": "datos inválidos"}), 400

    users = load_users()
    now   = datetime.utcnow()
    info  = users.get(email, {"suscripciones": {}})

    lang  = info.get("lang", "ES")
    cid   = info.get("chat_id")
    subs  = info["suscripciones"]
    stype = get_sub_type(plan)

    # ───── calcular nueva expiración (acumula si aún está activa) ─────
    base = now
    if stype in subs:
        try:
            exp_old = datetime.fromisoformat(subs[stype]["expira"])
            if exp_old > now:
                base = exp_old
        except ValueError:
            pass
    exp_new = base + timedelta(minutes=PLANS[plan]["duration_min"])

    subs[stype] = {
        "plan":        plan,
        "ingreso":     subs[stype]["ingreso"] if stype in subs else now.isoformat(),
        "expira":      exp_new.isoformat(),
        "avisado":     False,
        "invite_link": subs.get(stype, {}).get("invite_link")      # puede ser None
    }

    info.update({
        "nombre": nombre,
        "apellido": apellido,
        "telefono": telefono,
        "chat_id": cid,
        "lang": lang,
        "suscripciones": subs,
        "pending_sub": stype          # usado luego en /start
    })
    users[email] = info

    # ─────────────────────── PATCH ① ───────────────────────
    # Si ya conocemos chat_id + idioma creamos el enlace inmediato
    if cid and lang and stype:
        group_id = PLANS[plan][f"group_id_{lang.lower()}"]
        link = enlace_unico(group_id)

        if link:
            subs[stype]["invite_link"] = link

            # imagen según tipo
            img_url = (FIRE_IMAGE_URL  if stype == "Fire"  else
                       ELITE_IMAGE_URL if stype == "Élite" else
                       DELTA_IMAGE_URL)

            caption = (
                "🏆 Pulsa aquí👇 para unirte al nuevo grupo VIP o renovar tu acceso."
                if lang == "ES" else
                "🏆 Tap here👇 to join the new VIP group or renew your access."
            )
            btn = {"text": "🔗 Acceder / Join", "url": link}

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                json={
                    "chat_id": cid,
                    "photo":   img_url,
                    "caption": caption,
                    "reply_markup": {"inline_keyboard": [[btn]]}
                },
                timeout=10
            )
        else:
            # Fallback: no se pudo crear el link → avisamos al usuario
            warn = ("⚠️ No pude generar tu enlace VIP. Avísanos o inténtalo más tarde."
                    if lang == "ES" else
                    "⚠️ I couldn't generate your VIP link. Please contact support or try again later.")
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": cid, "text": warn},
                timeout=10
            )
    # ─────────────── fin PATCH ① ───────────────

    save_users(users)

    return jsonify({
        "status": "ok",
        "sub_type": stype,
        "expira":   exp_new.isoformat()
    }), 200

    return jsonify({"status": "ok", "sub_type": stype, "expira": exp_new.isoformat()}), 200


# ───── /usuarios-activos (igual que antes) ──────────────────────────
@app.route("/usuarios-activos")
def usuarios_activos():
    users = load_users()
    now   = datetime.utcnow()
    rows  = []
    for email, info in users.items():
        lang = info.get("lang", "ES")
        for stype, sub in info["suscripciones"].items():
            plan    = sub["plan"]
            group   = PLANS[plan][f"group_id_{lang.lower()}"]
            ingreso = sub["ingreso"]
            expira  = sub["expira"]
            try:
                mins = (datetime.fromisoformat(expira) - now).total_seconds()/60
                restante = f"{mins:.1f} min"
            except ValueError:
                restante = "—"
            rows.append((info.get("chat_id"), email, stype, plan, lang,
                         group, ingreso, expira, restante))
    rows.sort(key=lambda r: float(r[8].split()[0]) if "min" in r[8] else 999)

    return render_template_string("""
    <html><head><style>
      body{font-family:sans-serif;padding:20px}
      table{border-collapse:collapse;width:100%}
      th,td{border:1px solid #ccc;padding:8px;text-align:center}
      th{background:#f4f4f4}
    </style></head><body>
      <h2>Usuarios activos</h2>
      <table>
        <tr>
          <th>Chat ID</th><th>Email</th><th>Tipo</th><th>Plan</th><th>Idioma</th>
          <th>Grupo</th><th>Ingreso</th><th>Expira</th><th>Restante</th>
        </tr>
        {% for row in rows %}
        <tr>{% for col in row %}<td>{{col}}</td>{% endfor %}</tr>
        {% endfor %}
      </table>
    </body></html>
    """, rows=rows)


@app.route("/telegram-webhook", methods=["GET", "POST"])
def telegram_webhook():
    if request.method == "GET":
        return "OK", 200
    up = request.get_json(force=True)

    # Bienvenida en grupos
    if "message" in up and up["message"].get("new_chat_members"):
        chat_id = up["message"]["chat"]["id"]
        for new_member in up["message"]["new_chat_members"]:
            if new_member.get("is_bot"): continue
            username = new_member.get("first_name", "")
            plan_key = None
            lang = "ES"
            for key, data in PLANS.items():
                if data["group_id_es"] == str(chat_id):
                    plan_key = key; lang = "ES"; break
                if data["group_id_en"] == str(chat_id):
                    plan_key = key; lang = "EN"; break
            stype = get_sub_type(plan_key) if plan_key else ""
            stype_label = TYPE_LABELS.get(stype, stype)
            if lang == "ES":
                txt = f"""👋 ¡Bienvenido al plan {stype_label}, {username}! ¡Bienvenido al Grupo VIP de Crypto Signal Bot!

📈 Señales de trading en tiempo real | Máxima precisión | Resultados comprobados

🔹 Accede a señales de alta precisión para BTC, ETH, XRP, BNB y ADA  
🔹 Estrategias para scalping, intradía y swing trading  
🔹 Señales generadas 24/7 según la volatilidad del mercado  

📂 Grupo VIP organizado por temas independientes:  
🔄 Renovar Suscripción  
🏆 Análisis de Bitcoin  
🔹 BTC/USDT  
🔹 XRP/USDT  
🔹 BNB/USDT  
🔹 ETH/USDT  
🔹 ADA/USDT  

Cada tema funciona como un canal independiente con su propio botón de acceso a la señal.  
A medida que agreguemos nuevas criptomonedas, se irán generando nuevos temas automáticamente para ofrecer acceso rápido y organizado a cada señal.  

🔗 Accede con un solo clic a las señales y gráficos en vivo en nuestra web  
🚀 ¡Prepárate para impulsar tu trading con las mejores oportunidades!"""
            else:
                txt = f"""👋 Welcome to the {stype_label} Plan, {username}! Welcome to the Crypto Signal Bot VIP Group!

📈 Real-Time Trading | Maximum Accuracy | Proven Results

🔹 Access high-precision signals for BTC, ETH, XRP, BNB, and ADA  
🔹 Strategies for scalping, intraday, and swing trading  
🔹 Signals generated 24/7 based on market volatility  

📂 VIP group organized by separate topics:  
🔄 Renew Subscription  
🏆 Bitcoin Analysis  
🔹 BTC/USDT  
🔹 XRP/USDT  
🔹 BNB/USDT  
🔹 ETH/USDT  
🔹 ADA/USDT  

Each topic acts like an independent channel with its own signal-access button.  
As we add new cryptocurrencies, new topics will be generated automatically to provide quick, organized access to each signal.  

🔗 One-click access to live signals and charts on our website  
🚀 Get ready to boost your trading with the best opportunities!"""
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": txt}, timeout=10
            )
        return jsonify({}), 200

    # Manejo de mensajes
    if "message" in up:
        msg  = up["message"]
        text = msg.get("text", "").strip()
        cid  = msg.get("chat", {}).get("id")

        # 1) Deep-link sin token: iniciar flujo SendPulse
        if text == "/start":
            kb = {"inline_keyboard":[[
                {"text":"🌐 Idioma/Language","url":"https://t.me/CriptoSignalBotGestion_bot?start=6848494ba35fe4e8f30495ea"}
            ]]}
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": cid, "text":"🇪🇸 Español\n¡Bienvenido! Pulsa el botón para Selecciona tu idioma y comenzar con nuestras señales VIP.\n\n🇺🇸 English\nWelcome! Click the button to select your language and get started with our VIP signals.", "reply_markup": kb},
                timeout=10
            )
            return jsonify({}), 200

        # 2) Deep-link misdatos
        if text == "/start misdatos":
            kb = {"inline_keyboard":[
                [{"text":"🇪🇸 Español","callback_data":"misdatos_lang|ES"}],
                [{"text":"🇺🇸 English","callback_data":"misdatos_lang|EN"}]
            ]}
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": cid,
                    "text": """👤 𝐂𝐮𝐞𝐧𝐭𝐚 | 𝐀𝐜𝐜𝐨𝐮𝐧𝐭

🇪🇸 Español
En tu cuenta podrás ver todas tus suscripciones. Desde esta sección podrás consultar el estado de cada una, el tiempo de suscripción empleado, el tiempo restante y la fecha de vencimiento, así como renovarlas.

🇺🇸 English
In your account, you can see all your subscriptions. From this section, you can check the status of each one, the subscription time used, the time remaining, and the expiration date, as well as renew them.

Selecciona tu idioma para continuar.
Select your language to continue.""",
                    "reply_markup": kb
                },
                timeout=10
            )
            return jsonify({}), 200

        # 3) /start con token de registro (original)
        if text.startswith("/start ") and cid:
            token = text.split(maxsplit=1)[1]
            if len(token) % 4:
                token += "=" * (4 - len(token) % 4)
            try:
                email = base64.urlsafe_b64decode(token.encode()).decode()
            except:
                return jsonify({}), 200

            users = load_users()
            info  = users.get(email)
            if not info:
                return jsonify({}), 200

            # Guardar chat_id
            info["chat_id"] = cid
            users[email] = info
            save_users(users)

            kb = {"inline_keyboard":[[
                {"text":"🇪🇸 Español","callback_data":f"lang|ES|{email}"},
                {"text":"🇺🇸 English","callback_data":f"lang|EN|{email}"}
            ]]}
            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": cid,
                    "text": """📊 𝐒𝐞ñ𝐚𝐥𝐞𝐬 𝐕𝐈𝐏 | 𝐕𝐈𝐏 𝐒𝐢𝐠𝐧𝐚𝐥𝐬

🇪🇸 Español
𝐈𝐌𝐏𝐎𝐑𝐓𝐀𝐍𝐓𝐄: Al seleccionar tu idioma, generarás el acceso para unirte al grupo privado y comenzar a recibir las señales en tiempo real.

En el menú de este bot podrás ver tu cuenta y tus suscripciones, así como renovar tu suscripción y tu fecha de corte.

🇺🇸 English
𝐈𝐌𝐏𝐎𝐑𝐓𝐀𝐍𝐓: By selecting your language, you will generate access to join the private group and start receiving real-time signals.

In this bot’s menu you can view your account and your subscriptions, as well as renew your subscription and its expiration date.

Selecciona tu idioma para continuar.
Select your language to continue.""",
                    "reply_markup": kb
                },
                timeout=10
            ).json()

            mid = resp.get("result", {}).get("message_id")
            if mid:
                info.setdefault("messages", []).append(mid)
                users[email] = info
                save_users(users)

            return jsonify({}), 200

        # 4) /misdatos comando manual (original)
        if text == "/misdatos" and cid:
            kb = {"inline_keyboard":[
                [{"text":"🇪🇸 Español","callback_data":"misdatos_lang|ES"}],
                [{"text":"🇺🇸 English","callback_data":"misdatos_lang|EN"}]
            ]}
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": cid,
                    "text": """👤 𝐂𝐮𝐞𝐧𝐭𝐚 | 𝐀𝐜𝐜𝐨𝐮𝐧𝐭

🇪🇸 Español
En tu cuenta podrás ver todas tus suscripciones. Desde esta sección podrás consultar el estado de cada una, el tiempo de suscripción empleado, el tiempo restante y la fecha de vencimiento, así como renovarlas.

🇺🇸 English
In your account, you can see all your subscriptions. From this section, you can check the status of each one, the subscription time used, the time remaining, and the expiration date, as well as renew them.

Selecciona tu idioma para continuar.
Select your language to continue.""",
                    "reply_markup": kb
                },
                timeout=10
            )
            return jsonify({}), 200
        # 5) Soporte para texto libre (no comando), ignorar 🎁 VIP Gratis y 🎁 VIP Free
        if text and not text.startswith("/") and text not in ["🎁 VIP Gratis", "🎁 VIP Free"]:
            kb = {"inline_keyboard":[[
                {"text":"🇪🇸 Español","url":"https://t.me/CriptoSignalBotGestion_bot?start=68519f3993f15cf1aa079c62"},
                {"text":"🇺🇸 English","url":"https://t.me/CriptoSignalBotGestion_bot?start=68519fa69049c36b2a0e9485"}
            ]]}
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": cid,
                    "text": "\nBot automático. Para asesoría, elige un idioma.\n\nAutomated bot. Choose a language for assistance.",
                    "reply_markup": kb
                },
                timeout=10
            )
            return jsonify({}), 200

    # Callback queries (original)
    if "callback_query" in up:
        cq   = up["callback_query"]
        data = cq.get("data", "")
        cid  = cq["from"]["id"]
        users = load_users()

        # /start language selection  ─────────────────────────────────────────
        if data.startswith("lang|"):
            _, lang, email = data.split("|", 2)
            info = users.get(email)

            # seguridad
            if not info or info.get("chat_id") != cid:
                return jsonify({}), 200

            info["lang"] = lang          # actualizamos idioma
            subs = info.get("suscripciones", {})

            # 1️⃣ preferimos la suscripción marcada como pendiente
            stype = info.pop("pending_sub", None)

            # 2️⃣ si no hay pending → buscamos la que aún NO tenga invite_link
            if not stype:
                stype = next((s for s, v in subs.items() if not v.get("invite_link")), None)

            # 3️⃣ si todas tenían enlace, escogemos la MÁS RECIENTE (ingreso máximo)
            if not stype and subs:
                stype = max(subs, key=lambda s: subs[s]["ingreso"])

            # 4️⃣ si sigue sin haber nada, informamos al usuario
            if not stype:
                txt = ("No encontramos ninguna suscripción activa vinculada a tu cuenta."
                       if lang == "ES"
                       else "No active subscription was found for your account.")
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": cid, "text": txt},
                    timeout=10
                )
                return jsonify({}), 200

            # generamos enlace para la suscripción seleccionada
            sub       = subs[stype]
            plan_key  = sub["plan"]
            grp       = PLANS[plan_key][f"group_id_{lang.lower()}"]
            link      = enlace_unico(grp)
            sub["invite_link"] = link

            users[email] = info
            save_users(users)

            img_url = (FIRE_IMAGE_URL  if get_sub_type(plan_key) == "Fire"
                       else ELITE_IMAGE_URL if get_sub_type(plan_key) == "Élite"
                       else DELTA_IMAGE_URL)
            caption = (
                "🚀 ¡Bienvenido! Pulsa aquí👇 para acceder a señales VIP y mejorar tu trading 🔔\n"
                "Si ya eres miembro, pulsa igual para 🔄 renovar tu acceso."
                if lang == "ES" else
                "🚀 Welcome! Tap here👇 to access VIP signals and boost your trading 🔔\n"
                "If you’re already a member, tap again to 🔄 renew your access."
            )
            btn = [{"text": "🏆 Unirme o Renovar / Join or Renew", "url": link}]

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                json={
                    "chat_id": cid,
                    "photo":   img_url,
                    "caption": caption,
                    "reply_markup": {"inline_keyboard": [btn]}
                },
                timeout=10
            )
            return jsonify({}), 200

        # misdatos idioma
        if data.startswith("misdatos_lang|"):
            _, lang = data.split("|", 1)
            email = None; info = None
            for em, inf in users.items():
                if inf.get("chat_id") == cid:
                    email, info = em, inf
                    break

            if not info:
                rep = "Usted no posee ninguna suscripción." if lang=="ES" else "You have no active subscriptions."
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": cid, "text": rep},
                    timeout=10
                )
                return jsonify({}), 200

            n = info.get("nombre", "")
            a = info.get("apellido", "")
            t = info.get("telefono", "")
            subs = info.get("suscripciones", {})

            if not subs:
                if lang == "ES":
                    rep = (
                        f"Nombre: {n} {a}\n"
                        f"Correo: {email}\n"
                        f"Teléfono: {t}\n\n"
                        f"Usted no posee ninguna suscripción."
                    )
                else:
                    rep = (
                        f"Name: {n} {a}\n"
                        f"Email: {email}\n"
                        f"Phone: {t}\n\n"
                        f"You have no active subscriptions."
                    )
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": cid, "text": rep},
                    timeout=10
                )
                return jsonify({}), 200

            if lang == "ES":
                rep = f"Hola {n} {a},\n\n*Tus suscripciones activas:*\n"
            else:
                rep = f"Hello {n} {a},\n\n*Your active subscriptions:*\n"
            keyboard = []
            now = datetime.utcnow()
            for stype, sub in subs.items():
                plan_key = sub.get("plan")
                ing = datetime.fromisoformat(sub["ingreso"]).strftime("%Y-%m-%d %H:%M")
                exp_dt = datetime.fromisoformat(sub["expira"])
                exp = exp_dt.strftime("%Y-%m-%d %H:%M")
                delta = exp_dt - now
                total_seconds = int(delta.total_seconds())
                months = total_seconds // (30*24*3600)
                rem_secs = total_seconds - months*30*24*3600
                days = rem_secs // (24*3600)
                rem_secs -= days*24*3600
                hours = rem_secs // 3600
                rem_secs -= hours*3600
                minutes = rem_secs // 60
                plan_name = LABELS.get(plan_key, plan_key)
                label = TYPE_LABELS.get(stype, stype)
                if lang == "ES":
                    rep += (
                        f"\n• {label}: {plan_name}\n"
                        f"  - Ingreso: {ing}\n"
                        f"  - Expira: {exp}\n"
                        f"  - Restante: {months} meses, {days} días, {hours} horas, {minutes} minutos\n"
                    )
                    keyboard.append([{"text":f"🔄 Renovar {label}","callback_data":f"renovar_menu|{stype}"}])
                else:
                    rep += (
                        f"\n• {label}: {plan_name}\n"
                        f"  - Start: {ing}\n"
                        f"  - Expires: {exp}\n"
                        f"  - Remaining: {months} months, {days} days, {hours} hours, {minutes} minutes\n"
                    )
                    keyboard.append([{"text":f"🔄 Renew {label}","callback_data":f"renovar_menu|{stype}"}])

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": cid,
                    "text": rep,
                    "parse_mode": "Markdown",
                    "reply_markup": {"inline_keyboard": keyboard}
                },
                timeout=10
            )
            return jsonify({}), 200

        # Sub-menú renovar
        if "callback_query" in up and data.startswith("renovar_menu|"):
            _, stype = data.split("|", 1)
            lang = next((inf.get("lang", "ES") for inf in users.values() if inf.get("chat_id") == cid), "ES")

            if stype == "Fire":
                url_mes   = "https://cryptosignalbot.com/?renewal=1"
                url_anual = "https://cryptosignalbot.com/?anual=1"
            elif stype == "Élite":
                url_mes   = "https://cryptosignalbot.com/?renewal_elite=1"
                url_anual = "https://cryptosignalbot.com/?annual_elite=1"
            elif stype == "Delta":
                url_mes   = "https://cryptosignalbot.com/?renewal_delta=1"
                url_anual = "https://cryptosignalbot.com/?annual_delta=1"
            else:
                url_mes = url_anual = RENEWAL_URL

            if stype == "Fire":
                if lang == "ES":
                    text = "Selecciona periodo de renovación para Fire:"
                    btn1 = {"text": "🔄 Renovar Mes $17", "url": url_mes}
                    btn2 = {"text": "🔄 Renovar Año 204$ (–30%) = 142$", "url": url_anual}
                else:
                    text = "Select renewal period for Fire:"
                    btn1 = {"text": "🔄 Renew Month $17", "url": url_mes}
                    btn2 = {"text": "🔄 Renew Year 204$ (–30%) = 142$", "url": url_anual}
            elif stype == "Élite":
                if lang == "ES":
                    text = "Selecciona periodo de renovación para Élite:"
                    btn1 = {"text": "🔄 Renovar 1 Mes $25", "url": url_mes}
                    btn2 = {"text": "🔄 Renovar Año 300$ (–30%) = 210$", "url": url_anual}
                else:
                    text = "Select renewal period for Élite:"
                    btn1 = {"text": "🔄 Renew Month $25", "url": url_mes}
                    btn2 = {"text": "🔄 Renew Year 300$ (–30%) = 210$", "url": url_anual}
            elif stype == "Delta":
                if lang == "ES":
                    text = "Selecciona periodo de renovación para Delta:"
                    btn1 = {"text": "🔄 Renovar 1 Mes $31", "url": url_mes}
                    btn2 = {"text": "🔄 Renovar Año 372$ (–30%) = 260$", "url": url_anual}
                else:
                    text = "Select renewal period for Delta:"
                    btn1 = {"text": "🔄 Renew Month $31", "url": url_mes}
                    btn2 = {"text": "🔄 Renew Year 372$ (–30%) = 260$", "url": url_anual}
            else:
                if lang == "ES":
                    text = f"Selecciona periodo de renovación para {stype}:"
                    btn1 = {"text": "🔄 Renovar suscripción", "url": url_mes}
                    btn2 = {"text": "🔄 Renovar suscripción", "url": url_anual}
                else:
                    text = f"Select renewal period for {stype}:"
                    btn1 = {"text": "🔄 Renew subscription", "url": url_mes}
                    btn2 = {"text": "🔄 Renew subscription", "url": url_anual}

            kb = {"inline_keyboard": [[btn1], [btn2]]}
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": cid, "text": text, "reply_markup": kb},
                timeout=10
            )
            return jsonify({}), 200

    return jsonify({}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(__import__('os').environ.get("PORT", 5000)))
