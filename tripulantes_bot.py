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
        f_limpia = str(f_str).strip().replace(".", "")
        fecha_vuelo = datetime.strptime(f_limpia, "%d/%m/%Y")
        
        # Fecha de hoy (Sincronizada)
        hoy = datetime.now()
        dias = (hoy - fecha_vuelo).days
        
        if dias >= 45: return "🔴", dias
        if dias >= 35: return "🟡", dias
        return "🟢", dias
    except Exception:
        return "⚪", 0

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Lista General", "🚨 Alertas Críticas")
    markup.row("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message



