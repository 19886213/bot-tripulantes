import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
from flask import Flask
from threading import Thread
import os

# --- CONFIGURACIÓN DE FLASK (Para que Render no dé error de puerto) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot de Tripulantes está en línea!"

def run():
    # Render asigna un puerto dinámico, lo leemos de las variables de entorno
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURACIÓN DEL BOT ---
TOKEN = "8770392349:AAEcYxLOy_42HZu1SOCc3srH1a2qBP8L8rY"
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client['sistema_vuelos']
coleccion = db['tripulantes']

def calcular_vencimiento(f_str):
    try:
        f_limpia = str(f_str).strip().replace(" ", "")
        fecha_vuelo = datetime.strptime(f_limpia, "%d/%m/%Y")
        dias = (datetime.now() - fecha_vuelo).days
        if dias >= 45: return "🔴", dias, "CRÍTICO"
        if dias >= 35: return "🟡", dias, "PREVENTIVO"
        return "🟢", dias, "OK"
    except:
        return "⚪", 0, "ERROR"

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Lista General", "🚨 Alertas Críticas")
    markup.add("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "👨‍✈️ **SISTEMA ACTIVO**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def manejar_mensajes(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc: return
    personal = doc.get("datos", {})
    
    if "Lista General" in message.text:
        res = "📊 **REPORTE COMPLETO**\n"
        for cat, gente in personal.items():
            res += f"\n┏━━ **{cat}**\n"
            for n, f in gente.items():
                e, d, _ = calcular_vencimiento(f)
                res += f"┃ {e} **{n}**: {d}d — {f}\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")
    
    elif "Alertas Críticas" in message.text:
        res = "🔴 **PERSONAL CRÍTICO**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for n, f in gente.items():
                e, d, s = calcular_vencimiento(f)
                if s == "CRÍTICO":
                    res += f"📍 **{n}**: {d}d\n"
                    encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ Sin alertas.")

@bot.message_handler(commands=['vuelo'])
def cmd_vuelo(message):
    try:
        nombre = message.text.split(maxsplit=1)[1].upper()
        doc = coleccion.find_one({"id": "data_principal"})
        personal = doc["datos"]
        for cat in personal:
            if nombre in personal[cat]:
                hoy = datetime.now().strftime("%d/%m/%Y")
                personal[cat][nombre] = hoy
                coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": personal}})
                bot.reply_to(message, f"✅ **{nombre}** reseteado a 0 días.")
                return
    except:
        bot.reply_to(message, "Usa: /vuelo NOMBRE")

# --- INICIO ---
if __name__ == "__main__":
    keep_alive()  # Esto activa el servidor web para Render
    print("🚀 Bot iniciado...")
    bot.infinity_polling()









