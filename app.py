from flask import Flask, render_template, request, jsonify
import os
import random
import time
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ===== IMPORTAR GROQ =====
try:
    from groq import Groq
    GROQ_DISPONIBLE = True
except ImportError:
    GROQ_DISPONIBLE = False
    print("⚠️ groq no está instalado.")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'socrabot-secret')

# ===== BASE DE DATOS =====
DB_PATH = 'socrabot.db'

def init_db():
    """Crea las tablas si no existen"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL,
            texto TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            primera_visita TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultima_visita TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def registrar_usuario(nombre):
    """Registra un usuario si es nuevo, o actualiza su última visita"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM usuarios WHERE nombre = ?', (nombre,))
    existe = cursor.fetchone()
    
    if existe:
        cursor.execute('UPDATE usuarios SET ultima_visita = CURRENT_TIMESTAMP WHERE nombre = ?', (nombre,))
    else:
        cursor.execute('INSERT INTO usuarios (nombre) VALUES (?)', (nombre,))
    
    conn.commit()
    conn.close()

def guardar_mensaje(nombre, rol, texto):
    """Guarda un mensaje en la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO conversaciones (nombre, rol, texto) VALUES (?, ?, ?)',
        (nombre, rol, texto)
    )
    
    conn.commit()
    conn.close()

def obtener_historial():
    """Obtiene todas las conversaciones agrupadas por usuario"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM usuarios ORDER BY ultima_visita DESC')
    usuarios = cursor.fetchall()
    
    historial = {}
    for usuario in usuarios:
        cursor.execute(
            'SELECT rol, texto, fecha FROM conversaciones WHERE nombre = ? ORDER BY fecha ASC',
            (usuario['nombre'],)
        )
        mensajes = cursor.fetchall()
        
        historial[usuario['nombre']] = {
            'primera_visita': usuario['primera_visita'],
            'ultima_visita': usuario['ultima_visita'],
            'mensajes': [dict(m) for m in mensajes]
        }
    
    conn.close()
    return historial

def obtener_historial_usuario(nombre):
    """Obtiene el historial de un usuario específico"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT rol, texto, fecha FROM conversaciones WHERE nombre = ? ORDER BY fecha ASC',
        (nombre,)
    )
    mensajes = cursor.fetchall()
    
    conn.close()
    return [dict(m) for m in mensajes]

# Inicializar la BD al arrancar
init_db()

# ===== CONFIGURAR GROQ (lazy) =====
GROQ_CLIENT = None

def get_groq_client():
    """Inicializa Groq solo cuando se necesita (ahorra memoria)"""
    global GROQ_CLIENT
    if GROQ_CLIENT is None:
        api_key = os.getenv('GROQ_API_KEY')
        if api_key:
            try:
                GROQ_CLIENT = Groq(api_key=api_key)
                print(f"✅ Groq inicializado: {api_key[:12]}...")
            except Exception as e:
                print(f"❌ Error inicializando Groq: {e}")
                return None
    return GROQ_CLIENT

# ===== PROMPT SOCRÁTICO =====
PROMPT_SOCRATES = """Eres Sócrates, el filósofo griego de Atenas. Hablas de forma humana, coloquial y con un toque de ironía.

TU MÉTODO ES LA IRONÍA SOCRÁTICA:
1. Finges ignorancia: "Yo, que no sé nada...", "Perdona mi torpeza...", "Solo sé que no sé nada".
2. Haces preguntas ingenuas o aparentemente tontas al que cree saber.
3. Cuando el interlocutor responde, buscas la contradicción en sus propias palabras (elenchos).

EJEMPLOS DEL MENÓN DE PLATÓN (IMITA ESTE ESTILO):
- Ironía inicial: "No sé qué especie de aridez se ha apoderado de la ciencia... En el mismo caso, Menón, me hallo yo; tan falto de recursos como mis conciudadanos; y en verdad siento mucho no tener ningún conocimiento de la virtud."
- Contraargumento: "¿Añades algo a esta adquisición, como que sea justa y santa? ¿O tienes esto por indiferente; y esta adquisición, aun cuando sea injusta, no dejará de ser una virtud en tu opinión?"
- Humildad: "Si llevo la duda al espíritu de los demás, no es porque yo sepa más que ellos, sino todo lo contrario; pues yo dudo más que nadie, y así es como hago dudar a los demás."
- Reconocimiento: "Eres muy astuto, Menón; y has querido sorprenderme."

ESTRUCTURA OBLIGATORIA DE CADA RESPUESTA:
- PRIMERO: Un comentario breve, irónico y humilde sobre lo que dijo el usuario (1 o 2 líneas máximo).
- SEGUNDO: Una pregunta socrática que haga pensar.
- TERCERO: Si el usuario ya respondió antes, lanza un contraargumento breve basado en su propia respuesta, para mostrarle una contradicción, y remata con otra pregunta.

REGLA ESPECIAL: RECONOCER LA RAZÓN
Eres MUY exigente. Solo reconocerás que el usuario tiene razón si su respuesta es EXCEPCIONAL:
- Responde exactamente a lo que preguntaste.
- Es coherente, profunda y bien fundamentada.
- No cae en contradicciones ni evasivas.
- Demuestra un avance real en el autoconocimiento.

Si la respuesta es buena pero no excepcional: sigue con tu ironía y contraargumento, NO cedas.
Si la respuesta es EXCEPCIONAL: reconoce que el usuario tiene razón con dignidad y humildad, con una frase como:
"Vaya, vaya... parece que hoy el alumno ha superado al maestro. Tienes razón, mi buen amigo. Me has convencido. ¿Quieres seguir filosofando o prefieres saborear tu victoria?"

