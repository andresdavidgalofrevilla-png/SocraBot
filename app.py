from flask import Flask, render_template, request, jsonify
import random
import os
from collections import deque

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-para-socrabot'

# ===== MEMORIA =====
historial_preguntas = deque(maxlen=10)
historial_usuario = deque(maxlen=20)
turnos = 0
frases_usadas = deque(maxlen=8)
dialogo_activo = True

# ===== PREGUNTAS SOCRÁTICAS Y EVALUACIONES =====
PREGUNTAS_SOCRATICAS = {
    'virtud': {
        'pregunta': "¿Qué es la virtud para ti? No me des ejemplos, dame la esencia.",
        'evaluacion_buena': "Has dado una definición esencial. La virtud es el conocimiento del bien. Pero dime, ¿el conocimiento se puede enseñar?",
        'evaluacion_mala': "Has dado ejemplos, no la esencia. La virtud no es una lista de acciones, es el conocimiento de lo que es bueno. ¿Qué es el bien en sí mismo?",
        'pistas': ["La virtud es conocimiento", "¿Qué tienen en común todas las acciones virtuosas?"]
    },
    'justicia': {
        'pregunta': "¿Crees que eso es justo? ¿Por qué?",
        'evaluacion_buena': "Bien, estás buscando el fundamento de la justicia. La justicia es dar a cada uno lo que merece. Pero ¿quién decide lo que merece cada uno?",
        'evaluacion_mala': "Estás confundiendo justicia con ley o costumbre. La justicia es una virtud del alma. ¿Qué pasaría si las leyes fueran injustas?",
        'pistas': ["La justicia es armonía", "¿Qué es lo justo en sí mismo?"]
    },
    'bien': {
        'pregunta': "Si te preguntara qué es el bien, ¿qué me responderías?",
        'evaluacion_buena': "Has identificado el bien con lo que es bueno para todos. El bien es aquello que perfecciona al ser humano. ¿Qué te perfecciona a ti?",
        'evaluacion_mala': "Has confundido el bien con lo que es útil o placentero. El bien es lo que es bueno en sí mismo, no por sus consecuencias.",
        'pistas': ["El bien es la excelencia", "¿Qué es bueno siempre?"]
    },
    'amor': {
        'pregunta': "¿Qué es el amor? ¿Cómo lo reconoces en tu vida?",
        'evaluacion_buena': "Has descrito el amor en su esencia. El amor es deseo de belleza y bien. ¿Qué belleza buscas en quien amas?",
        'evaluacion_mala': "Has confundido el amor con el deseo o la pasión. El amor es desear el bien del otro. ¿Deseas el bien de los que amas?",
        'pistas': ["El amor busca la belleza", "¿Qué es el amor en sí mismo?"]
    },
    'libertad': {
        'pregunta': "¿Qué significa ser libre? ¿No estás esclavizado por tus deseos?",
        'evaluacion_buena': "Has comprendido que la libertad no es hacer lo que se quiere. La libertad es dominio de uno mismo. ¿Eres dueño de tus deseos?",
        'evaluacion_mala': "Has confundido libertad con libertinaje. La verdadera libertad es la capacidad de elegir el bien. ¿Eliges siempre el bien?",
        'pistas': ["La libertad es autodominio", "¿Eres esclavo de tus pasiones?"]
    },
    'felicidad': {
        'pregunta': "¿Qué es la felicidad? ¿Acaso no la confundes con el placer?",
        'evaluacion_buena': "Bien, has distinguido felicidad de placer. La felicidad es la actividad del alma conforme a la virtud. ¿Vives de acuerdo a la virtud?",
        'evaluacion_mala': "Has confundido felicidad con placer. La felicidad no es un estado pasajero, es la excelencia del alma. ¿Qué te hace excelente?",
        'pistas': ["La felicidad es virtud", "¿El placer es siempre bueno?"]
    },
    'conocimiento': {
        'pregunta': "¿Cómo sabes que eso es verdad? ¿Qué fundamento tiene?",
        'evaluacion_buena': "Has buscado un fundamento sólido. El conocimiento verdadero se basa en razones. ¿Puedes dar razones de todo lo que sabes?",
        'evaluacion_mala': "Has aceptado algo sin cuestionarlo. El conocimiento requiere justificación. ¿Cómo justificas lo que crees?",
        'pistas': ["El conocimiento es creencia verdadera justificada", "¿Por qué crees eso?"]
    }
}

