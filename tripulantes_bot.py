import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient

TOKEN = "8770392349:AAEcYxLOy_42HZu1SOCc3srH1a2qBP8L8rY"
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client['sistema_vuelos']
coleccion = db['tripulantes']

def calcular_vencimiento(f_str):
    try:
        d = (datetime.now() - datetime.strptime(f_str, "%Y-%m-%d")).days
        if d >= 45: return "🔴", d
        if d >= 35: return "🟡", d
        return "🟢", d
    except: return "⚪", 0

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Lista General", "🚨 Alertas Críticas")
    markup.row("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "👨‍✈️ **SISTEMA CONECTADO**\nPresione un botón para consultar:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def manejar_mensajes(message):
    try:
        # Buscamos el documento en MongoDB
        doc = coleccion.find_one({"id": "data_principal"})
        
        if not doc:
            bot.send_message(message.chat.id, "🚨 **ERROR**: No encontré el documento con id: 'data_principal' en tu MongoDB Atlas.")
            return

        personal = doc.get("datos", {})

        if message.text == "📋 Lista General":
            res = "📊 **REPORTE COMPLETO**\n"
            for cat, gente in personal.items():
                res += f"\n┏━━ **{cat}**\n"
                for n, f in gente.items():
                    e, d = calcular_vencimiento(f)
                    res += f"┃ {e} **{n}**: {d}d\n"
            bot.send_message(message.chat.id, res, parse_mode="Markdown")

        elif message.text == "🚨 Alertas Críticas":
            res = "🔴 **CRÍTICOS (45+ DÍAS)**\n"
            hay = any(calcular_vencimiento(f)[1] >= 45 for cat in personal for f in personal[cat].values())
            if not hay:
                bot.send_message(message.chat.id, "✅ No hay alertas críticas.")
                return
            for cat, gente in personal.items():
                for n, f in gente.items():
                    e, d = calcular_vencimiento(f)
                    if d >= 45: res += f"📍 {n}: {d} días\n"
            bot.send_message(message.chat.id, res, parse_mode="Markdown")

        elif message.text == "⚠️ Próximos a Vencer":
            res = "🟡 **PREVENTIVOS (35-44 DÍAS)**\n"
            hay = False
            for cat, gente in personal.items():
                for n, f in gente.items():
                    e, d = calcular_vencimiento(f)
                    if 35 <= d < 45:
                        res += f"🔸 {n}: {d} días\n"
                        hay = True
            bot.send_message(message.chat.id, res if hay else "✅ No hay personal en amarillo.", parse_mode="Markdown")

        elif message.text == "❓ Ayuda":
            bot.send_message(message.chat.id, "📖 **GUÍA**\nUsa los botones para ver reportes.\nPara resetear a alguien usa: `/vuelo NOMBRE`", parse_mode="Markdown")

    except Exception as e:
        bot.send_message(message.chat.id, f"🚨 **ERROR CRÍTICO**: {str(e)}")

# Mantener igual la función de /vuelo abajo
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
                bot.reply_to(message, f"✅ {nombre} actualizado.")
                return
        bot.reply_to(message, "❌ No encontrado.")
    except: bot.reply_to(message, "Usa: /vuelo NOMBRE")

bot.infinity_polling()
