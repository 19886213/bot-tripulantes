import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
from flask import Flask
from threading import Thread
import os
import logging

logging.basicConfig(level=logging.INFO)

# --- 1. SERVIDOR WEB ---
app = Flask('')

@app.route('/')
def home():
    return "Bot de Control de Tripulantes: Activo"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- 2. CONFIGURACIÓN DEL BOT Y BASE DE DATOS ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

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

# --- 5. MANEJADOR DE MENSAJES ---
@bot.message_handler(func=lambda msg: True)
def handle_all_messages(message):
    # Intentar buscar por id principal, si no, agarra el primer documento disponible
    doc = coleccion.find_one({"id": "data_principal"}) or coleccion.find_one()
    if not doc:
        bot.reply_to(message, "❌ Error: La colección de MongoDB está completamente vacía.")
        return
    
    personal = doc.get("datos", {})
    text = message.text

    if "Lista General" in text:
        res = "📊 **REPORTE COMPLETO**\n"
        for cat, gente in personal.items():
            res += f"\n┏━━ **{cat}**\n"
            for n, f in gente.items():
                e, d, _ = calcular_vencimiento(f)
                res += f"┃ {e} **{n}**: {d}d (v: {f})\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")

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

    elif "Ayuda" in text:
        ayuda_texto = (
            "❓ **AYUDA Y COMANDOS**\n\n"
            "• Escribe `/vuelo NOMBRE` para actualizar la fecha de alguien a hoy.\n"
            "• Verde (🟢): Menos de 35 días.\n"
            "• Amarillo (🟡): Entre 35 y 44 días.\n"
            "• Rojo (🔴): 45 días o más."
        )
        bot.send_message(message.chat.id, ayuda_texto, parse_mode="Markdown")

# --- 6. COMANDO /VUELO CON ULTRA-DIAGNÓSTICO ---
@bot.message_handler(commands=['vuelo'])
def reset_vuelo(message):
    try:
        argumento = message.text.split(maxsplit=1)
        if len(argumento) < 2:
            bot.reply_to(message, "⚠️ Formato incorrecto. Usa: `/vuelo NOMBRE`", parse_mode="Markdown")
            return
            
        nombre_buscar = argumento[1].strip().upper()
        
        # BÚSQUEDA ROBUSTA: Intenta con ID, si no, toma el primero que encuentre
        doc = coleccion.find_one({"id": "data_principal"})
        if not doc:
            doc = coleccion.find_one() # Plan B: Agarrar cualquier documento
            
        if not doc:
            bot.reply_to(message, "❌ Error fatal: No se encontró ningún documento en tu base de datos.")
            return

        # Extraemos el identificador real del documento para el update
        _id_documento = doc.get("_id")
        id_logico = doc.get("id", "No tiene campo 'id'")
        
        personal = doc.get("datos", {})
        encontrado = False
        categoria_destino = None
        key_original = None

        # Buscar coincidencia
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
            
            # GUARDAR USANDO EL _ID ÚNICO DE MONGODB (Infalible)
            resultado = coleccion.update_one({"_id": _id_documento}, {"$set": {"datos": personal}})
            
            # Mensaje de Diagnóstico de Guardado
            diag = (
                f"📊 **DIAGNÓSTICO DE MONGODB**\n"
                f"• ID del Documento usado: `{id_logico}`\n"
                f"• Documentos coincidentes: {resultado.matched_count}\n"
                f"• Documentos modificados: {resultado.modified_count}\n\n"
            )
            
            if resultado.modified_count > 0 or resultado.matched_count > 0:
                diag += f"✅ **¡FECHA ACTUALIZADA!**\n• `{key_original}` cambiado a **{fecha_hoy}**."
            else:
                diag += "❌ **Error:** MongoDB encontró el registro pero rechazó la escritura (verifica permisos)."
                
            bot.reply_to(message, diag, parse_mode="Markdown")
        else:
            # Si no lo encuentra, te muestra los nombres que sí existen
            todos_los_nombres = []
            for c, t in personal.items():
                todos_los_nombres.extend(t.keys())
            lista = ", ".join([f"`{n}`" for n in todos_los_nombres[:8]])
            
            bot.reply_to(
                message, 
                f"❌ No encontré a '{nombre_buscar}' en la lista.\n\n"
                f"📋 **Nombres que sí existen en tu DB:**\n{lista}",
                parse_mode="Markdown"
            )

    except Exception as e:
        bot.reply_to(message, f"💥 Error interno en comando: `{str(e)}`", parse_mode="Markdown")

# --- 7. EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    keep_alive()
    print("🚀 Servidor Web Flask Activo...")
    print("🤖 Iniciando Polling de Telegram...")
    bot.infinity_polling(skip_pending=True)





