# ===== RESPUESTAS SOCRÁTICAS BÁSICAS =====
SOCRATES_BASICO = {
    'saludo': [
        "Hola, amigo. Dime, ¿qué te preocupa hoy?",
        "Saludos, caminante. ¿Has venido a examinar tu alma?",
        "Bienvenido. No tengo riquezas ni honores, solo preguntas. ¿Qué buscas?",
        "Hola, conciudadano. ¿Qué te trae a este diálogo?"
    ],
    'frustracion': [
        "Veo que te enfadas. Pero dime, ¿por qué te enfadas? ¿No estás aprendiendo?",
        "La frustración es el inicio del aprendizaje. ¿Qué has descubierto de ti mismo?",
        "Sócrates también enfadaba a Atenas. ¿Qué te enfada de mis preguntas?",
        "El diálogo incomoda porque te hace pensar. ¿Qué pensamientos incómodos tienes?"
    ],
    'aporia': [
        "Reconocer que no sabes es el principio de la sabiduría.",
        "Has llegado a la aporía. Ahora sí podemos empezar a filosofar.",
        "No saber es humano. ¿Qué te gustaría descubrir ahora?",
        "La duda es el comienzo del conocimiento. ¿Qué preguntas te surgen?"
    ],
    'despedida': [
        "Cuida tu alma más que tu cuerpo. Hasta luego.",
        "El diálogo termina, pero la búsqueda continúa.",
        "Examínate a ti mismo, que es la tarea más importante.",
        "Sigue buscando, sigue dudando. Solo así encontrarás la verdad."
    ]
}

def analizar_calidad_respuesta(texto, tema):
    """Analiza si la respuesta del usuario es buena o mala según el tema socrático"""
    texto_lower = texto.lower()
    
    # Palabras clave para evaluar respuestas
    buena_virtud = ['esencia', 'conocimiento', 'alma', 'bien', 'excelencia']
    mala_virtud = ['ejemplo', 'acción', 'hacer', 'comportamiento']
    
    buena_justicia = ['merece', 'armonía', 'virtud', 'equilibrio']
    mala_justicia = ['ley', 'costumbre', 'norma', 'regla']
    
    buena_bien = ['perfecciona', 'excelencia', 'virtud', 'alma']
    mala_bien = ['útil', 'placer', 'conveniente', 'agradable']
    
    buena_amor = ['bien del otro', 'desear el bien', 'belleza', 'esencia']
    mala_amor = ['pasión', 'deseo', 'atracción', 'sentimiento']
    
    buena_libertad = ['autodominio', 'dominio propio', 'virtud', 'razón']
    mala_libertad = ['hacer lo que quiero', 'libertinaje', 'deseos', 'impulsos']
    
    buena_felicidad = ['virtud', 'alma', 'excelencia', 'razón']
    mala_felicidad = ['placer', 'dinero', 'éxito', 'reconocimiento']
    
    buena_conocimiento = ['justificación', 'razón', 'evidencia', 'fundamento']
    mala_conocimiento = ['creo', 'siento', 'intuición', 'confianza']
    
    # Mapeo de temas a evaluaciones
    evaluaciones = {
        'virtud': (buena_virtud, mala_virtud, 'virtud'),
        'justicia': (buena_justicia, mala_justicia, 'justicia'),
        'bien': (buena_bien, mala_bien, 'bien'),
        'amor': (buena_amor, mala_amor, 'amor'),
        'libertad': (buena_libertad, mala_libertad, 'libertad'),
        'felicidad': (buena_felicidad, mala_felicidad, 'felicidad'),
        'conocimiento': (buena_conocimiento, mala_conocimiento, 'conocimiento')
    }
    
    if tema in evaluaciones:
        buenas, malas, clave = evaluaciones[tema]
        
        # Contar coincidencias
        coincidencias_buenas = sum(1 for p in buenas if p in texto_lower)
        coincidencias_malas = sum(1 for p in malas if p in texto_lower)
        
        # Si tiene más palabras clave buenas que malas
        if coincidencias_buenas > coincidencias_malas and len(texto.split()) > 3:
            return 'buena'
        elif coincidencias_malas > coincidencias_buenas:
            return 'mala'
        else:
            return 'neutral'
    
    return 'neutral'

