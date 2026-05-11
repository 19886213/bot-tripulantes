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

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Lista General", "🚨 Alertas Críticas")
    markup.row("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "👨‍✈️ **SISTEMA INTEGRAL DE VUELOS**\nSeleccione una opción del menú:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def manejar_mensajes(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        bot.send_message(message.chat.id, "❌ Error: Datos no encontrados.")
        return
    
    personal = doc.get("datos", {})

    if message.text == "📋 Lista General":
        res = "📊 **REPORTE COMPLETO**\n"
        for cat, gente in personal.items():
            res += f"\n┏━━ **{cat}**\n"
            for i, (nombre, fecha) in enumerate(gente.items(), 1):
                emoji, dias, _ = calcular_vencimiento(fecha)
                res += f"┃ {i}. {emoji} **{nombre}**: {dias}d — Últ: {fecha}\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")

    elif message.text == "🚨 Alertas Críticas":
        res = "🔴 **PERSONAL EN ESTADO CRÍTICO (45+ días)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for nombre, fecha in gente.items():
                emoji, dias, estado = calcular_vencimiento(fecha)
                if estado == "CRÍTICO":
                    res += f"📍 **{nombre}**: {dias} días (Últ: {fecha})\n"
                    encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay personal en estado crítico.")

    elif message.text == "⚠️ Próximos a Vencer":
        res = "🟡 **PERSONAL PRÓXIMO A VENCER (35-44 días)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for nombre, fecha in gente.items():
                emoji, dias, estado = calcular_vencimiento(fecha)
                if estado == "PREVENTIVO":
                    res += f"🔸 **{nombre}**: {dias} días (Últ: {fecha})\n"
                    encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay personal próximo a vencer.")

    elif message.text == "❓ Ayuda":
        ayuda = (
            "❓ **MANUAL DE USO RÁPIDO**\n\n"
            "1️⃣ **Botones:** Usa el menú para ver reportes rápidos.\n"
            "2️⃣ **Actualizar Vuelo:** Escribe `/vuelo NOMBRE` para poner a alguien en 0 días (🟢).\n"
            "3️⃣ **Colores:**\n"
            "   🟢 0-34 días: Al día.\n"
            "   🟡 35-44 días: Preventivo.\n"
            "   🔴 45+ días: Crítico.\n\n"
            "*Nota: Las fechas en MongoDB deben ser DD/MM/AAAA.*"
        )
        bot.send_message(message.chat.id, ayuda, parse_mode="Markdown")

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
                bot.reply_to(message, f"✅ **{nombre}** actualizado a hoy: {hoy} (🟢)")
                return
        bot.reply_to(message, "❌ Nombre no encontrado.")
    except:
        bot.reply_to(message, "Usa: `/vuelo NOMBRE`", parse_mode="Markdown")

bot.infinity_polling()






