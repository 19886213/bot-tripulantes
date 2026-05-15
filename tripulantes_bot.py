import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
from flask import Flask
from threading import Thread
import os
import time
import unicodedata

# --- 1. SERVIDOR WEB (Estructura base para Render) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot de Control de Tripulantes: Activo"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- 2. CONFIGURACIÓN DEL BOT Y BASE DE DATOS ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Conexión a MongoDB
MONGO_URI = "mongodb+srv://Alejosmv:17954966@alejosmv.ajwv4ej.mongodb.net/?retryWrites=true&w=majority&appName=Alejosmv"
client = MongoClient(MONGO_URI)
db = client['sistema_vuelos']
coleccion = db['tripulantes']

# --- 3. FUNCIONES DE LIMPIEZA Y CÁLCULO ---
def normalizar_texto(texto):
    if not texto: return ""
    texto_limpio = "".join(
        c for c in unicodedata.normalize('NFD', str(texto))
        if unicodedata.category(c) != 'Mn'
    )
    return texto_limpio.strip().upper()

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
    doc = coleccion.find_one({"id": "data_principal\\"}) or coleccion.find_one({"id": "data_principal"}) or coleccion.find_one()
    if not doc:
        bot.reply_to(message, "❌ Error: La colección en MongoDB está vacía.")
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

# --- 6. COMANDO /VUELO CON BÚSQUEDA POR PALABRAS CLAVE ---
@bot.message_handler(commands=['vuelo'])
def reset_vuelo(message):
    try:
        argumento = message.text.split(maxsplit=1)
        
        doc = coleccion.find_one({"id": "data_principal\\"}) or coleccion.find_one({"id": "data_principal"}) or coleccion.find_one()
        if not doc:
            bot.reply_to(message, "❌ Error: No se encontraron documentos en MongoDB.")
            return

        _id_documento = doc.get("_id")
        personal = doc.get("datos", {})

        # Si el usuario no escribe nombre, mandamos botones rápidos
        if len(argumento) < 2:
            markup = types.InlineKeyboardMarkup(row_width=1)
            botones = []
            # Listamos solo los primeros 15 para no saturar Telegram
            contador = 0
            for cat, t in personal.items():
                for nombre_db in t.keys():
                    if contador < 15:
                        botones.append(types.InlineKeyboardButton(text=f"✈️ {nombre_db}", callback_data=f"upd_{nombre_db[:30]}"))
                        contador += 1
            markup.add(*botones)
            bot.reply_to(message, "📋 **Selecciona el tripulante directamente para actualizar:**", reply_markup=markup, parse_mode="Markdown")
            return
            
        # Limpiamos el texto que escribió el usuario y lo separamos en palabras
        palabras_buscadas = normalizar_texto(argumento[1]).split()
        
        encontrado = False
        categoria_destino = None
        key_original = None

        # Búsqueda súper inteligente por palabras sueltas
        for cat, tripulantes in personal.items():
            for nombre_db in tripulantes.keys():
                nombre_db_limpio = normalizar_texto(nombre_db)
                
                # Comprobamos si AL MENOS UNA de las palabras que escribió el usuario está en el nombre de la DB
                if any(p in nombre_db_limpio for p in palabras_buscadas):
                    key_original = nombre_db
                    categoria_destino = cat
                    encontrado = True
                    break
            if encontrado: break
        
        if encontrado:
            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
            personal[categoria_destino][key_original] = fecha_hoy
            
            # Guardamos el cambio directamente por el _id único de MongoDB
            resultado = coleccion.update_one({"_id": _id_documento}, {"$set": {"datos": personal}})
            
            bot.reply_to(
                message, 
                f"✅ **¡ACTUALIZACIÓN EXITOSA!**\n\n"
                f"• **Tripulante:** `{key_original}`\n"
                f"• **Nueva Fecha registrada:** `{fecha_hoy}`\n"
                f"• **Registros modificados:** {resultado.modified_count}",
                parse_mode="Markdown"
            )
        else:
            bot.reply_to(message, f"❌ No encontré a nadie que coincida con **{argumento[1]}**.")

    except Exception as e:
        bot.reply_to(message, f"💥 Error interno en comando: `{str(e)}`")

# --- 7. MANEJADOR DE CLICS EN LOS BOTONES ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('upd_'))
def callback_actualizar_vuelo(call):
    try:
        nombre_limpio_callback = call.data.replace("upd_", "")
        doc = coleccion.find_one({"id": "data_principal\\"}) or coleccion.find_one({"id": "data_principal"}) or coleccion.find_one()
        _id_documento = doc.get("_id")
        personal = doc.get("datos", {})
        
        encontrado = False
        for cat, t in personal.items():
            for nombre_db in t.keys():
                if nombre_db.startswith(nombre_limpio_callback) or nombre_limpio_callback in nombre_db:
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                    personal[cat][nombre_db] = fecha_hoy
                    encontrado = True
                    key_original = nombre_db
                    break
            if encontrado: break
            
        if encontrado:
            coleccion.update_one({"_id": _id_documento}, {"$set": {"datos": personal}})
            bot.answer_callback_query(call.id, text=f"Actualizado: {key_original}")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ **¡ACTUALIZACIÓN EXITOSA!**\n\n• **Tripulante:** `{key_original}`\n• **Nueva Fecha:** `{fecha_hoy}`",
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, text="Error al procesar el nombre.")
    except Exception as e:
        print(f"Error en callback: {e}")

# --- 8. BUCLE CONTINUO DE EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            time.sleep(5)
























