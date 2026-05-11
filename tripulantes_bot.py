import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient

TOKEN = "8770392349:AAEcYxLOy_42HZu1SOCc3srH1a2qBP8L8rY"
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client['sistema_vuelos']
coleccion = db['tripulantes']

def calcular_vencimiento(f_str):
    try:
        # AQUÍ CAMBIAMOS EL FORMATO A DIA/MES/AÑO
        fecha_vuelo = datetime.strptime(f_str, "%d/%m/%Y")
        dias_transcurridos = (datetime.now() - fecha_vuelo).days
        
        if dias_transcurridos >= 45:
            return "🔴", dias_transcurridos
        elif dias_transcurridos >= 35:
            return "🟡", dias_transcurridos
        else:
            return "🟢", dias_transcurridos
    except Exception as e:
        return "⚪", 0

@bot.message_handler(commands=['start'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Lista General", "🚨 Alertas Críticas")
    markup.row("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "👨‍✈️ **SISTEMA DE VUELOS ACTUALIZADO**\nLas fechas ahora se manejan como DD/MM/AAAA.", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def manejar_botones(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        bot.send_message(message.chat.id, "❌ No hay datos.")
        return
    
    personal = doc.get("datos", {})

    if message.text == "📋 Lista General":
        res = "📊 **REPORTE DE TRIPULACIÓN**\n"
        for cat, gente in personal.items():
            res += f"\n┏━━ **{cat}**\n"
            for n, f in gente.items():
                e, d = calcular_vencimiento(f)
                res += f"┃ {e} **{n}**: {d} días\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")
    
    # Agregamos la lógica para los otros botones
    elif message.text == "🚨 Alertas Críticas":
        res = "🔴 **PERSONAL CRÍTICO (45+ DÍAS)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for n, f in gente.items():
                e, d = calcular_vencimiento(f)
                if d >= 45:
                    res += f"📍 {n} ({cat}): {d} días\n"
                    encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay alertas críticas.")

@bot.message_handler(commands=['vuelo'])
def cmd_vuelo(message):
    try:
        nombre = message.text.split(maxsplit=1)[1].upper()
        doc = coleccion.find_one({"id": "data_principal"})
        personal = doc["datos"]
        for cat in personal:
            if nombre in personal[cat]:
                # Actualiza a fecha de hoy en formato DD/MM/AAAA
                personal[cat][nombre] = datetime.now().strftime("%d/%m/%Y")
                coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": personal}})
                bot.reply_to(message, f"✅ Fecha de vuelo actualizada para: {nombre}")
                return
        bot.reply_to(message, "❌ Nombre no encontrado en la lista.")
    except:
        bot.reply_to(message, "Usa: `/vuelo NOMBRE`", parse_mode="Markdown")

bot.infinity_polling()

