import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
from flask import Flask
from threading import Thread
import os

# --- 1. SERVIDOR WEB (Para mantener el bot 'Live' en Render) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot de Control de Tripulantes: Activo"

def run():
    # Render usa el puerto 10000 por defecto para servicios web
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. CONFIGURACIÓN DEL BOT Y BASE DE DATOS ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Conexión a MongoDB
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"
client = MongoClient(MONGO_URI)
db = client['sistema_vuelos']
coleccion = db['tripulantes']

# --- 3. LÓGICA DE CÁLCULO ---
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

# --- 4. COMANDOS PRINCIPALES ---
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Lista General", "🚨 Alertas Críticas")
    markup.add("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(
        message.chat.id, 
        "👨‍✈️ **SISTEMA DE CONTROL DE TRIPULANTES**\nSeleccione una opción del menú:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# --- 5. MANEJADOR DE MENSAJES (BOTONES) ---
@bot.message_handler(func=lambda msg: True)
def handle_all_messages(message):
    doc = coleccion.find_one({"id": "data_principal"})
    if not doc:
        # AQUÍ ESTABA EL ERROR DE LA LÍNEA 67. YA ESTÁ CORREGIDO Y CERRADO CORRECTAMENTE.
        bot.reply_to(message, "❌ Error: No se encontró el documento 'data_principal' en la DB.")
        return
    
    personal = doc.get("datos", {})
    text = message.text

    # BOTÓN: LISTA GENERAL
    if "Lista General" in text:
        res = "📊 **REPORTE COMPLETO**\n"
        for cat, gente in personal.items():
            res += f"\n┏━━ **{cat}**\n"
            for n, f in gente.items():
                e, d, _ = calcular_vencimiento(f)
                res += f"┃ {e} **{n}**: {d}d (v: {f})\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")

    # BOTÓN: ALERTAS CRÍTICAS
    elif "Alertas Críticas" in text:
        res = "🔴 **ESTADO CRÍTICO (45+ días)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for n, f in gente.items():
                _, d, s = calcular_vencimiento(f)
                if s == "CRÍTICO":
                    res += f"📍 **{n}**: {d}d (vuelo: {f})\n"
                    encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay personal en estado crítico.")

    # BOTÓN: PRÓXIMOS A VENCER
    elif "Próximos a Vencer" in text:
        res = "🟡 **PRÓXIMOS A VENCER (35-44 días)**\n\n"
        encontrado = False
        for cat, gente in personal.items():
            for n, f in gente.items():
                _, d, s = calcular_vencimiento(f)
                if s == "PREVENTIVO":
                    res += f"🔸 **{n}**: {d}d (vuelo: {f})\n"
                    encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay personal próximo a vencer.")

    # BOTÓN: AYUDA
    elif "Ayuda" in text:
        ayuda_texto = (
            "❓ **AYUDA Y COMANDOS**\n\n"
            "• Escribe `/vuelo NOMBRE` para actualizar la fecha de alguien a hoy.\n"
            "• Verde (🟢): Menos de 35 días.\n"
            "• Amarillo (🟡): Entre 35 y 44 días.\n"
            "• Rojo (🔴): 45 días o más."
        )
        bot.send_message(message.chat.id, ayuda_texto, parse_mode="Markdown")

# --- 6. COMANDO PARA ACTUALIZAR VUELO (CON DIAGNÓSTICO) ---
@bot.message_handler(commands=['vuelo'])
def reset_vuelo(message):
    try:
        nombre_buscar = message.text.split(maxsplit=1)[1].strip().upper()
        
        doc = coleccion.find_one({"id": "data_principal"})
        if not doc:
            bot.reply_to(message, "⚠️ Error técnico: No se encontró 'data_principal' en tu MongoDB.")
            return

        personal = doc.get("datos", {})
        encontrado = False
        key_original = None

        for cat in personal:
            nombres_normalizados = {k.strip().upper(): k for k in personal[cat].keys()}
            if nombre_buscar in nombres_normalizados:
                key_original = nombres_normalizados[nombre_buscar]
                personal[cat][key_original] = datetime.now().strftime("%d/%m/%Y")
                encontrado = True
                break
        
        if not encontrado:
            bot.reply_to(message, f"❌ El nombre **{nombre_buscar}** no existe en la DB.")
            return

        resultado_db = coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": personal}})
        
        respuesta_diagnostico = (
            f"📊 **DIAGNÓSTICO DE ACTUALIZACIÓN**\n"
            f"• Tripulante detectado: `{key_original}`\n"
            f"• Coincidencias en DB: {resultado_db.matched_count}\n"
            f"• Modificados en DB: {resultado_db.modified_count}\n\n"
        )
        
        if resultado_db.matched_count > 0:
            respuesta_diagnostico += "✅ *¡Cambio confirmado y guardado con éxito en MongoDB!*"
        else:
            respuesta_diagnostico += "❌ *MongoDB rechazó la escritura.*"
            
        bot.reply_to(message, respuesta_diagnostico, parse_mode="Markdown")

    except IndexError:
        bot.reply_to(message, "⚠️ Formato incorrecto. Usa: `/vuelo NOMBRE`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"💥 Error inesperado: `{str(e)}`", parse_mode="Markdown")

# --- 7. INICIO DEL BOT ---
if __name__ == "__main__":
    keep_alive()
    print("🚀 Bot iniciado...")
    bot.infinity_polling(skip_pending=True)


















