// ========================================
// SOCRABOT - JAVASCRIPT COMPLETO
// ========================================

const CONFIG = {
    API_URL: '/preguntar',
    RESET_URL: '/reset',
    TYPING_DELAY_MIN: 600,
    TYPING_DELAY_MAX: 1200,
};

let historialConversacion = [];
let esperandoRespuesta = false;

const DOM = {
    chatBox: document.getElementById('chat'),
    userInput: document.getElementById('userInput'),
    sendButton: document.getElementById('sendButton'),
};

// ===== FUNCIÓN PRINCIPAL =====
async function dialogar() {
    if (esperandoRespuesta) return;
    
    const texto = DOM.userInput.value.trim();
    
    if (!texto) {
        DOM.userInput.style.borderColor = '#c0392b';
        setTimeout(() => DOM.userInput.style.borderColor = '', 1000);
        return;
    }

    DOM.userInput.value = '';
    DOM.userInput.focus();
    esperandoRespuesta = true;
    DOM.sendButton.disabled = true;

    agregarMensaje(texto, 'user');
    historialConversacion.push({ rol: 'usuario', texto: texto });

    const typingId = mostrarIndicadorEscritura();

    try {
        const response = await fetch(CONFIG.API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                texto: texto,
                historial: historialConversacion.slice(-5)
            })
        });

        const data = await response.json();
        ocultarIndicadorEscritura(typingId);

        if (data.error) {
            agregarMensaje(`⚠️ Error: ${data.error}`, 'socrates');
        } else {
            const delay = Math.random() * (CONFIG.TYPING_DELAY_MAX - CONFIG.TYPING_DELAY_MIN) + CONFIG.TYPING_DELAY_MIN;
            setTimeout(() => {
                agregarMensaje(data.respuesta, 'socrates');
                historialConversacion.push({ rol: 'socrates', texto: data.respuesta });
                esperandoRespuesta = false;
                DOM.sendButton.disabled = false;
            }, delay);
        }

    } catch (error) {
        ocultarIndicadorEscritura(typingId);
        agregarMensaje(`⚠️ Error de conexión: ${error.message}`, 'socrates');
        esperandoRespuesta = false;
        DOM.sendButton.disabled = false;
    }
}

// ===== AGREGAR MENSAJES =====
function agregarMensaje(texto, tipo, opciones = {}) {
    const div = document.createElement('div');
    div.className = `message ${tipo} fade-in`;
    
    const textoFormateado = texto.replace(/\n/g, '<br>');
    
    if (tipo === 'socrates') {
        div.innerHTML = `${textoFormateado} <span class="socrates-label">— Sócrates</span>`;
    } else if (tipo === 'system') {
        div.textContent = texto;
    } else {
        div.textContent = texto;
    }
    
    if (opciones.id) div.id = opciones.id;
    if (opciones.className) div.classList.add(opciones.className);
    
    DOM.chatBox.appendChild(div);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    return div;
}

// ===== INDICADOR DE ESCRITURA =====
function mostrarIndicadorEscritura() {
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message socrates typing-indicator';
    
    const frases = [
        '🤔 Sócrates está reflexionando...',
        '🧠 Sócrates está pensando en su próxima pregunta...',
        '💭 Sócrates está meditando...',
        '📚 Sócrates está consultando su sabiduría...'
    ];
    div.textContent = frases[Math.floor(Math.random() * frases.length)];
    
    DOM.chatBox.appendChild(div);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    return id;
}

function ocultarIndicadorEscritura(id) {
    const indicator = document.getElementById(id);
    if (indicator) indicator.remove();
}

// ===== LIMPIAR CHAT =====
function limpiarChat() {
    if (historialConversacion.length > 0 && !confirm('¿Seguro que quieres limpiar el diálogo?')) {
        return;
    }
    
    DOM.chatBox.innerHTML = '';
    historialConversacion = [];
    
    agregarMensaje(
        'El diálogo se renueva. Como el río, el pensamiento fluye constantemente.\n\n¿Qué nueva pregunta te gustaría explorar?',
        'socrates'
    );
    
    try {
        fetch(CONFIG.RESET_URL, { method: 'POST' });
    } catch (e) {}
}

// ===== EJEMPLOS =====
function ejemploFilosofico() {
    const ejemplos = [
        "¿Qué es la felicidad y cómo se alcanza?",
        "¿El conocimiento verdadero viene de la razón o de la experiencia?",
        "¿Qué significa ser una buena persona?",
        "¿Cómo sabemos lo que es real?",
        "¿El amor es un sentimiento o una elección?",
        "¿Qué es la justicia y cómo se aplica?",
        "¿Qué papel juega la libertad en nuestra vida?",
        "¿El ser humano es bueno por naturaleza?",
        "¿Qué es la belleza y dónde se encuentra?",
        "¿Cuál es el sentido de la existencia?"
    ];
    DOM.userInput.value = ejemplos[Math.floor(Math.random() * ejemplos.length)];
    DOM.userInput.focus();
    setTimeout(dialogar, 300);
}

function ejemploDuda() {
    const dudas = [
        "¿Cómo puedo estar seguro de lo que sé?",
        "¿Por qué tememos tanto a la incertidumbre?",
        "¿Qué es lo que realmente importa en la vida?",
        "¿Cómo distinguir lo verdadero de lo falso?",
        "¿Por qué es tan difícil conocerse a uno mismo?",
        "¿Qué hay después de la muerte?",
        "¿Por qué existe el sufrimiento?",
        "¿Qué es la conciencia y cómo funciona?",
        "¿Cómo sé que no estoy soñando?",
        "¿Qué es la libertad y cómo se conquista?"
    ];
    DOM.userInput.value = dudas[Math.floor(Math.random() * dudas.length)];
    DOM.userInput.focus();
    setTimeout(dialogar, 300);
}
