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
        hoy = datetime.now()
        dias = (hoy - fecha_vuelo).days
        
        if dias >= 45: return "🔴", dias
        if dias >= 35: return "🟡", dias
        return "🟢", dias
    except:
        return "⚪", 0

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Lista General", "🚨 Alertas Críticas")
    markup.row("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "👨‍✈️ **SISTEMA RESTABLECIDO**\nMostrando reporte con fechas completas.", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def manejar_lista(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        bot.send_message(message.chat.id, "❌ Error: Datos no encontrados.")
        return
    
    personal = doc.get("datos", {})
    res = "📊 **REPORTE COMPLETO**\n"
    
    for cat, gente in personal.items():
        res += f"\n┏━━ **{cat}**\n"
        for i, (nombre, fecha) in enumerate(gente.items(), 1):
            emoji, dias = calcular_vencimiento(fecha)
            # ESTA LÍNEA AHORA SÍ INCLUYE LA FECHA
            res += f"┃ {i}. {emoji} **{nombre}**: {dias} días — Últ: {fecha}\n"
            
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

@bot.message_handler(commands=['vuelo'])
def cmd_vuelo(message):
    try:
        nombre = message.text.split(maxsplit=1)[1].upper()
        doc = coleccion.find_one({"id": "data_principal"})
        personal = doc["datos"]
        encontrado = False
        
        for cat in personal:
            if nombre in personal[cat]:
                hoy_str = datetime.now().strftime("%d/%m/%Y")
                personal[cat][nombre] = hoy_str
                coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": personal}})
                bot.reply_to(message, f"✅ **{nombre}** actualizado a hoy: {hoy_str}")
                encontrado = True
                break
        if not encontrado:
            bot.reply_to(message, "❌ Nombre no encontrado.")
    except:
        bot.reply_to(message, "Usa: `/vuelo NOMBRE`")

bot.infinity_polling()




