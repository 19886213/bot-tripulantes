import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
from flask import Flask
from threading import Thread
import os
import logging

# Configurar logs básicos para ver errores en Render
logging.basicConfig(level=logging.INFO)

# --- 1. SERVIDOR WEB (En hilo secundario para mantener el bot 'Live') ---
app = Flask('')

@app.route('/')
def home():
    return "Bot de Control de Tripulantes: Activo"

def run_flask():
    # Render usa el puerto 10000 por defecto para servicios web
    port = int(os.environ.get("PORT", 10000))
    # 'threaded=True' ayuda a manejar múltiples peticiones HTTP de Render sin congelarse
    app.run(host='0.0.0.0', port=port, threaded=True)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True  # Permite que el hilo muera si el proceso principal se detiene
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

# --- 6. COMANDO PARA ACTUALIZAR VUELO ---
@bot.message_handler(commands=['vuelo'])
def reset_vuelo(message):
    try:
        argumento = message.text.split(maxsplit=1)
        if len(argumento) < 2:
            bot.reply_to(message, "⚠️ Formato incorrecto. Usa: `/vuelo NOMBRE`", parse_mode="Markdown")
            return
            
        nombre_buscar = argumento[1].strip().upper()
        doc = coleccion.find_one({"id": "data_principal"})
        
        if not doc:
            bot.reply_to(message, "⚠️ Error de Base de Datos: No existe el documento 'data_principal'.")
            return

        personal = doc.get("datos", {})
        encontrado = False
        categoria_destino = None
        key_original = None

        for cat, tripulantes in personal.items():
            for nombre_db in tripulantes.keys():
                if nombre_buscar in nombre_db.strip().upper() or nombre_db.strip().upper() in nombre_buscar:
                    key_original = nombre_db
                    categoria_destino = cat
                    encontrado = True
                    break
            if encontrado:
                break
        
        if encontrado:
            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
            personal[categoria_destino][key_original] = fecha_hoy
            coleccion.update_one({"id": "data_principal"}, {"$set": {"datos": personal}})
            
            bot.reply_to(
                message, 
                f"✅ **PROCESADO EXITOSAMENTE**\n"
                f"• **Tripulante:** `{key_original}`\n"
                f"• **Nueva Fecha:** {fecha_hoy}\n\n"
                f"💾 *Cambio sincronizado con la base de datos de MongoDB.*",
                parse_mode="Markdown"
            )
        else:
            nombres_disponibles = []
            for cat, t in personal.items():
                nombres_disponibles.extend(t.keys())
            lista_nombres = ", ".join([f"`{n}`" for n in nombres_disponibles[:10]])
            bot.reply_to(
                message, 
                f"❌ No encontré a **{nombre_buscar}**.\n\n"
                f"📋 *Nombres en DB:* {lista_nombres}...",
                parse_mode="Markdown"
            )

    except Exception as e:
        bot.reply_to(message, f"💥 Error interno: `{str(e)}`", parse_mode="Markdown")

# --- 7. EJECUCIÓN PRINCIPAL DEL SISTEMA ---
if __name__ == "__main__":
    # Primero: Iniciamos Flask en segundo plano (hilo secundario)
    keep_alive()
    print("🚀 Servidor Web Flask en segundo plano iniciado...")
    
    # Segundo: Corremos Telegram en el hilo principal del procesador.
    # Esto asegura que Render no 'congele' el bot de Telegram.
    print("🤖 Iniciando Polling de Telegram...")
    bot.infinity_polling(skip_pending=True)




















