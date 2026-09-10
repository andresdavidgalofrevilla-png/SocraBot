from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ===== IMPORTAR NUEVA LIBRERÍA =====
try:
    from google import genai
    from google.genai import types
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
]

import time

def generar_respuesta_ia(texto_usuario, intentos=3):
    """Genera respuesta socrática usando Gemini con reintentos"""
    if GEMINI_DISPONIBLE:
        for intento in range(intentos):
            try:
                prompt = PROMPT_SOCRATES.format(texto=texto_usuario)
                response = client.models.generate_content(
                    model='gemini-flash-latest',
                    contents=prompt
                )
                return response.text.strip()
            except Exception as e:
                print(f"⚠️ Intento {intento + 1}/{intentos} falló: {e}")
                if intento < intentos - 1:
                    time.sleep(1.5)  # Esperar 1.5 segundos antes de reintentar
                else:
                    print("❌ Todos los intentos fallaron. Usando fallback.")
                    import random
                    return random.choice(PREGUNTAS_FALLBACK)
    else:
        import random
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
        
        if not texto:
            return jsonify({'error': 'El texto no puede estar vacío'}), 400
        
        respuesta = generar_respuesta_ia(texto)
        
        return jsonify({
            'respuesta': respuesta,
            'tipo': 'ia' if GEMINI_DISPONIBLE else 'fallback'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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