# -*- coding: utf-8 -*-
"""
main.py – Crypto Signal Bot 🔥 gestión avanzada multi-suscripciones
– Mantiene usuarios_activos.json con varias suscripciones por usuario
– Avisos −5 min y expulsión a 0 min (7/10/15 min según plan), sin ban
– Mensaje a −5 min con botón “🔄 Renovar suscripción” indicando el tipo y desplegando sub-menú de renovación
– Mensaje a 0 min con botón “🔄 Renovar suscripción” indicando el tipo y desplegando sub-menú de renovación
– Envía imagen de bienvenida según tipo tras /start + enlace único
– Envía mensaje de bienvenida en el grupo indicando el plan
– Comando /misdatos muestra menú de idioma, luego datos y opción de renovar con sub-menú
– Tabla HTML en /usuarios-activos con Chat ID, Email, Tipo, Plan, Idioma, Grupo, Ingreso, Expira, Restante
– Comprueba cada minuto con APScheduler
"""
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import json, pathlib, logging, requests, base64
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ─── Health-check para mantener la app despierta ───────────────────────────────────
@app.route('/ping', methods=['GET'])
def ping():
    return 'pong', 200

# ───────── CONFIGURACIÓN ──────────
BOT_TOKEN         = "7457058289:AAF-VN0UWiduteBV79VdKxgIT2yeg9wa-LQ"
FIRE_IMAGE_URL    = "https://cryptosignalbot.com/wp-content/uploads/2025/02/Fire-Scalping-Senales-de-Trading-para-Ganar-Mas-en-Cripto-3.png"
ELITE_IMAGE_URL   = "https://cryptosignalbot.com/wp-content/uploads/2025/02/ELITE-Scalping-Intradia-Senales-en-Tiempo-Real.png"
DELTA_IMAGE_URL   = "https://cryptosignalbot.com/wp-content/uploads/2025/03/delta-swing-trading-crypto-signal.png"
RENEWAL_URL       = "https://cryptosignalbot.com/mi-cuenta"
USERS_FILE        = "usuarios_activos.json"
LOG_FILE          = "csb_events.log"

# Planes y sus tiempos
PLANS = {
    # FIRE
    "GRATIS_ES":        {"duration_min":  7   * 24 * 60,   "group_id_es": "-1002470074373", "group_id_en": "-1002371800315"},
    "MES_ES":           {"duration_min": 30   * 24 * 60,   "group_id_es": "-1002470074373", "group_id_en": "-1002371800315"},
    "ANIO_ES":          {"duration_min":365   * 24 * 60,   "group_id_es": "-1002470074373", "group_id_en": "-1002371800315"},

    # ÉLITE
    "GRATIS_ES_ELITE":  {"duration_min": 15   * 24 * 60,   "group_id_es": "-1002437381292", "group_id_en": "-1002432864193"},
    "MES_ES_ELITE":     {"duration_min": 30   * 24 * 60,   "group_id_es": "-1002437381292", "group_id_en": "-1002432864193"},
    "ANIO_ES_ELITE":    {"duration_min":365   * 24 * 60,   "group_id_es": "-1002437381292", "group_id_en": "-1002432864193"},

    # DELTA
    "GRATIS_ES_DELTA":  {"duration_min": 30   * 24 * 60,   "group_id_es": "-1002299713092", "group_id_en": "-1002428632182"},
    "MES_ES_DELTA":     {"duration_min": 30   * 24 * 60,   "group_id_es": "-1002299713092", "group_id_en": "-1002428632182"},
    "ANIO_ES_DELTA":    {"duration_min":365   * 24 * 60,   "group_id_es": "-1002299713092", "group_id_en": "-1002428632182"},
}

