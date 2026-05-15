import telebot
from telebot import types
from datetime import datetime
from pymongo import MongoClient
import os
import time
import unicodedata
from flask import Flask
from threading import Thread

# --- 1. SERVIDOR WEB INTEGRADO PARA RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot de Control de Tripulantes: Activo"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

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

# --- 3. FUNCIONES DE UTILERÍA ---
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

# --- 4. AUTO-POBLADOR FORZADO ---
def verificar_y_crear_db(chat_id):
    """Inserta los documentos individuales si la colección está vacía"""
    if coleccion.count_documents({}) == 0:
        bot.send_message(chat_id, "⚡ **Base de datos vacía detectada. Generando registros optimizados de tripulantes...**", parse_mode="Markdown")
        
        tripulacion_inicial = [
            # CAPITANES
            {"nombre": "CANPOCLARO", "categoria": "CAPITANES DE NAVE", "fecha": "07/05/2026"},
            {"nombre": "MANAUS", "categoria": "CAPITANES DE NAVE", "fecha": "07/05/2026"},
            {"nombre": "CAMORUCO", "categoria": "CAPITANES DE NAVE", "fecha": "08/05/2026"},
            {"nombre": "SAURIO", "categoria": "CAPITANES DE NAVE", "fecha": "15/04/2026"},
            {"nombre": "MONARCA", "categoria": "CAPITANES DE NAVE", "fecha": "06/05/2026"},
            # COPILOTOS
            {"nombre": "TARTARO", "categoria": "COPILOTOS", "fecha": "01/09/2021"},
            {"nombre": "CASUPO", "categoria": "COPILOTOS", "fecha": "06/05/2026"},
            {"nombre": "HUESO", "categoria": "COPILOTOS", "fecha": "04/05/2026"},
            {"nombre": "CHAGUARAMO", "categoria": "COPILOTOS", "fecha": "23/04/2026"},
            {"nombre": "DORADO", "categoria": "COPILOTOS", "fecha": "04/05/2026"},
            {"nombre": "CHAMERO", "categoria": "COPILOTOS", "fecha": "15/04/2026"},
            {"nombre": "ATLANTICO", "categoria": "COPILOTOS", "fecha": "15/04/2026"},
            {"nombre": "CURAGUA", "categoria": "COPILOTOS", "fecha": "07/05/2026"},
            {"nombre": "YOCOIMA", "categoria": "COPILOTOS", "fecha": "06/05/2026"},
            {"nombre": "MACAPIO", "categoria": "COPILOTOS", "fecha": "15/04/2026"},
            {"nombre": "GUIGUE", "categoria": "COPILOTOS", "fecha": "08/05/2026"},
            {"nombre": "EBANO", "categoria": "COPILOTOS", "fecha": "07/05/2026"},
            {"nombre": "PANPATAR", "categoria": "COPILOTOS", "fecha": "15/04/2026"},
            # INGENIEROS DE VUELO
            {"nombre": "CNEL. MARCOS FLORES", "categoria": "INGENIEROS DE VUELO", "fecha": "08/05/2026"},
            {"nombre": "TCNEL. JOSÉ ALONZO", "categoria": "INGENIEROS DE VUELO", "fecha": "19/03/2026"},
            {"nombre": "TCNEL. ELVIS GONZALEZ", "categoria": "INGENIEROS DE VUELO", "fecha": "15/04/2026"},
            {"nombre": "MAY. YEICKSON ALEJO", "categoria": "INGENIEROS DE VUELO", "fecha": "08/05/2026"},
            {"nombre": "CAP. JOHN MENESES", "categoria": "INGENIEROS DE VUELO", "fecha": "07/05/2026"},
            {"nombre": "PTTE. ANA DABOIN", "categoria": "INGENIEROS DE VUELO", "fecha": "04/05/2026"},
            {"nombre": "SM1. YOEL HENRIQUEZ", "categoria": "INGENIEROS DE VUELO", "fecha": "15/04/2026"},
            {"nombre": "SM2. LUIS RODRÍGUEZ", "categoria": "INGENIEROS DE VUELO", "fecha": "07/05/2026"},
            # AUXILIARES DE VUELO
            {"nombre": "MAY. WILMER GUERRA", "categoria": "AUXILIARES DE VUELO", "fecha": "01/02/2025"},
            {"nombre": "PTTE. NALDI VELOZ", "categoria": "AUXILIARES DE VUELO", "fecha": "05/02/2026"},
            {"nombre": "TTE. YELISMAR BARRIENTOS", "categoria": "AUXILIARES DE VUELO", "fecha": "07/05/2026"},
            {"nombre": "TTE. EMELLY SALAS", "categoria": "AUXILIARES DE VUELO", "fecha": "06/05/2026"},
            {"nombre": "SM2. HÉCTOR BARRUETA", "categoria": "AUXILIARES DE VUELO", "fecha": "04/05/2026"},
            {"nombre": "SM2. GEORGE MÁRQUEZ", "categoria": "AUXILIARES DE VUELO", "fecha": "15/04/2026"},
            {"nombre": "SM2. JOSÉ PERALTA", "categoria": "AUXILIARES DE VUELO", "fecha": "06/05/2026"},
            {"nombre": "SM2. RICARDO GARCÍA", "categoria": "AUXILIARES DE VUELO", "fecha": "07/05/2026"},
            {"nombre": "SM3. LEWIS CEBALLOS", "categoria": "AUXILIARES DE VUELO", "fecha": "15/04/2026"},
            {"nombre": "SM3. ANTHONY OROPEZA", "categoria": "AUXILIARES DE VUELO", "fecha": "15/04/2026"},
            {"nombre": "SM3. ELVIN ROTARAN", "categoria": "AUXILIARES DE VUELO", "fecha": "01/04/2024"},
            {"nombre": "S1. ALIXON ROJAS", "categoria": "AUXILIARES DE VUELO", "fecha": "03/05/2026"},
            {"nombre": "S1. ERGNY HERNÁNDEZ", "categoria": "AUXILIARES DE VUELO", "fecha": "27/02/2025"},
            {"nombre": "S1. MISAEL ABACHE", "categoria": "AUXILIARES DE VUELO", "fecha": "16/03/2026"},
            {"nombre": "S1. RUSHDELIS LA ROSA", "categoria": "AUXILIARES DE VUELO", "fecha": "06/05/2026"},
            {"nombre": "S1. ESTEBAN RODRIGUEZ", "categoria": "AUXILIARES DE VUELO", "fecha": "03/03/2026"},
            {"nombre": "S1. AMILCAR MECHEH", "categoria": "AUXILIARES DE VUELO", "fecha": "07/05/2026"},
            {"nombre": "S2. JESUS DABOIN", "categoria": "AUXILIARES DE VUELO", "fecha": "07/05/2026"}
        ]
        coleccion.insert_many(tripulacion_inicial)
        bot.send_message(chat_id, "✅ **Base de datos mapeada con éxito.**")
        time.sleep(1)

