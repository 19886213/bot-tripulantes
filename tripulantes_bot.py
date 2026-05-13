import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
from flask import Flask
from threading import Thread
import os

# --- WEB SERVER PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Servidor Activo"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURACIÓN DEL BOT ---
# ¡CAMBIA ESTE TOKEN POR EL NUEVO QUE TE DÉ BOTFATHER!
TOKEN = "8770392349:AAEcYxLOy_42HZu1SOCc3srH1a2qBP8L8rY"
bot = telebot.TeleBot(TOKEN)

client = MongoClient("mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv")
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
    except: return "⚪", 0, "ERROR"

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Lista General", "🚨 Alertas Críticas")
    markup.add("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "👨‍✈️ **SISTEMA TRIPULANTES**\nSelecciona una opción:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_all_messages(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc: return
    personal = doc.get("datos", {})
    text = message.text

    if "Lista General" in text:
        res = "📊 **REPORTE COMPLETO**\n"
        for cat, gente in personal.items():
            res += f"\n┏━━ **{cat}**\n"
            for n, f in gente.items():
                e, d, _ = calcular_vencimiento(f)
                res += f"┃ {e} **{n}**: {d}d (v: {f})\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")

    elif "Alertas Críticas" in text:
        res = "🔴 **ESTADO CRÍTICO (45+ días)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for n, f in gente.items():
                e, d, s = calcular_vencimiento(f)
                if s == "CRÍTICO":
                    res += f"📍 **{n}**: {d}d\n"
                    encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay críticos.")

    elif "Próximos a Vencer" in text:
        res = "🟡 **PRÓXIMOS A VENCER (35-44 días)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for n, f in gente.items():
                e, d, s = calcular_vencimiento(f)
                if s == "PREVENTIVO":
                    res += f"🔸 **{n}**: {d}d\n"
                    encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay próximos.")

    elif "Ayuda" in text:
        bot.send_message(message.chat.id, "❓ **AYUDA**\nUsa `/vuelo NOMBRE` para resetear a 0 días.", parse_mode="Markdown")

@bot.message_handler(commands=['vuelo'])
def reset_vuelo(message):
    try:
        nombre = message.text.split(maxsplit=1)[1].upper()
        doc = coleccion.find_one({"id": "data_principal"})
        personal = doc["datos"]
        for cat in personal:
            if nombre in personal[cat]:
                hoy = datetime.now().strftime("%d/%m/%Y")
                personal[cat][nombre] = hoy
                coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": personal}})
                bot.reply_to(message, f"✅ **{nombre}** reseteado a hoy.")
                return
        bot.reply_to(message, "❌ No encontrado.")
    except: bot.reply_to(message, "Usa: /vuelo NOMBRE")

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling(skip_pending=True)










