import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient

# TOKEN ACTUALIZADO
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

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("📋 Lista General", "🚨 Alertas Críticas")
    bot.send_message(message.chat.id, "👨‍✈️ **Control de Vuelos Activo**\nSeleccione una opción:", reply_markup=m, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def cmd_lista(message):
    doc = coleccion.find_one({"id": "data_principal"})
    personal = doc["datos"]
    res = "📊 **REPORTE DE ESTADO**\n"
    for cat, gente in personal.items():
        res += f"\n┏━━ **{cat}**\n"
        for i, (n, f) in enumerate(gente.items(), 1):
            e, d = calcular_vencimiento(f)
            res += f"┃ {i}. {e} **{n}**: {d}d\n"
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🚨 Alertas Críticas")
def cmd_alertas(message):
    doc = coleccion.find_one({"id": "data_principal"})
    personal = doc["datos"]
    res = "🚨 **PERSONAL EN ALERTA (45+ días)**\n"
    hay = False
    for cat, gente in personal.items():
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            if d >= 45:
                res += f"⚠️ {n} ({cat}): {d} días\n"
                hay = True
    bot.send_message(message.chat.id, res if hay else "✅ No hay alertas críticas.", parse_mode="Markdown")

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
                bot.reply_to(message, f"✅ **{nombre}** actualizado.")
                return
        bot.reply_to(message, "❌ Nombre no encontrado.")
    except:
        bot.reply_to(message, "Usa: `/vuelo NOMBRE`")

print("INICIANDO BOT...")
bot.infinity_polling()

