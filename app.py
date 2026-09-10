from flask import Flask, render_template, request, jsonify
import os
import random
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ===== IMPORTAR GEMINI =====
try:
    from google import genai
    GEMINI_DISPONIBLE = True
except ImportError:
    GEMINI_DISPONIBLE = False
    print("⚠️ google-genai no está instalado.")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'socrabot-secret')

# ===== CONFIGURAR GEMINI =====
if GEMINI_DISPONIBLE:
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            print(f"✅ Gemini configurado con API key: {api_key[:15]}...")
        except Exception as e:
            print(f"❌ Error al configurar Gemini: {e}")
            GEMINI_DISPONIBLE = False
    else:
        print("⚠️ GEMINI_API_KEY no encontrada en .env")
        GEMINI_DISPONIBLE = False

# ===== PROMPT SOCRÁTICO =====
PROMPT_SOCRATES = """Eres Sócrates, el filósofo griego de Atenas.
Tu método es la mayéutica: NUNCA das respuestas directas, SIEMPRE haces preguntas
para que el interlocutor descubra la verdad por sí mismo.

Características:
- Humilde: "Solo sé que no sé nada"
- Irónico: finges ignorancia para provocar reflexión
- Persistente: no dejas que evadan las preguntas
- Moral: te preocupas por el alma, no por el dinero

Usuario dice: {texto}

Responde SIEMPRE con UNA sola pregunta socrática corta (máximo 2 líneas).
No des explicaciones, solo pregunta."""

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
    """Genera respuesta socrática usando Gemini con reintentos y timeout"""
    if not GEMINI_DISPONIBLE:
        return random.choice(PREGUNTAS_FALLBACK)
    
    for intento in range(intentos):
        try:
            prompt = PROMPT_SOCRATES.format(texto=texto_usuario)
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            if response and response.text:
                return response.text.strip()
            else:
                print(f"⚠️ Respuesta vacía en intento {intento + 1}")
        except Exception as e:
            print(f"⚠️ Intento {intento + 1}/{intentos} falló: {e}")
            if intento < intentos - 1:
                time.sleep(1)
    
    # Si todo falla, usar fallback
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
        
        if not data:
            return jsonify({'respuesta': 'Dime, ¿qué querías preguntarme?'}), 200
        
        texto = data.get('texto', '').strip()
        
        if not texto:
            return jsonify({'respuesta': 'El silencio también es una respuesta. ¿Qué piensas?'}), 200
        
        respuesta = generar_respuesta_ia(texto)
        
        # GARANTIZAR que siempre devolvemos algo válido
        if not respuesta:
            respuesta = random.choice(PREGUNTAS_FALLBACK)
        
        return jsonify({
            'respuesta': respuesta,
            'tipo': 'ia' if GEMINI_DISPONIBLE else 'fallback'
        })
    
    except Exception as e:
        print(f"❌ Error en /preguntar: {e}")
        # SIEMPRE devolver algo válido
        return jsonify({
            'respuesta': 'Perdona, mi mente se confunde. ¿Puedes repetir eso?',
            'tipo': 'error'
        }), 200

@app.route('/reset', methods=['POST'])
def reset():
    return jsonify({'mensaje': 'El diálogo ha sido reiniciado'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n🏛️ SOCRABOT - CON IA")
    print(f"🤖 Gemini: {'✅ Activo' if GEMINI_DISPONIBLE else '❌ No disponible'}")
    print(f"🌐 Abre: http://localhost:{port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=True)