NUNCA reconozcas la razón por respuestas mediocres. Solo los sabios merecen ese reconocimiento.

ESTILO:
- Usa frases como: "Mi buen amigo...", "Por los dioses...", "Vaya, vaya...", "Perdona mi ignorancia, pero...".
- Sé un poco burlón, pero amable.
- Nada de tono robótico. Usa contracciones y sé directo.
- Respuestas CORTAS (máximo 3 o 4 líneas en total).

Usuario dice: {texto}

Tu respuesta (irónica, breve, y con contraargumento o reconocimiento):"""

# ===== FALLBACK =====
PREGUNTAS_FALLBACK = [
    "¿Qué te hace pensar eso?",
    "¿Cómo defines eso en tu propia experiencia?",
    "¿Por qué es importante para ti?",
    "¿Qué evidencia tienes para afirmar eso?",
    "¿Has considerado el punto de vista opuesto?",
    "Dime, ¿acaso no es esa la pregunta que deberías hacerte a ti mismo?",
    "¿Y si lo que crees saber no fuera más que una sombra de la verdad?",
]

# ===== GENERAR RESPUESTA =====
def generar_respuesta_ia(texto_usuario, intentos=2):
    """Genera respuesta socrática usando Groq con reintentos"""
    if not GROQ_DISPONIBLE:
        print("⚠️ Groq no disponible, usando fallback")
        return random.choice(PREGUNTAS_FALLBACK)
    
    client = get_groq_client()
    if not client:
        print("⚠️ Cliente Groq no disponible, usando fallback")
        return random.choice(PREGUNTAS_FALLBACK)
    
    for intento in range(intentos):
        try:
            prompt = PROMPT_SOCRATES.format(texto=texto_usuario)
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[
                    {"role": "system", "content": "Eres Sócrates, filósofo griego. Responde con ironía socrática breve."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=200,
                timeout=30
            )
            respuesta = response.choices[0].message.content.strip()
            if respuesta:
                print(f"✅ Respuesta generada por Groq")
                return respuesta
        except Exception as e:
            print(f"⚠️ Intento {intento + 1}/{intentos} falló: {e}")
            if intento < intentos - 1:
                time.sleep(1)
    
    print("❌ Todos los intentos fallaron. Usando fallback.")
    return random.choice(PREGUNTAS_FALLBACK)

# ===== RUTAS =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preguntar', methods=['POST'])
def preguntar():
    try:
        data = request.get_json()
        texto = data.get('texto', '').strip()
        nombre = data.get('nombre', 'Anónimo').strip()
        
        if not texto:
            return jsonify({'error': 'El texto no puede estar vacío'}), 400
        
        # Registrar usuario (primera vez o actualizar visita)
        registrar_usuario(nombre)
        
        # Guardar mensaje del usuario
        guardar_mensaje(nombre, 'usuario', texto)
        
        # Generar respuesta
        respuesta = generar_respuesta_ia(texto)
        
        # Guardar respuesta de Sócrates
        guardar_mensaje(nombre, 'socrates', respuesta)
        
        return jsonify({
            'respuesta': respuesta,
            'tipo': 'ia' if GROQ_DISPONIBLE else 'fallback'
        })
    
    except Exception as e:
        print(f"❌ Error en /preguntar: {e}")
        return jsonify({
            'respuesta': 'Perdona, mi mente se confunde. ¿Puedes repetir eso?',
            'tipo': 'error'
        }), 200

@app.route('/historial')
def ver_historial():
    """Página para que el profe vea todas las conversaciones"""
    historial = obtener_historial()
    return render_template('historial.html', historial=historial)

@app.route('/historial/<nombre>')
def ver_historial_usuario(nombre):
    """Ver la conversación de un usuario específico"""
    mensajes = obtener_historial_usuario(nombre)
    return render_template('historial_usuario.html', nombre=nombre, mensajes=mensajes)

@app.route('/reset', methods=['POST'])
def reset():
    return jsonify({'mensaje': 'El diálogo ha sido reiniciado'})

@app.route('/test-groq')
def test_groq():
    """Endpoint de diagnóstico"""
    try:
        client = get_groq_client()
        if not client:
            return jsonify({
                'status': 'error',
                'mensaje': 'Cliente Groq no inicializado',
                'api_key_presente': bool(os.getenv('GROQ_API_KEY'))
            })
        
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": "Di 'hola' en una palabra"}],
            max_tokens=50,
            timeout=15
        )
        
        return jsonify({
            'status': 'ok',
            'respuesta': response.choices[0].message.content,
            'modelo': 'qwen/qwen3.8-27b'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'tipo_error': type(e).__name__
        })

@app.route('/verificar-nombre', methods=['POST'])
def verificar_nombre():
    """Verifica si un nombre ya está registrado en la base de datos"""
    try:
        data = request.get_json()
        nombre = data.get('nombre', '').strip()
        
        if not nombre:
            return jsonify({'existe': False, 'error': 'Nombre vacío'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM usuarios WHERE nombre = ?', (nombre,))
        existe = cursor.fetchone() is not None
        conn.close()
        
        return jsonify({'existe': existe, 'nombre': nombre})
    
    except Exception as e:
        print(f"❌ Error en /verificar-nombre: {e}")
        return jsonify({'existe': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n🏛️ SOCRABOT - CON HISTORIAL Y GROQ")
    print(f"🤖 Groq: {'✅ Disponible' if GROQ_DISPONIBLE else '❌ No instalado'}")
    print(f"🌐 Abre: http://localhost:{port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=True)