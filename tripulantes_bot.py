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
        # Esto limpia espacios y quita los puntos que a veces se cuelan
        limpio = str(f_str).strip().replace(".", "")
        
        # Leemos el formato DIA/MES/AÑO que tienes en tu JSON
        fecha_vuelo = datetime.strptime(limpio, "%d/%m/%Y")
        
        # Fecha actual (Hoy es 11 de Mayo de 2026)
        hoy = datetime.now()
        dias = (hoy - fecha_vuelo).days
        
        if dias >= 45: return "🔴", dias
        if dias >= 35: return "🟡", dias
        return "🟢", dias
    except:
        return "⚪", 0

@bot.message_handler(commands=['start'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Lista General", "🚨 Alertas Críticas")
    markup.row("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "👨‍✈️ **SISTEMA SINCRONIZADO**\nPulsa 'Lista General' para ver los colores.", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def manejar_lista(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        bot.send_message(message.chat.id, "❌ No encontré los datos en MongoDB.")
        return
    
    personal = doc.get("datos", {})
    res = "📊 **REPORTE DE TRIPULACIÓN**\n"
    
    for cat, gente in personal.items():
        res += f"\n┏━━ **{cat}**\n"
        # Usamos i+1 para enumerar la lista automáticamente
        for i, (nombre, fecha) in enumerate(gente.items()):
            emoji, dias = calcular_vencimiento(fecha)
            res += f"┃ {i+1}. {emoji} **{nombre}**: {dias}d — Últ: {fecha}\n"
            
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

@bot.message_handler(commands=['vuelo'])
def cmd_vuelo(message):
    try:
        # Extrae el nombre después del comando /vuelo
        nombre = message.text.split(maxsplit=1)[1].upper()
        doc = coleccion.find_one({"id": "data_principal"})
        personal = doc["datos"]
        encontrado = False
        
        for cat in personal:
            if nombre in personal[cat]:
                hoy_str = datetime.now().strftime("%d/%m/%Y")
                personal[cat][nombre] = hoy_str
                coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": personal}})
                bot.reply_to(message, f"✅ **{nombre}** actualizado a hoy: {hoy_str} (🟢)")
                encontrado = True
                break
        if not encontrado:
            bot.reply_to(message, "❌ No encontré ese nombre.")
    except:
        bot.reply_to(message, "Usa: `/vuelo NOMBRE`")

bot.infinity_polling()


