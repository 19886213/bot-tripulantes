import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
import os

# --- CONFIGURACIÓN ---
TOKEN = "8770392349:AAEcYxLOy_42HZu1SOCc3srH1a2qBP8L8rY"
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['sistema_vuelos']
    coleccion = db['tripulantes']
    bot = telebot.TeleBot(TOKEN)
    print("✅ Conexión exitosa a MongoDB")
except Exception as e:
    print(f"❌ Error de conexión: {e}")

def calcular_vencimiento(f_str):
    try:
        d = (datetime.now() - datetime.strptime(f_str, "%Y-%m-%d")).days
        if d >= 45: return "🔴", d
        if d >= 35: return "🟡", d
        return "🟢", d
    except:
        return "⚪", 0

# --- MENÚ ---
@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Lista General", "🚨 Alertas Críticas")
    markup.row("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "👋 **¡Bot Conectado!**\nUsa los botones para consultar.", reply_markup=markup, parse_mode="Markdown")

# --- LISTA GENERAL ---
@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def cmd_lista(message):
    bot.send_chat_action(message.chat.id, 'typing')
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        bot.send_message(message.chat.id, "❌ No se encontraron datos.")
        return
    
    personal = doc.get("datos", {})
    res = "📊 **REPORTE ACTUAL**\n"
    for cat, gente in personal.items():
        res += f"\n┏━━ **{cat}**\n"
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            res += f"┃ {e} **{n}**: {d}d\n"
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

# --- ALERTA ROJA ---
@bot.message_handler(func=lambda msg: msg.text == "🚨 Alertas Críticas")
def cmd_rojo(message):
    doc = coleccion.find_one({"id": "data_principal"})
    personal = doc.get("datos", {})
    res = "🔴 **ALERTAS CRÍTICAS (45+ días)**\n"
    hay = False
    for cat, gente in personal.items():
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            if d >= 45:
                res += f"⚠️ {n}: {d} días\n"
                hay = True
    bot.send_message(message.chat.id, res if hay else "✅ Todo en orden (45+).", parse_mode="Markdown")

# --- ALERTA AMARILLA ---
@bot.message_handler(func=lambda msg: msg.text == "⚠️ Próximos a Vencer")
def cmd_amarillo(message):
    doc = coleccion.find_one({"id": "data_principal"})
    personal = doc.get("datos", {})
    res = "🟡 **PRÓXIMOS A VENCER (35-44 días)**\n"
    hay = False
    for cat, gente in personal.items():
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            if 35 <= d < 45:
                res += f"🔸 {n}: {d} días\n"
                hay = True
    bot.send_message(message.chat.id, res if hay else "✅ Todo en orden (35-44).", parse_mode="Markdown")

# --- AYUDA ---
@bot.message_handler(func=lambda msg: msg.text == "❓ Ayuda")
def cmd_ayuda(message):
    bot.send_message(message.chat.id, "💡 **Instrucciones:**\n1. Usa los botones para ver listas.\n2. Escribe `/vuelo NOMBRE` para resetear.\n3. Si el bot no responde, pulsa /start.", parse_mode="Markdown")

# --- VUELO ---
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
    except:
        bot.reply_to(message, "Escribe: `/vuelo NOMBRE`")

print("🚀 BOT INICIADO Y ESCUCHANDO...")
bot.infinity_polling()

