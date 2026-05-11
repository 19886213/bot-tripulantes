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
        f_limpia = str(f_str).strip().replace(" ", "")
        fecha_vuelo = datetime.strptime(f_limpia, "%d/%m/%Y")
        dias = (datetime.now() - fecha_vuelo).days
        if dias >= 45: return "🔴", dias, "CRÍTICO"
        if dias >= 35: return "🟡", dias, "PREVENTIVO"
        return "🟢", dias, "OK"
    except:
        return "⚪", 0, "ERROR"

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Definimos los botones exactamente como los compararemos después
    btn1 = types.KeyboardButton("📋 Lista General")
    btn2 = types.KeyboardButton("🚨 Alertas Críticas")
    btn3 = types.KeyboardButton("⚠️ Próximos a Vencer")
    btn4 = types.KeyboardButton("❓ Ayuda")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    bot.send_message(message.chat.id, "👨‍✈️ **SISTEMA ACTIVO**\nSeleccione una opción del menú:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def manejar_mensajes(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        bot.send_message(message.chat.id, "❌ Error: No se encontraron datos en MongoDB.")
        return
    
    personal = doc.get("datos", {})
    texto_final = ""

    # Usamos "in" por si el texto trae emojis o espacios extra
    text = message.text

    if "Lista General" in text:
        texto_final = "📊 **REPORTE COMPLETO**\n"
        for cat, gente in personal.items():
            texto_final += f"\n┏━━ **{cat}**\n"
            for i, (nombre, fecha) in enumerate(gente.items(), 1):
                emoji, dias, _ = calcular_vencimiento(fecha)
                texto_final += f"┃ {i}. {emoji} **{nombre}**: {dias}d — Últ: {fecha}\n"
    
    elif "Alertas Críticas" in text:
        texto_final = "🔴 **ESTADO CRÍTICO (45+ días)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for nombre, fecha in gente.items():
                emoji, dias, estado = calcular_vencimiento(fecha)
                if estado == "CRÍTICO":
                    texto_final += f"📍 **{nombre}**: {dias}d (Últ: {fecha})\n"
                    encontrado = True
        if not encontrado: texto_final = "✅ No hay personal en estado crítico."

    elif "Próximos a Vencer" in text:
        texto_final = "🟡 **PRÓXIMOS A VENCER (35-44 días)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for nombre, fecha in gente.items():
                emoji, dias, estado = calcular_vencimiento(fecha)
                if estado == "PREVENTIVO":
                    texto_final += f"🔸 **{nombre}**: {dias}d (Últ: {fecha})\n"
                    encontrado = True
        if not encontrado: texto_final = "✅ No hay personal próximo a vencer."

    elif "Ayuda" in text:
        texto_final = (
            "❓ **AYUDA Y COMANDOS**\n\n"
            "• Escribe `/vuelo NOMBRE` para actualizar la fecha de alguien a hoy.\n"
            "• **Verde (🟢):** Menos de 35 días.\n"
            "• **Amarillo (🟡):** Entre 35 y 44 días.\n"
            "• **Rojo (🔴):** 45 días o más."
        )

    if texto_final:
        bot.send_message(message.chat.id, texto_final, parse_mode="Markdown")

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
                bot.reply_to(message, f"✅ **{nombre}** actualizado a hoy: {hoy}")
                return
        bot.reply_to(message, "❌ Nombre no encontrado.")
    except:
        bot.reply_to(message, "Usa: `/vuelo NOMBRE` (Ej: /vuelo CAMPOCLARO)")

bot.infinity_polling()