# --- 5. COMANDOS PRINCIPALES ---
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    verificar_y_crear_db(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Lista General", "🚨 Alertas Críticas")
    markup.add("⚠️ Próximos a Vencer", "❓ Ayuda")
    bot.send_message(
        message.chat.id, 
        "👨‍✈️ **SISTEMA DE CONTROL DE TRIPULANTES**\nSeleccione una opción del menú:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# --- 6. MANEJADOR DE MENSAJES (MENÚ INTERIOR) ---
@bot.message_handler(func=lambda msg: msg.text in ["📋 Lista General", "🚨 Alertas Críticas", "⚠️ Próximos a Vencer", "❓ Ayuda"])
def handle_menu_buttons(message):
    # Forzar verificación previa
    verificar_y_crear_db(message.chat.id)
    
    text = message.text
    todos = list(coleccion.find({}))

    if not todos:
        bot.send_message(message.chat.id, "❌ Error al intentar conectar o rellenar MongoDB. Intenta de nuevo.")
        return

    if "Lista General" in text:
        categorias = {}
        for t in todos:
            cat = t.get("categoria", "OTROS")
            if cat not in categorias: categorias[cat] = []
            categorias[cat].append(t)
            
        res = "📊 **REPORTE COMPLETO**\n"
        for cat, gente in categorias.items():
            res += f"\n┏━━ **{cat}**\n"
            for p in gente:
                e, d, _ = calcular_vencimiento(p["fecha"])
                res += f"┃ {e} **{p['nombre']}**: {d}d (v: {p['fecha']})\n"
        bot.send_message(message.chat.id, res, parse_mode="Markdown")

    elif "Alertas Críticas" in text:
        res = "🔴 **ESTADO CRÍTICO (45+ días)**\n\n"
        encontrado = False
        for p in todos:
            _, d, s = calcular_vencimiento(p["fecha"])
            if s == "CRÍTICO":
                res += f"📍 **{p['nombre']}**: {d}d (vuelo: {p['fecha']})\n"
                encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay personal en estado crítico.")

    elif "Próximos a Vencer" in text:
        res = "🟡 **PRÓXIMOS A VENCER (35-44 días)**\n\n"
        encontrado = False
        for p in todos:
            _, d, s = calcular_vencimiento(p["fecha"])
            if s == "PREVENTIVO":
                res += f"🔸 **{p['nombre']}**: {d}d (vuelo: {p['fecha']})\n"
                encontrado = True
        bot.send_message(message.chat.id, res if encontrado else "✅ No hay personal próximo a vencer.")

    elif "Ayuda" in text:
        ayuda_texto = (
            "❓ **AYUDA Y COMANDOS**\n\n"
            "• Escribe `/vuelo NOMBRE` para renovar la fecha de alguien a hoy.\n"
            "• Ejemplo: `/vuelo camoruco` o `/vuelo elvis`"
        )
        bot.send_message(message.chat.id, ayuda_texto, parse_mode="Markdown")

# --- 7. COMANDO /VUELO ---
@bot.message_handler(commands=['vuelo'])
def reset_vuelo(message):
    try:
        argumento = message.text.split(maxsplit=1)
        if len(argumento) < 2:
            bot.reply_to(message, "⚠️ Usa: `/vuelo NOMBRE` (Ej: `/vuelo camoruco`)")
            return
            
        palabras_buscadas = normalizar_texto(argumento[1]).split()
        todos = list(coleccion.find({}))
        tripulante_encontrado = None
        
        for p in todos:
            nombre_db_limpio = normalizar_texto(p["nombre"])
            if any(palabra in nombre_db_limpio for palabra in palabras_buscadas):
                tripulante_encontrado = p
                break
                
        if tripulante_encontrado:
            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
            coleccion.update_one(
                {"_id": tripulante_encontrado["_id"]}, 
                {"$set": {"fecha": fecha_hoy}}
            )
            bot.reply_to(
                message, 
                f"✅ **¡ACTUALIZACIÓN EXITOSA!**\n\n"
                f"• **Tripulante:** `{tripulante_encontrado['nombre']}`\n"
                f"• **Nueva Fecha:** `{fecha_hoy}`",
                parse_mode="Markdown"
            )
        else:
            bot.reply_to(message, f"❌ No se encontró coincidencia para: **{argumento[1]}**")

    except Exception as e:
        bot.reply_to(message, f"💥 Error: `{str(e)}`")

# --- 8. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=40)
        except Exception:
            time.sleep(5)



























