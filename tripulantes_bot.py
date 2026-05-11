import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient

# 1. TOKEN ACTUALIZADO
TOKEN = "8770392349:AAFaJW4zHfNohY3UUvC3pVHTd1DPmzG7_5o"

# 2. CONEXIÓN MONGODB
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"

client = MongoClient(MONGO_URI)
db = client['sistema_vuelos']
coleccion = db['tripulantes']
bot = telebot.TeleBot(TOKEN)

# Datos iniciales de respaldo
DATOS_INICIALES = {
    "CAPITANES DE NAVE": {"CAMPOCLARO": "2026-05-07", "MANAUS": "2026-05-07", "CAMORUCO": "2026-05-08", "SAURIO": "2026-04-15", "MONARCA": "2026-05-06"},
    "COPILOTOS": {"TÁRTARO": "2021-09-01", "CASUPO": "2026-05-08", "HUESO": "2026-05-04", "CHAGUARAMO": "2026-04-23", "DORADO": "2026-05-04", "CHAMERO": "2026-04-15", "ATLÁNTICO": "2026-04-15", "CURAGUA": "2026-05-07", "YOCOIMA": "2026-05-06", "MACARIO": "2026-04-15", "GÜIGÜE": "2026-05-08", "ÉBANO": "2026-05-07", "PAMPATAR": "2026-04-15"},
    "INGENIEROS DE VUELO": {"CNEL. MARCOS FLORES": "2026-05-06", "TCNEL. JOSÉ ALONZO": "2026-03-19", "TCNEL. ELVIS GONZALEZ": "2026-04-15", "MAY. YEICKSON ALEJO": "2026-05-08", "CAP. JOHN MENESES": "2026-05-07", "PTTE. ANA DABOIN": "2026-05-04", "SM1. YOEL HENRIQUEZ": "2026-04-15", "SM2. LUIS RODRÍGUEZ": "2026-05-07"},
    "AUXILIARES DE VUELO": {"MAY. WILMER GUERRA": "2025-02-01", "PTTE. NALDI VELOZ": "2026-02-05", "TTE. YELISMAR BARRIENTOS": "2026-05-07", "TTE. EMELLY SALAS": "2026-05-06", "SM2. HÉCTOR BARRUETA": "2026-05-04", "SM2. GEORGE MÁRQUEZ": "2026-04-15", "SM2. JOSÉ PERALTA": "2026-05-08", "SM2. RICARDO GARCÍA": "2026-05-07", "SM3. LEWIS CEBALLOS": "2026-04-15", "SM3. ANTHONY OROPEZA": "2026-04-15", "SM3. ELVIN BOTABAN": "2024-04-01", "S1. ALIXON ROJAS": "2026-05-08", "S1. ERGNY HERNÁNDEZ": "2025-02-27", "S1. MISAEL ABACHE": "2026-03-16", "S1. RUSHDELIS LA ROSA": "2026-05-06", "S1. ESTEBAN RODRÍGUEZ": "2026-03-03", "S1. AMILCAR MECHEH": "2026-05-07", "S2. JESUS DABOIN": "2026-05-07"}
}

def obtener_personal():
    try:
        doc = coleccion.find_one({"id": "data_principal"})
        if not doc:
            coleccion.insert_one({"id": "data_principal", "datos": DATOS_INICIALES})
            return DATOS_INICIALES
        return doc["datos"]
    except:
        return DATOS_INICIALES

def guardar_personal(datos):
    coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": datos}}, upsert=True)

def calcular_vencimiento(f_str):
    d = (datetime.now() - datetime.strptime(f_str, "%Y-%m-%d")).days
    emoji = "🟢"
    if d >= 45: emoji = "🔴"
    elif d >= 35: emoji = "🟡"
    return emoji, d

# --- COMANDOS ---

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("📋 Lista General", "🚨 Alertas Críticas")
    bot.send_message(message.chat.id, "👨‍✈️ **Control de Vuelos Activo**\nSeleccione una opción:", reply_markup=m, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📋 Lista General")
def cmd_lista(message):
    personal = obtener_personal()
    res = "📊 **REPORTE DE ESTADO**\n"
    for cat, gente in personal.items():
        res += f"\n┏━━ **{cat}**\n"
        for i, (n, f) in enumerate(gente.items(), 1):
            e, d = calcular_vencimiento(f)
            res += f"┃ {i}. {e} **{n}**: {d}d\n"
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🚨 Alertas Críticas")
def cmd_alertas(message):
    personal = obtener_personal()
    res = "🚨 **PERSONAL EN ALERTA (45+ días)**\n"
    hay_alertas = False
    for cat, gente in personal.items():
        for n, f in gente.items():
            e, d = calcular_vencimiento(f)
            if d >= 45:
                res += f"⚠️ {n} ({cat}): {d} días\n"
                hay_alertas = True
    
    if not hay_alertas:
        res = "✅ No hay alertas críticas actualmente."
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

@bot.message_handler(commands=['vuelo'])
def cmd_vuelo(message):
    try:
        nombre = message.text.split(maxsplit=1)[1].upper()
        personal = obtener_personal()
        encontrado = False
        for cat in personal:
            if nombre in personal[cat]:
                personal[cat][nombre] = datetime.now().strftime("%Y-%m-%d")
                guardar_personal(personal)
                bot.reply_to(message, f"✅ **{nombre}** actualizado. Contador a 0 días.")
                encontrado = True
                break
        if not encontrado:
            bot.reply_to(message, f"❌ El nombre **{nombre}** no está en la base de datos.")
    except:
        bot.reply_to(message, "Usa: `/vuelo NOMBRE` (ejemplo: `/vuelo CAMPOCLARO`)")

print("INICIANDO BOT...")
bot.infinity_polling()



