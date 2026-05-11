import telebot
from telebot import types
from datetime import datetime
import json
import os

# --- CONFIGURACIÓN ---
TOKEN = "8355996836:AAH5M84faJAB1N2d9Y4YP5BBLk9n3E0_1Ic"
GRUPO_ID = -5211746405 
DB_FILE = "datos_vuelos.json"

bot = telebot.TeleBot(TOKEN)
CATS = ["CAPITANES DE NAVE", "COPILOTOS", "INGENIEROS DE VUELO", "AUXILIARES DE VUELO"]

def cargar_datos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {c: {} for c in CATS}

def guardar(datos):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def calcular(fecha_str):
    d = (datetime.now() - datetime.strptime(fecha_str, "%Y-%m-%d")).days
    if d >= 45: return "🔴", d
    if d >= 35: return "🟡", d
    return "🟢", d

def f_bonita(f_iso):
    return datetime.strptime(f_iso, "%Y-%m-%d").strftime("%d/%m/%Y")

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    m = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    m.add("📋 Lista General", "🚨 Alertas Críticas", "🔍 Chequeo Preventivo", "📖 Ayuda")
    bot.send_message(message.chat.id, "👨‍✈️ **Control Activo en Render**\nUsa /nuevo para añadir gente.", reply_markup=m, parse_mode="Markdown")

@bot.message_handler(commands=['nuevo'])
def cmd_nuevo(message):
    personal = cargar_datos()
    try:
        partes = message.text.split(maxsplit=2)
        nombre = partes[1].upper()
        categoria = partes[2].upper()
        if categoria in CATS:
            personal[categoria][nombre] = datetime.now().strftime("%Y-%m-%d")
            guardar(personal)
            bot.reply_to(message, f"✅ **{nombre}** registrado en {categoria}.")
        else:
            bot.reply_to(message, f"❌ Error. Categorías: {', '.join(CATS)}")
    except:
        bot.reply_to(message, "Uso: `/nuevo NOMBRE CATEGORIA`")

@bot.message_handler(commands=['vuelo'])
def cmd_vuelo(message):
    personal = cargar_datos()
    try:
        n = message.text.split(maxsplit=1)[1].upper()
        for cat in personal:
            if n in personal[cat]:
                personal[cat][n] = datetime.now().strftime("%Y-%m-%d")
                guardar(personal)
                bot.reply_to(message, f"✅ **{n}** actualizado a hoy.")
                return
        bot.reply_to(message, "❌ No encontrado. Usa `/nuevo`.")
    except:
        bot.reply_to(message, "Uso: `/vuelo NOMBRE`")

@bot.message_handler(func=lambda msg: True)
def botones(message):
    personal = cargar_datos()
    if message.text == "📋 Lista General":
        r = "📊 **REPORTE GENERAL ENUMERADO**\n"
        for cat, gente in personal.items():
            r += f"\n┏━━ **{cat}**\n"
            i = 1
            for n, f in gente.items():
                c, d = calcular(f)
                r += f"┃ {i}. {c} **{n}**: {d}d — {f_bonita(f)}\n"
                i += 1
        bot.send_message(message.chat.id, r, parse_mode="Markdown")

    elif message.text == "🚨 Alertas Críticas":
        ro, am = "", ""
        for cat, gente in personal.items():
            ir, ia = 1, 1
            for n, f in gente.items():
                c, d = calcular(f)
                txt = f"**{n}**: {d}d — {f_bonita(f)}\n"
                if c == "🔴": ro += f"{ir}. 🔴 {txt}"; ir += 1
                elif c == "🟡": am += f"{ia}. 🟡 {txt}"; ia += 1
        bot.send_message(message.chat.id, f"🚫 **VENCIDOS:**\n{ro if ro else 'Limpio'}\n\n⚠️ **PRÓXIMOS:**\n{am if am else 'Limpio'}", parse_mode="Markdown")

    elif message.text == "🔍 Chequeo Preventivo":
        ch, ic = "", 1
        for cat, gente in personal.items():
            for n, f in gente.items():
                _, d = calcular(f)
                if d == 34: ch += f"{ic}. 🟡 **{n}** (Mañana Amarillo)\n"; ic += 1
                elif d == 44: ch += f"{ic}. 🔴 **{n}** (Mañana Vence)\n"; ic += 1
        if ch:
            bot.send_message(message.chat.id, "⏳ **CAMBIOS MAÑANA:**\n" + ch, parse_mode="Markdown")
            bot.send_message(GRUPO_ID, "📢 **ALERTA:**\n" + ch, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "✅ Sin cambios mañana.")

    elif message.text == "📖 Ayuda":
        bot.send_message(message.chat.id, "🛠 **COMANDOS**\n`/nuevo NOMBRE CATEGORIA`\n`/vuelo NOMBRE`", parse_mode="Markdown")

print("BOT OPERATIVO")
bot.infinity_polling()
