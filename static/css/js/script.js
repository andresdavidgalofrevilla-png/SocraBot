// ========================================
// SOCRABOT - VERSIÓN AVANZADA
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
                // Si el usuario está haciendo preguntas, cambiar estilo de respuesta
                if (data.usuario_pregunta && data.turnos > 5) {
                    agregarMensaje('🌟 ' + data.respuesta, 'socrates');
                } else {
                    agregarMensaje(data.respuesta, 'socrates');
                }
                
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

// ===== FUNCIONES DE INTERFAZ =====

function agregarMensaje(texto, tipo, opciones = {}) {
    const div = document.createElement('div');
    div.className = `message ${tipo} fade-in`;
    
    const textoFormateado = texto.replace(/\n/g, '<br>');
    
    if (tipo === 'socrates') {
        // Detectar si es un mensaje de celebración (empieza con 🌟)
        if (texto.startsWith('🌟')) {
            div.innerHTML = `
                <div style="background: linear-gradient(135deg, #f9f3e8, #f0e8df); padding: 16px; border-radius: 12px; border-left: 4px solid #f39c12;">
                    ${textoFormateado}
                </div>
                <span class="socrates-label">— Sócrates</span>
            `;
        } else {
            div.innerHTML = `${textoFormateado} <span class="socrates-label">— Sócrates</span>`;
        }
    } else {
        div.textContent = texto;
    }
    
    if (opciones.id) div.id = opciones.id;
    if (opciones.className) div.classList.add(opciones.className);
    
    DOM.chatBox.appendChild(div);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    return div;
}

function mostrarIndicadorEscritura() {
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message socrates typing-indicator';
    
    // Textos alternativos para el indicador
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

function cambiarEnfoque() {
    const temas = [
        "Hablemos de la verdad",
        "¿Qué piensas sobre la justicia?",
        "Exploremos el concepto de amor",
        "¿Qué es la libertad para ti?",
        "Hablemos de la muerte",
        "¿Qué significa ser feliz?",
        "¿Qué es el conocimiento?",
        "¿Existe el destino?"
    ];
    DOM.userInput.value = temas[Math.floor(Math.random() * temas.length)];
    DOM.userInput.focus();
    setTimeout(dialogar, 300);
}

function ejemploFilosofico() {
    const ejemplos = [
        "¿Qué es la felicidad y cómo se alcanza?",
        "¿El conocimiento verdadero viene de la razón o de la experiencia?",
        "¿Qué significa ser una buena persona?",
        "¿Cómo sabemos lo que es real?",
        "¿El amor es un sentimiento o una elección?",
        "¿Qué es la justicia y cómo se aplica?",
        "¿Qué papel juega la libertad en nuestra vida?"
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
        "¿Por qué es tan difícil conocerse a uno mismo?"
    ];
    DOM.userInput.value = dudas[Math.floor(Math.random() * dudas.length)];
    DOM.userInput.focus();
    setTimeout(dialogar, 300);
}

function exportarChat() {
    const mensajes = DOM.chatBox.querySelectorAll('.message:not(.system)');
    if (mensajes.length === 0) {
        alert('No hay mensajes para exportar.');
        return;
    }
    
    let contenido = '🏛️ SOCRABOT - DIÁLOGO SOCRÁTICO\n';
    contenido += '='.repeat(50) + '\n';
    contenido += `Fecha: ${new Date().toLocaleString()}\n\n`;
    
    mensajes.forEach(msg => {
        let texto = msg.textContent.trim();
        // Limpiar etiquetas
        texto = texto.replace('— Sócrates', '').trim();
        
        if (msg.classList.contains('user')) {
            contenido += `🧑 Tú: ${texto}\n`;
        } else if (msg.classList.contains('socrates')) {
            contenido += `🎭 Sócrates: ${texto}\n`;
        }
    });
    
    contenido += '\n' + '='.repeat(50) + '\n';
    contenido += 'El conocimiento está en las preguntas, no en las respuestas.';
    
    const blob = new Blob([contenido], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dialogo_socratico_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ===== EVENTOS =====
document.addEventListener('DOMContentLoaded', function() {
    DOM.userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            dialogar();
        }
    });
    DOM.userInput.focus();
    
    // Agregar atajo con Ctrl+Enter
    DOM.userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            dialogar();
        }
    });
});

// ===== EXPORTAR FUNCIONES GLOBALES =====//
window.dialogar = dialogar;
window.limpiarChat = limpiarChat;
window.cambiarEnfoque = cambiarEnfoque;
window.ejemploFilosofico = ejemploFilosofico;
window.ejemploDuda = ejemploDuda;
window.exportarChat = exportarChat;