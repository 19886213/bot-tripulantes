import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
from flask import Flask
from threading import Thread
import os

# 1. SERVIDOR WEB (Para evitar que Render se apague)
app = Flask('')
@app.route('/')
def home(): return "Servidor Activo"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. CONFIGURACIÓN BOT (Usando la variable de Render)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# CONEXIÓN MONGO
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"
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
    except: return "⚪", 0, "ERROR"

# 3. COMANDOS
@bot.message_handler(commands=['start', 'menu'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Lista General", "🚨 Alertas Críticas")
    markup.add("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "✅ **SISTEMA TRIPULANTES CONECTADO**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    # Buscamos el documento principal
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        bot.reply_to(message, "❌ Error: No se encontró 'data_principal' en la DB.")
        return
        
    personal = doc.get("datos", {})
    text = message.text

    # --- BOTÓN: LISTA GENERAL ---
    if "Lista General" in text:
        res = "📊 **REPORTE COMPLETO**\n"
        for cat, gente in personal.items():
            res += f"\n┏━━ **{cat}**\n"
            for n, f in gente.items():
                e, d, _ = calcular_vencimiento(f)
                res += f"┃ {e} **{n}**: {d}d\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")

    # --- BOTÓN: ALERTAS CRÍTICAS ---
    elif "Alertas Críticas" in text:
        res = "🔴 **ESTADO CRÍTICO (45+ días)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for n, f in gente.items():
                _, d, s = calcular_vencimiento(f)
                if s == "CRÍTICO":
                    res += f"📍 **{n}**: {d}d (vuelo: {f})\n"
                    encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay alertas críticas.")

    # --- BOTÓN: PRÓXIMOS A VENCER ---
    elif "Próximos a Vencer" in text:
        res = "🟡 **PRÓXIMOS A VENCER (35-44 días)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for n, f in gente.items():
                _, d, s = calcular_vencimiento(f)
                if s == "PREVENTIVO":
                    res += f"🔸 **{n}**: {d}d (vuelo: {f})\n"
                    encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay personal próximo a vencer.")
    
    # --- BOTÓN: AYUDA ---
    elif "Ayuda" in text:
        ayuda_texto = (
            "❓ **AYUDA Y COMANDOS**\n\n"
            "• Escribe `/vuelo NOMBRE` para actualizar la fecha de alguien a hoy.\n"
            "• Verde (🟢): Menos de 35 días.\n"
            "• Amarillo (🟡): Entre 35 y 44 días.\n"
            "• Rojo (🔴): 45 días o más."
        )
        bot.send_message(message.chat.id, ayuda_texto, parse_mode="Markdown")

@bot.message_handler(commands=['vuelo'])
def reset(message):
    try:
        nombre = message.text.split(maxsplit=1)[1].upper()
        doc = coleccion.find_one({"id": "data_principal"})
        personal = doc["datos"]
        modificado = False
        for cat in personal:
            if nombre in personal[cat]:
                personal[cat][nombre] = datetime.now().strftime("%d/%m/%Y")
                modificado = True
                break
        if modificado:
            coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": personal}})
            bot.reply_to(message, f"✅ **{nombre}** actualizado a hoy (0 días).")
        else:
            bot.reply_to(message, "❌ Nombre no encontrado.")
    except: bot.reply_to(message, "Usa: /vuelo NOMBRE")

if __name__ == "__main__":
    Thread(target=run).start()
    # skip_pending=True limpia el historial para evitar el Error 409 Conflict
    bot.infinity_polling(skip_pending=True)













