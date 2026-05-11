import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient

# --- CONFIGURACIÓN ---
TOKEN = "8770392349:AAEcYxLOy_42HZu1SOCc3srH1a2qBP8L8rY"
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"

client = MongoClient(MONGO_URI)
db = client['sistema_vuelos']
coleccion = db['tripulantes']
bot = telebot.TeleBot(TOKEN)

def calcular_vencimiento(f_str):
    try:
        d = (datetime.now() - datetime.strptime(f_str, "%Y-%m-%d")).days
        if d >= 45: return "🔴", d
        if d >= 35: return "🟡", d
        return "🟢", d
    except:
        return "⚪", 0

# --- 1. FUNCIÓN: MENÚ PRINCIPAL ---
@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add("📋 Lista General", "🚨 Alertas Críticas", "⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(message.chat.id, "👨‍✈️ **Control de Tripulación**\nSeleccione una opción o use `/vuelo NOMBRE`", reply_markup=m, parse_mode="Markdown")

# --- 2. FUNCIÓN: LISTA GENERAL ---
@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def cmd_lista(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        bot.send_message(message.chat.id, "❌ No hay datos.")
        return
    personal = doc["datos"]
    res = "📊 **ESTADO GENERAL**\n"
    for cat, gente in personal.items():
        res += f"\n┏━━ **{cat}**\n"
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            res += f"┃ {e} **{n}**: {d}d\n"
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

# --- 3. FUNCIÓN: ROJOS (CRÍTICOS) ---
@bot.message_handler(func=lambda msg: msg.text == "🚨 Alertas Críticas")
def cmd_rojo(message):
    doc = coleccion.find_one({"id": "data_principal"})
    personal = doc["datos"]
    res = "🔴 **ALERTAS CRÍTICAS (45+ días)**\n"
    hay = False
    for cat, gente in personal.items():
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            if d >= 45:
                res += f"⚠️ {n}: {d} días\n"
                hay = True
    bot.send_message(message.chat.id, res if hay else "✅ Sin alertas críticas.", parse_mode="Markdown")

# --- 4. FUNCIÓN: AMARILLOS (PREVENTIVOS) ---
@bot.message_handler(func=lambda msg: msg.text == "⚠️ Próximos a Vencer")
def cmd_amarillo(message):
    doc = coleccion.find_one({"id": "data_principal"})
    personal = doc["datos"]
    res = "🟡 **PRÓXIMOS A VENCER (35-44 días)**\n"
    hay = False
    for cat, gente in personal.items():
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            if 35 <= d < 45:
                res += f"🔸 {n}: {d} días\n"
                hay = True
    bot.send_message(message.chat.id, res if hay else "✅ Sin alertas preventivas.", parse_mode="Markdown")

# --- 5. FUNCIÓN: AYUDA ---
@bot.message_handler(func=lambda msg: msg.text == "❓ Ayuda")
def cmd_ayuda(message):
    bot.send_message(message.chat.id, "📖 **AYUDA**\n\n1. Botones para ver estados.\n2. `/vuelo NOMBRE` para reiniciar a 0.\n3. `/menu` para volver a ver botones.", parse_mode="Markdown")

# --- 6. FUNCIÓN: ACTUALIZAR VUELO ---
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
                bot.reply_to(message, f"✅ **{nombre}** actualizado.")
                return
        bot.reply_to(message, "❌ No encontrado.")
    except:
        bot.reply_to(message, "Usa: `/vuelo NOMBRE`")

print("🚀 BOT INICIADO...")
bot.infinity_polling()


