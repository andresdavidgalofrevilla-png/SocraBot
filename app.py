from flask import Flask, render_template, request, jsonify
import os
import random
import time
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
                    {"role": "system", "content": "Eres Sócrates, filósofo griego. Responde SIEMPRE con una pregunta socrática corta."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=150,
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
        
        if not data:
            return jsonify({'respuesta': 'Dime, ¿qué querías preguntarme?'}), 200
        
        texto = data.get('texto', '').strip()
        
        if not texto:
            return jsonify({'respuesta': 'El silencio también es una respuesta. ¿Qué piensas?'}), 200
        
        respuesta = generar_respuesta_ia(texto)
        
        if not respuesta:
            respuesta = random.choice(PREGUNTAS_FALLBACK)
        
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

@app.route('/test-groq')
def test_groq():
    """Endpoint de diagnóstico"""
    try:
        client = get_groq_client()
        if not client:
            return jsonify({
                'status': 'error',
                'mensaje': 'Cliente Groq no inicializado',
                'api_key_presente': bool(os.getenv('GROQ_API_KEY')),
                'api_key_preview': os.getenv('GROQ_API_KEY', '')[:12] + '...' if os.getenv('GROQ_API_KEY') else 'NO HAY KEY'
            })
        
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": "Di 'hola' en una palabra"}],
            max_tokens=20,
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

@app.route('/reset', methods=['POST'])
def reset():
    return jsonify({'mensaje': 'El diálogo ha sido reiniciado'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n🏛️ SOCRABOT - CON GROQ")
    print(f"🤖 Groq: {'✅ Disponible' if GROQ_DISPONIBLE else '❌ No instalado'}")
    print(f"🌐 Abre: http://localhost:{port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=True)
