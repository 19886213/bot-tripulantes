import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient

# --- CONFIGURACIÓN ---
TOKEN = "8770392349:AAEcYxLOy_42HZu1SOCc3srH1a2qBP8L8rY"
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client['sistema_vuelos']
coleccion = db['tripulantes']

def calcular_vencimiento(f_str):
    try:
        d = (datetime.now() - datetime.strptime(f_str, "%Y-%m-%d")).days
        if d >= 45: return "🔴", d
        if d >= 35: return "🟡", d
        return "🟢", d
    except: return "⚪", 0

# --- MENÚ (AQUÍ ESTÁ LA MAGIA) ---
@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Definimos las filas de los botones
    markup.row("📋 Lista General", "🚨 Alertas Críticas")
    markup.row("⚠️ Próximos a Vencer", "❓ Ayuda")
    
    bot.send_message(
        message.chat.id, 
        "👨‍✈️ **SISTEMA DE VUELOS ACTIVO**\nSeleccione una opción del menú:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def cmd_lista(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        bot.send_message(message.chat.id, "❌ No hay datos en MongoDB.")
        return
    personal = doc.get("datos", {})
    res = "📊 **REPORTE ACTUAL**\n"
    for cat, gente in personal.items():
        res += f"\n┏━━ **{cat}**\n"
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            res += f"┃ {e} **{n}**: {d}d\n"
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

# (Las demás funciones se activan con los botones arriba creados)

print("🚀 Bot iniciado con éxito...")
bot.infinity_polling()