# Etiquetas legibles
LABELS = {
    "GRATIS_ES":"𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐚𝐏𝐢𝐧𝐠 𝐠𝐫𝐚𝐭𝐢𝐬 𝟕 𝐝í𝐚𝐬",
    "MES_ES":"𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐚𝐏𝐢𝐧𝐠 𝐦𝐞𝐧𝐬𝐮𝐚𝐥",
    "ANIO_ES":"𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐚𝐏𝐢𝐧𝐠 𝐚𝐧𝐮𝐚𝐥",
    "GRATIS_ES_ELITE":"𝐄𝐋𝐈𝐓𝐄 𝐒𝐜𝐚𝐥𝐚𝐏𝐢𝐧𝐠 𝐏𝐑𝐎 𝐆𝐫𝐚𝐭𝐢𝐬 𝟏𝟓 𝐝í𝐚𝐬",
    "MES_ES_ELITE":"𝐄𝐋𝐈𝐓𝐄 𝐒𝐜𝐚𝐥𝐚𝐏𝐢𝐧𝐠 𝐏𝐑𝐎 𝐦𝐞𝐧𝐬𝐮𝐚𝐥",
    "ANIO_ES_ELITE":"𝐄𝐋𝐈𝐓𝐄 𝐒𝐜𝐚𝐥𝐚𝐏𝐢𝐧𝐠 𝐏𝐑𝐎 𝐚𝐧𝐮𝐚𝐥",
    "GRATIS_ES_DELTA":"𝐃𝐄𝐋𝐓𝐀 𝐒𝐰𝐢𝐧𝐠 𝐆𝐫𝐚𝐭𝐢𝐬 𝟑𝟎 𝐝í𝐚𝐬",
    "MES_ES_DELTA":"𝐃𝐄𝐋𝐓𝐀 𝐒𝐰𝐢𝐧𝐠 𝐦𝐞𝐧𝐬𝐮𝐚𝐥",
    "ANIO_ES_DELTA":"𝐃𝐄𝐋𝐓𝐀 𝐒𝐰𝐢𝐧𝐠 𝐚𝐧𝐮𝐚𝐥",
}

# Etiquetas base de planes (sin duración)
TYPE_LABELS = {
    "Fire":  "🔥 𝐅𝐢𝐫𝐞 𝐒𝐜𝐚𝐥𝐚𝐏𝐢𝐧𝐠",
    "Élite": "💎 𝐄𝐋𝐈𝐓𝐄 𝐒𝐜𝐚𝐥𝐚𝐏𝐢𝐧𝐠 𝐏𝐑𝐎",
    "Delta": "🪙 𝐃𝐄𝐋𝐓𝐀 𝐒𝐰𝐢𝐧𝐠"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
log = logging.getLogger("CSB")


def load_users():
    p = pathlib.Path(USERS_FILE)
    return json.loads(p.read_text()) if p.exists() else {}


def save_users(u):
    pathlib.Path(USERS_FILE).write_text(json.dumps(u, indent=2))


def get_sub_type(plan_key):
    if plan_key.endswith('_ELITE'): return 'Élite'
    if plan_key.endswith('_DELTA'): return 'Delta'
    return 'Fire'


def enlace_unico(group_id):
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


def check_subscriptions():
    users = load_users()
    now = datetime.utcnow()
    modified = False

    for email, info in list(users.items()):
        cid  = info.get("chat_id")
        lang = info.get("lang", "ES")
        subs = info.get("suscripciones", {})

        for stype, sub in list(subs.items()):
            try:
                exp  = datetime.fromisoformat(sub.get("expira"))
            except:
                continue
            secs = (exp - now).total_seconds()

            # ─── Aviso 5 minutos ─────────────────────────────────────────
            if secs <= 300 and not sub.get("avisado", False):
                if lang == "ES":
                    text = (
                        "⏳ Tu suscripción "
                        f"{TYPE_LABELS.get(stype, stype)} expira en 24 Horas. "
                        "Renueva tu suscripción y mantén el acceso a las señales de trading de Cripto Signal Bot. ¡No pierdas esta oportunidad!"  
                    )
                else:
                    text = (
                        "⏳ Your "
                        f"{TYPE_LABELS.get(stype, stype)} subscription expires in 24 hours. "
                        "Renew your subscription and maintain access to Crypto Signal Bot's trading signals. Don't miss this opportunity!"
                    )
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": cid,
                        "text": text,
                        "reply_markup": {
                            "inline_keyboard": [[
                                {"text":"🔄 Renovar / Renew","callback_data":f"renovar_menu|{stype}"}
                            ]]
                        }
                    },
                    timeout=10
                )
                subs[stype]["avisado"] = True
                modified = True

            # ─── Expiración ───────────────────────────────────────────────
            if secs <= 0:
                invite_link = sub.get("invite_link")
                plan_key    = sub.get("plan")
                group_id    = PLANS[plan_key][f"group_id_{lang.lower()}"]

                if invite_link:
                    try:
                        requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/revokeChatInviteLink",
                            json={"chat_id": group_id, "invite_link": invite_link},
                            timeout=10
                        )
                    except Exception as e:
                        log.error(f"Error revoking invite link: {e}")

                if lang == "ES":
                    text = f"❌ Tu suscripción {TYPE_LABELS.get(stype, stype)} ha expirado."
                else:
                    text = f"❌ Your subscription {TYPE_LABELS.get(stype, stype)} has expired."

                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": cid,
                        "text": text,
                        "reply_markup": {
                            "inline_keyboard": [[
                                {"text":"🔄 Renovar / Renew","callback_data":f"renovar_menu|{stype}"}
                            ]]
                        }
                    },
                    timeout=10
                )
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/kickChatMember",
                    json={"chat_id": group_id, "user_id": cid},
                    timeout=10
                )
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/unbanChatMember",
                    json={"chat_id": group_id, "user_id": cid},
                    timeout=10
                )

                subs.pop(stype)
                modified = True

        if not subs:
            users.pop(email)
            modified = True
        else:
            users[email]["suscripciones"] = subs

    if modified:
        save_users(users)


