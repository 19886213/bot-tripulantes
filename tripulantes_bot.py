import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient

TOKEN = "8770392349:AAEcYxLOy_42HZu1SOCc3srH1a2qBP8L8rY"
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"

bot = telebot.TeleBot(TOKEN)

# CONEXIÓN SEGURA
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['sistema_vuelos']
    coleccion = db['tripulantes']
    print("✅ Conectado a MongoDB")
except Exception as e:
    print(f"❌ Error Mongo: {e}")

def calcular_vencimiento(f_str):
    try:
        d = (datetime.now() - datetime.strptime(f_str, "%Y-%m-%d")).days
        if d >= 45: return "🔴", d
        if d >= 35: return "🟡", d
        return "🟢", d
    except: return "⚪", 0

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add("📋 Lista General", "🚨 Alertas Críticas", "⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "🚀 **Bot en Línea**\nSi no ves la lista, asegúrate de haber creado el documento en MongoDB.", reply_markup=m, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def cmd_lista(message):
    try:
        doc = coleccion.find_one({"id": "data_principal"})
        if not doc:
            bot.send_message(message.chat.id, "❌ No encontré datos en MongoDB. Verifica el id: 'data_principal'")
            return
        
        personal = doc.get("datos", {})
        res = "📊 **REPORTE ACTUAL**\n"
        for cat, gente in personal.items():
            res += f"\n**{cat}**\n"
            for n, f in gente.items():
                e, d = calcular_vencimiento(f)
                res += f"{e} {n}: {d}d\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"🚨 Error: {e}")

# (Mantenemos las otras funciones igual)
print("INICIANDO...")
bot.infinity_polling()



