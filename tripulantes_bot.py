import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient

# 1. CONFIGURACIÓN
TOKEN = "8770392349:AAEcYxLOy_42HZu1SOCc3srH1a2qBP8L8rY"
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"

client = MongoClient(MONGO_URI)
db = client['sistema_vuelos']
coleccion = db['tripulantes']
bot = telebot.TeleBot(TOKEN)

def calcular_vencimiento(f_str):
    d = (datetime.now() - datetime.strptime(f_str, "%Y-%m-%d")).days
    if d >= 45: return "🔴", d
    if d >= 35: return "🟡", d
    return "🟢", d

# --- FUNCIÓN 1: MENÚ PRINCIPAL ---
@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_lista = types.KeyboardButton("📋 Lista General")
    btn_rojo = types.KeyboardButton("🚨 Alertas Críticas")
    btn_amarillo = types.KeyboardButton("⚠️ Próximos a Vencer")
    btn_ayuda = types.KeyboardButton("❓ Ayuda")
    m.add(btn_lista, btn_rojo, btn_amarillo, btn_ayuda)
    bot.send_message(message.chat.id, "👨‍✈️ **Control de Tripulación Activo**\nSeleccione una opción:", reply_markup=m, parse_mode="Markdown")

# --- FUNCIÓN 2: LISTA GENERAL ---
@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def cmd_lista(message):
    doc = coleccion.find_one({"id": "data_principal"})
    personal = doc["datos"]
    res = "📊 **REPORTE COMPLETO**\n"
    for cat, gente in personal.items():
        res += f"\n┏━━ **{cat}**\n"
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            res += f"┃ {e} **{n}**: {d}d\n"
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

# --- FUNCIÓN 3: ALERTAS CRÍTICAS (ROJO) ---
@bot.message_handler(func=lambda msg: msg.text == "🚨 Alertas Críticas")
def cmd_alertas_rojo(message):
    doc = coleccion.find_one({"id": "data_principal"})
    personal = doc["datos"]
    res = "🔴 **ALERTAS CRÍTICAS (45+ DÍAS)**\n"
    hay = False
    for cat, gente in personal.items():
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            if d >= 45:
                res += f"📍 {n} ({cat}): {d} días\n"
                hay = True
    bot.send_message(message.chat.id, res if hay else "✅ No hay alertas críticas.", parse_mode="Markdown")

# --- FUNCIÓN 4: ALERTAS PREVENTIVAS (AMARILLO) ---
@bot.message_handler(func=lambda msg: msg.text == "⚠️ Próximos a Vencer")
def cmd_alertas_amarillo(message):
    doc = coleccion.find_one({"id": "data_principal"})
    personal = doc["datos"]
    res = "🟡 **PRÓXIMOS A VENCER (35-44 DÍAS)**\n"
    hay = False
    for cat, gente in personal.items():
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            if 35 <= d < 45:
                res += f"🔸 {n} ({cat}): {d} días\n"
                hay = True
    bot.send_message(message.chat.id, res if hay else "✅ No hay personal en preventivo.", parse_mode="Markdown")

# --- FUNCIÓN 5: AYUDA ---
@bot.message_handler(func=lambda msg: msg.text == "❓ Ayuda")
def cmd_ayuda(message):
    texto = (
        "❓ **GUÍA DE USO**\n\n"
        "🔴 **Crítico**: 45 días o más.\n"
        "🟡 **Preventivo**: 35 a 44 días.\n"
        "🟢 **Operativo**: Menos de 35 días.\n\n"
        "👉 Para reiniciar a alguien use:\n`/vuelo NOMBRE`"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

# --- FUNCIÓN 6: ACTUALIZAR VUELO ---
@bot.message_handler(commands=['vuelo'])
def cmd_vuelo(message):
    try:
        nombre = message.text.split(maxsplit=1)[1].upper()
        doc = coleccion.find_one({"id": "data_principal"})
        personal = doc["datos"]
        for cat in personal:
            if nombre in personal[cat]:
                personal[cat][nombre] = datetime.now().strftime("%Y-%m-%d")
                coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": personal}})
                bot.reply_to(message, f"✅ **{nombre}** actualizado a 0 días.")
                return
        bot.reply_to(message, "❌ No encontrado.")
    except:
        bot.reply_to(message, "Usa: `/vuelo NOMBRE`")

print("BOT COMPLETO INICIADO...")
bot.infinity_polling()