scheduler = BackgroundScheduler()
scheduler.add_job(func=check_subscriptions, trigger='interval', minutes=1)
scheduler.start()


@app.route("/revisar", methods=["GET"])
def revisar():
    check_subscriptions()
    return jsonify({"status": "ok"}), 200


@app.route("/agregar-suscripcion", methods=["POST"])
def agregar_suscripción():
    d = request.get_json(silent=True) or {}
    email    = d.get("email")
    plan     = d.get("plan")
    nombre   = d.get("nombre", "")
    apellido = d.get("apellido", "")
    telefono = d.get("telefono", "")
    if not email or plan not in PLANS:
        return jsonify({"status": "error", "msg": "datos inválidos"}), 400

    users = load_users()
    now   = datetime.utcnow()
    info  = users.get(email, {})
    lang  = info.get("lang", "ES")
    subs  = info.get("suscripciones", {})

    stype = get_sub_type(plan)
    old   = subs.get(stype)
    if old and old.get("expira"):
        try:
            exp_old = datetime.fromisoformat(old["expira"])
        except:
            exp_old = now
        base = exp_old if exp_old > now else now
        ingreso = old.get("ingreso", now.isoformat())
    else:
        base = now
        ingreso = now.isoformat()
    exp_new = base + timedelta(minutes=PLANS[plan]["duration_min"])

    subs[stype] = {
        "plan":      plan,
        "ingreso":   ingreso,
        "expira":    exp_new.isoformat(),
        "avisado":   False,
        "invite_link": info.get("suscripciones", {}).get(stype, {}).get("invite_link")
    }
    info.update({
        "nombre":        nombre,
        "apellido":      apellido,
        "telefono":      telefono,
        "chat_id":       info.get("chat_id"),
        "lang":          lang,
        "suscripciones": subs,
        "pending_sub":   stype
    })
    users[email] = info
    save_users(users)

    return jsonify({"status": "ok", "sub_type": stype, "expira": exp_new.isoformat()}), 200


