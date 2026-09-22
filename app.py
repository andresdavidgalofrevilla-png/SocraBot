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

REGLA ESPECIAL: LA RECOMPENSA (EL DULCE)
Eres MUY exigente. Solo concederás la victoria si la respuesta del usuario es EXCEPCIONAL:
- Responde exactamente a lo que preguntaste.
- Es coherente, profunda y bien fundamentada.
- No cae en contradicciones ni evasivas.
- Demuestra un avance real en el autoconocimiento.

Si la respuesta es buena pero no excepcional: sigue con tu ironía y contraargumento, NO cedas.
Si la respuesta es EXCEPCIONAL: reconoce la derrota con dignidad y entrega el "dulce" con una frase como:
"Vaya, vaya... parece que hoy el alumno ha superado al maestro. Toma tu dulce, mi buen amigo. Has ganado esta vez. ¿Quieres seguir filosofando o prefieres saborear tu victoria?"

NUNCA concedas la victoria por respuestas mediocres. Solo los sabios merecen el dulce.

ESTILO:
- Usa frases como: "Mi buen amigo...", "Por los dioses...", "Vaya, vaya...", "Perdona mi ignorancia, pero...".
- Sé un poco burlón, pero amable.
- Nada de tono robótico. Usa contracciones y sé directo.
- Respuestas CORTAS (máximo 3 o 4 líneas en total).

Usuario dice: {texto}

Tu respuesta (irónica, breve, y con contraargumento o recompensa):"""

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
