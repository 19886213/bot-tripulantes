import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
import time

# --- DATOS ---
TOKEN = "8770392349:AAEcYxLOy_42HZu1SOCc3srH1a2qBP8L8rY"
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"

bot = telebot.TeleBot(TOKEN)

# CONEXIÓN CON TIEMPO DE ESPERA
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['sistema_vuelos']
    coleccion = db['tripulantes']
    client.server_info() # Esto verifica si la conexión es real
    print("✅ Conectado a MongoDB")
except Exception as e:
    print(f"❌ Error de conexión: {e}")

def calcular_vencimiento(f_str):
    try:
        d = (datetime.now() - datetime.strptime(f_str, "%Y-%m-%d")).days
        if d >= 45: return "🔴", d
        if d >= 35: return "🟡", d
        return "🟢", d
    except: return "⚪", 0

@bot.message_handler(commands=['start'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Lista General", "🚨 Alertas Críticas")
    markup.row("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.reply_to(message, "🚀 **BOT REINICIADO**\nPulsa un botón:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def cmd_lista(message):
    try:
        doc = coleccion.find_one({"id": "data_principal"})
        if not doc:
            bot.send_message(message.chat.id, "⚠️ El documento no existe en MongoDB. Crea uno con id: 'data_principal'")
            return
        
        personal = doc.get("datos", {})
        res = "📊 **REPORTE ACTUAL**\n"
        for cat, gente in personal.items():
            res += f"\n┏━━ **{cat}**\n"
            for n, f in gente.items():
                e, d = calcular_vencimiento(f)
                res += f"┃ {e} **{n}**: {d}d\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"🚨 Error: {e}")

# Mantenlo vivo
if __name__ == "__main__":
    print("Bot escuchando...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)