@app.route("/usuarios-activos")
def usuarios_activos():
    users = load_users()
    now   = datetime.utcnow()
    rows  = []
    for email, info in users.items():
        lang = info.get("lang", "ES")
        for stype, sub in info.get("suscripciones", {}).items():
            plan    = sub.get("plan")
            group   = PLANS[plan][f"group_id_{lang.lower()}"]
            ingreso = sub.get("ingreso", "—")
            expira  = sub.get("expira",  "—")
            try:
                restante = f"{(datetime.fromisoformat(expira) - now).total_seconds()/60:.1f} min"
            except:
                restante = "—"
            rows.append((info.get("chat_id"), email, stype, plan, lang, group, ingreso, expira, restante))
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
        {% for cid,email,stype,plan,lang,group,ing,exp,rem in rows %}
        <tr>
          <td>{{cid}}</td><td>{{email}}</td><td>{{stype}}</td><td>{{plan}}</td><td>{{lang}}</td>
          <td>{{group}}</td><td>{{ing}}</td><td>{{exp}}</td><td>{{rem}}</td>
        </tr>
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
                json={"chat_id": cid, "text":"🇪🇸 Español\n¡Bienvenido! Pulsa el botón para seleccionar tu idioma y comenzar con nuestras señales VIP.\n\n🇺🇸 English\nWelcome! Click the button to select your language and get started with our VIP signals.", "reply_markup": kb},
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

        # 3) /start con token de registro
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

        # 4) /misdatos comando manual
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

        # 5) texto libre
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

    # Callback queries
    if "callback_query" in up:
        cq   = up["callback_query"]
        data = cq.get("data", "")
        cid  = cq["from"]["id"]
        users = load_users()

        if data.startswith("lang|"):
            # /start language selection
            _, lang, email = data.split("|", 2)
            info = users.get(email)
            if not info or info.get("chat_id") != cid:
                return jsonify({}), 200
            info["lang"] = lang
            stype = info.pop("pending_sub", None)
            sub   = info.get("suscripciones", {}).get(stype)
            plan_key = sub.get("plan")
            grp = PLANS[plan_key][f"group_id_{lang.lower()}"]
            link = enlace_unico(grp)
            info["suscripciones"][stype]["invite_link"] = link
            users[email] = info
            save_users(users)

            btn = [{"text":"🏆 Unirme o Renovar / Join or Renew","url":link}]
            caption = (
                "🚀 ¡Bienvenido! Pulsa aquí👇 para acceder a señales VIP y mejorar tu trading 🔔\n"
                "Si ya eres miembro, pulsa igual para 🔄 renovar tu acceso y seguir disfrutando de análisis en tiempo real."
                if lang=="ES"
                else
                "🚀 Welcome! Tap here👇 to access VIP signals and boost your trading 🔔\n"
                "If you’re already a member, tap again to 🔄 renew your access and keep enjoying real-time analysis."
            )
            img_url = FIRE_IMAGE_URL if get_sub_type(plan_key)=="Fire" else ELITE_IMAGE_URL if get_sub_type(plan_key)=="Élite" else DELTA_IMAGE_URL
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                json={"chat_id": cid, "photo": img_url, "caption": caption, "reply_markup":{"inline_keyboard":[btn]}},
                timeout=10
            )
            return jsonify({}), 200

        if data.startswith("misdatos_lang|"):
            # misdatos idioma
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

        if data.startswith("renovar_menu|"):
            # Sub-menú renovar
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

    # ─── Siempre devolvemos algo al final para evitar None ────────────────────────────
    return jsonify({}), 200


# ─── Endpoint para eliminar suscripción desde WordPress ─────────────────────────────
@app.route("/remove-subscription", methods=["POST"])
def remove_subscription():
    """
    Recibe JSON { "email": "...", "plan": "MES_ES" } desde WP,
    expulsa al usuario del grupo de Telegram y actualiza usuarios_activos.json.
    """
    data = request.get_json(force=True) or {}
    email = data.get("email")
    plan  = data.get("plan")
    if not email or plan not in PLANS:
        return jsonify({"status": "error", "msg": "datos inválidos"}), 400

    users = load_users()
    info = users.get(email)
    if not info or "suscripciones" not in info:
        return jsonify({"status": "error", "msg": "sin suscripción"}), 404

    # Expulsa del grupo
    stype = get_sub_type(plan)
    sub = info["suscripciones"].pop(stype, None)
    if sub:
        lang     = info.get("lang", "ES").lower()
        group_id = PLANS[plan][f"group_id_{lang}"]
        cid      = info.get("chat_id")
        if cid:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/kickChatMember",
                json={"chat_id": group_id, "user_id": cid}, timeout=10
            )
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/unbanChatMember",
                json={"chat_id": group_id, "user_id": cid}, timeout=10
            )

    # Actualiza JSON
    if not info["suscripciones"]:
        users.pop(email)
    else:
        users[email] = info
    save_users(users)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(__import__('os').environ.get("PORT", 5000)))