def detectar_tema_pregunta(pregunta):
    """Detecta de qué tema socrático se trata la pregunta"""
    temas = {
        'virtud': ['virtud', 'virtuoso'],
        'justicia': ['justicia', 'justo'],
        'bien': ['bien', 'bueno'],
        'amor': ['amor', 'amar'],
        'libertad': ['libertad', 'libre'],
        'felicidad': ['felicidad', 'feliz'],
        'conocimiento': ['verdad', 'saber', 'conocimiento']
    }
    
    for tema, palabras in temas.items():
        if any(p in pregunta.lower() for p in palabras):
            return tema
    return None

def generar_respuesta_socratica(texto_usuario, ultima_pregunta_socrates):
    """Genera respuesta evaluando la respuesta del usuario"""
    global turnos
    
    # Si el usuario dice "no sé" o similar
    if any(ns in texto_usuario.lower() for ns in ['no sé', 'no se', 'ns', 'tampoco']):
        return random.choice(SOCRATES_BASICO['aporia'])
    
    # Detectar frustración
    frustracion = ['hijo de puta', 'mierda', 'pinche', 'puedes deepsek', 'mrd']
    if any(f in texto_usuario.lower() for f in frustracion):
        return "Veo que estás frustrado. Pero dime: ¿qué te ha hecho enfadar? ¿No estás aprendiendo algo sobre ti mismo? El diálogo verdadero incomoda. ¿Qué incomodidad sientes?"
    
    # Si hay una pregunta anterior, evaluar la respuesta
    if ultima_pregunta_socrates:
        tema = detectar_tema_pregunta(ultima_pregunta_socrates)
        if tema:
            calidad = analizar_calidad_respuesta(texto_usuario, tema)
            
            # Obtener evaluaciones del tema
            if tema in PREGUNTAS_SOCRATICAS:
                info = PREGUNTAS_SOCRATICAS[tema]
                if calidad == 'buena':
                    return info['evaluacion_buena']
                elif calidad == 'mala':
                    return info['evaluacion_mala']
                else:
                    return info['evaluacion_buena']  # Por defecto, dar el beneficio de la duda
    
    # Si no hay evaluación específica, hacer una pregunta nueva
    return hacer_pregunta_socratica()

def hacer_pregunta_socratica():
    """Elige una pregunta socrática para hacer"""
    temas = list(PREGUNTAS_SOCRATICAS.keys())
    tema = random.choice(temas)
    return PREGUNTAS_SOCRATICAS[tema]['pregunta']

# ===== VARIABLES DE ESTADO =====
ultima_pregunta_socrates = None

# ===== RUTAS =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preguntar', methods=['POST'])
def preguntar():
    global turnos, ultima_pregunta_socrates
    
    try:
        data = request.get_json()
        texto_usuario = data.get('texto', '').strip()
        
        if not texto_usuario:
            return jsonify({'error': 'El texto no puede estar vacío'}), 400
        
        turnos += 1
        
        # Detectar si es un saludo
        if any(s in texto_usuario.lower() for s in ['hola', 'buenas', 'saludos', 'hey']):
            respuesta = random.choice(SOCRATES_BASICO['saludo'])
            ultima_pregunta_socrates = None
        else:
            # Generar respuesta evaluativa
            respuesta = generar_respuesta_socratica(texto_usuario, ultima_pregunta_socrates)
            ultima_pregunta_socrates = respuesta  # Guardar la pregunta que hicimos
        
        return jsonify({
            'respuesta': respuesta,
            'turnos': turnos
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    global turnos, ultima_pregunta_socrates, historial_usuario
    turnos = 0
    ultima_pregunta_socrates = None
    historial_usuario.clear()
    return jsonify({'mensaje': 'El diálogo ha sido reiniciado'})

if __name__ == '__main__':
    print("\n🏛️ SOCRABOT - VERSIÓN EVALUADOR")
    print("🧠 Evalúa tus respuestas y te dice si están bien o mal")
    print("🌐 Abre: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Render usa el puerto de entorno, o 5000 por defecto
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)