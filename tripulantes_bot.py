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
        f_limpia = str(f_str).strip().replace(" ", "")
        fecha_vuelo = datetime.strptime(f_limpia, "%d/%m/%Y")
        dias = (datetime.now() - fecha_vuelo).days
        
        if dias >= 45: return "🔴", dias, "CRÍTICO"
        if dias >= 35: return "🟡", dias, "PREVENTIVO"
        return "🟢", dias, "OK"
    except:
        return "⚪", 0, "ERROR"

@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def manejar_lista(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        bot.send_message(message.chat.id, "❌ Error: Datos no encontrados.")
        return
    
    personal = doc.get("datos", {})
    
    # --- SISTEMA DE ALERTA AL DESPERTAR ---
    alertas_criticas = []
    for cat, gente in personal.items():
        for nombre, fecha in gente.items():
            emoji, dias, estado = calcular_vencimiento(fecha)
            if estado == "CRÍTICO":
                alertas_criticas.append(f"🚨 {nombre} ({dias} días sin volar)")

    # Si hay gente en rojo, manda este mensaje primero
    if alertas_criticas:
        aviso = "⚠️ **¡ALERTA DE VENCIMIENTO!**\n\nAl procesar la lista he detectado personal en estado crítico:\n\n"
        aviso += "\n".join(alertas_criticas)
        bot.send_message(message.chat.id, aviso, parse_mode="Markdown")
    # ---------------------------------------

    # Mostrar la lista normal después del aviso
    res = "📊 **REPORTE ACTUALIZADO**\n"
    for cat, gente in personal.items():
        res += f"\n┏━━ **{cat}**\n"
        for i, (nombre, fecha) in enumerate(gente.items(), 1):
            emoji, dias, _ = calcular_vencimiento(fecha)
            res += f"┃ {i}. {emoji} **{nombre}**: {dias}d — Últ: {fecha}\n"
    
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

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
                bot.reply_to(message, f"✅ {nombre} actualizado a hoy: {hoy} 🟢")
                return
        bot.reply_to(message, "❌ No encontrado.")
    except:
        bot.reply_to(message, "Usa: /vuelo NOMBRE")

bot.infinity_polling()





