// ========================================
// SOCRABOT - JAVASCRIPT COMPLETO
// Con manejo robusto de errores
// ========================================

// ===== CONFIGURACIÓN =====
const CONFIG = {
    API_URL: '/preguntar',
    RESET_URL: '/reset',
    TYPING_DELAY_MIN: 600,
    TYPING_DELAY_MAX: 1200,
    MAX_HISTORY: 100,
};

// ===== ESTADO =====
let historialConversacion = [];
let esperandoRespuesta = false;

// ===== ELEMENTOS DOM =====
const DOM = {
    chatBox: document.getElementById('chat'),
    userInput: document.getElementById('userInput'),
    sendButton: document.getElementById('sendButton'),
};

// ========================================
// FUNCIÓN PRINCIPAL
// ========================================
async function dialogar() {
    // Prevenir múltiples envíos
    if (esperandoRespuesta) return;
    
    const texto = DOM.userInput.value.trim();
    
    // Validar entrada
    if (!texto) {
        DOM.userInput.style.borderColor = '#c0392b';
        setTimeout(() => DOM.userInput.style.borderColor = '', 1000);
        return;
    }

    // Limpiar input y deshabilitar botón
    DOM.userInput.value = '';
    DOM.userInput.focus();
    esperandoRespuesta = true;
    DOM.sendButton.disabled = true;

    // Mostrar mensaje del usuario
    agregarMensaje(texto, 'user');
    historialConversacion.push({ rol: 'usuario', texto: texto });
    
    // Mantener historial limitado
    if (historialConversacion.length > CONFIG.MAX_HISTORY) {
        historialConversacion.shift();
    }

    // Mostrar indicador de escritura
    const typingId = mostrarIndicadorEscritura();

    try {
        // Enviar al servidor
        const response = await fetch(CONFIG.API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                texto: texto,
                historial: historialConversacion.slice(-5)
            })
        });

        // Verificar que la respuesta HTTP es OK
        if (!response.ok) {
            throw new Error(`Error del servidor: ${response.status}`);
        }

        // Leer el texto primero (evita "Unexpected end of JSON input")
        const textoRespuesta = await response.text();
        
        // Verificar que no está vacío
        if (!textoRespuesta || textoRespuesta.trim() === '') {
            throw new Error('Respuesta vacía del servidor');
        }

        // Parsear JSON de forma segura
        let data;
        try {
            data = JSON.parse(textoRespuesta);
        } catch (e) {
            console.error('Error parseando JSON:', textoRespuesta);
            throw new Error('Respuesta inválida del servidor');
        }

        // Ocultar indicador
        ocultarIndicadorEscritura(typingId);

        // Procesar respuesta
        if (data.error) {
            agregarMensaje(`⚠️ ${data.error}`, 'socrates');
        } else {
            const delay = Math.random() * (CONFIG.TYPING_DELAY_MAX - CONFIG.TYPING_DELAY_MIN) + CONFIG.TYPING_DELAY_MIN;
            setTimeout(() => {
                const respuestaFinal = data.respuesta || 'Interesante... ¿Puedes elaborar más?';
                agregarMensaje(respuestaFinal, 'socrates');
                historialConversacion.push({ rol: 'socrates', texto: respuestaFinal });
                esperandoRespuesta = false;
                DOM.sendButton.disabled = false;
            }, delay);
            return; // Salir antes del finally
        }

    } catch (error) {
        ocultarIndicadorEscritura(typingId);
        console.error('Error detallado:', error);
        
        // Mensaje amigable según el tipo de error
        let mensajeError = 'Perdona, mi mente se nubla. ';
        
        if (error.message.includes('vacía')) {
            mensajeError += '¿Puedes repetir tu pregunta?';
        } else if (error.message.includes('inválida')) {
            mensajeError += 'Estoy meditando. Intenta de nuevo.';
        } else if (error.message.includes('servidor')) {
            mensajeError += 'El oráculo está ocupado. Prueba otra vez.';
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            mensajeError += 'No puedo alcanzar el oráculo. ¿Estás conectado?';
        } else {
            mensajeError += '¿Puedes preguntarme de nuevo?';
        }
        
        agregarMensaje(mensajeError, 'socrates');
    }

    // Siempre reactivar el botón
    esperandoRespuesta = false;
    DOM.sendButton.disabled = false;
}

