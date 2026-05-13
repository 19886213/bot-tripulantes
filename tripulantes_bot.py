import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
from flask import Flask
from threading import Thread
import os

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
# Esto lee el token desde la variable que pusiste en la imagen 244014.jpg
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- 2. SERVIDOR WEB (PARA RENDER) ---
app = Flask('')
@app.route('/')
def home(): return "Bot de Tripulantes Activo"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 3. BASE DE DATOS ---
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"
client = MongoClient(MONGO_URI)
db = client['sistema_vuelos']
coleccion = db['tripulantes']

# --- 4. FUNCIONES Y COMANDOS ---
def calcular_vencimiento(f_str):
    try:
        f_limpia = str(f_str).strip().replace(" ", "")
        fecha_vuelo = datetime.strptime(f_limpia, "%d/%m/%Y")
        dias = (datetime.now() - fecha_vuelo).days
        if dias >= 45: return "🔴", dias, "CRÍTICO"
        if dias >= 35: return "🟡", dias, "PREVENTIVO"
        return "🟢", dias, "OK"
    except: return "⚪", 0, "ERROR"

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Lista General", "🚨 Alertas Críticas")
    markup.add("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "👨‍✈️ **SISTEMA ACTIVO**\nSeleccione una opción:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_messages(message):
    doc = coleccion.find_one({"id": "data_principal"})
    personal = doc.get("datos", {})
    text = message.text

    if "Lista General" in text:
        res = "📊 **REPORTE**\n"
        for cat, gente in personal.items():
            res += f"\n┏━━ **{cat}**\n"
            for n, f in gente.items():
                e, d, _ = calcular_vencimiento(f)
                res += f"┃ {e} **{n}**: {d}d\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")
    
    elif "Ayuda" in text:
        res = "❓ **AYUDA Y COMANDOS**\n\n• Escribe `/vuelo NOMBRE` para actualizar.\n• Verde (🟢): < 35d.\n• Amarillo (🟡): 35-44d.\n• Rojo (🔴): 45d+."
        bot.send_message(message.chat.id, res, parse_mode="Markdown")

@bot.message_handler(commands=['vuelo'])
def reset_vuelo(message):
    try:
        nombre = message.text.split(maxsplit=1)[1].upper()
        doc = coleccion.find_one({"id": "data_principal"})
        personal = doc["datos"]
        for cat in personal:
            if nombre in personal[cat]:
                personal[cat][nombre] = datetime.now().strftime("%d/%m/%Y")
                coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": personal}})
                bot.reply_to(message, f"✅ **{nombre}** reseteado a 0 días.")
                return
        bot.reply_to(message, "❌ No encontrado.")
    except: bot.reply_to(message, "Usa: /vuelo NOMBRE")

if __name__ == "__main__":
    Thread(target=run).start()
    print("🚀 Bot iniciado correctamente")
    bot.infinity_polling(skip_pending=True)