// ========================================
// AGREGAR MENSAJES
// ========================================
function agregarMensaje(texto, tipo, opciones = {}) {
    const div = document.createElement('div');
    div.className = `message ${tipo} fade-in`;
    
    // Convertir saltos de línea a <br>
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

// ========================================
// INDICADOR DE ESCRITURA
// ========================================
function mostrarIndicadorEscritura() {
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message socrates typing-indicator';
    
    const frases = [
        '🤔 Sócrates está reflexionando...',
        '🧠 Sócrates está pensando en su próxima pregunta...',
        '💭 Sócrates está meditando...',
        '📚 Sócrates está consultando su sabiduría...',
        '🏛️ Sócrates está contemplando tu pregunta...'
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

// ========================================
// LIMPIAR CHAT
// ========================================
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
    
    // Resetear en el servidor
    try {
        fetch(CONFIG.RESET_URL, { method: 'POST' }).catch(() => {});
    } catch (e) {
        // Ignorar errores
    }
}

// ========================================
// EJEMPLOS FILOSÓFICOS
// ========================================
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
        "¿Cuál es el sentido de la existencia?",
        "¿Puede la virtud enseñarse?",
        "¿Qué es la verdad y cómo la reconocemos?"
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
        "¿Qué es la libertad y cómo se conquista?",
        "¿Por qué hacemos lo que hacemos?",
        "¿Qué sentido tiene la vida si todo termina?"
    ];
    DOM.userInput.value = dudas[Math.floor(Math.random() * dudas.length)];
    DOM.userInput.focus();
    setTimeout(dialogar, 300);
}

// ========================================
// EXPORTAR DIÁLOGO
// ========================================
function exportarChat() {
    const mensajes = DOM.chatBox.querySelectorAll('.message:not(.system):not(.typing-indicator)');
    
    if (mensajes.length === 0) {
        alert('No hay mensajes para exportar.');
        return;
    }
    
    let contenido = '🏛️ SOCRABOT - DIÁLOGO SOCRÁTICO\n';
    contenido += '='.repeat(50) + '\n';
    contenido += `Fecha: ${new Date().toLocaleString()}\n`;
    contenido += `Total de mensajes: ${mensajes.length}\n`;
    contenido += '='.repeat(50) + '\n\n';
    
    mensajes.forEach(msg => {
        let texto = msg.textContent.trim();
        texto = texto.replace('— Sócrates', '').trim();
        
        if (msg.classList.contains('user')) {
            contenido += `🧑 Tú: ${texto}\n\n`;
        } else if (msg.classList.contains('socrates')) {
            contenido += `🎭 Sócrates: ${texto}\n\n`;
        }
    });
    
    contenido += '='.repeat(50) + '\n';
    contenido += 'El conocimiento está en las preguntas, no en las respuestas.\n';
    contenido += '— Inspirado en el método socrático';
    
    // Crear y descargar archivo
    const blob = new Blob([contenido], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dialogo_socratico_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ========================================
// EVENTOS
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // Enter para enviar
    DOM.userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            dialogar();
        }
    });
    
    // Focus automático
    DOM.userInput.focus();
    
    // Manejo de errores globales
    window.addEventListener('error', function(e) {
        console.error('Error global:', e.error);
    });
});

// ========================================
// EXPORTAR FUNCIONES GLOBALES
// ========================================
window.dialogar = dialogar;
window.limpiarChat = limpiarChat;
window.ejemploFilosofico = ejemploFilosofico;
window.ejemploDuda = ejemploDuda;
window.exportarChat = exportarChat;