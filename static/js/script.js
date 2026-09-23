// ========================================
// SOCRABOT - LÓGICA COMPLETA
// ========================================

const CONFIG = {
    API_URL: '/preguntar',
    RESET_URL: '/reset',
    TYPING_DELAY_MIN: 600,
    TYPING_DELAY_MAX: 1200,
    INACTIVITY_TIME: 15000,
    BUBBLE_DURATION: 6000,
    BLINK_INTERVAL_MIN: 3000,
    BLINK_INTERVAL_MAX: 6000,
    BLINK_DURATION: 150,
    TALK_FRAME_INTERVAL: 150,
};

let historialConversacion = [];
let esperandoRespuesta = false;
let inactivityTimer = null;
let bubbleTimer = null;
let bubbleOcupada = false;
let blinkTimer = null;
let talkTimer = null;
let estadoActual = 'idle';
let nombreUsuario = localStorage.getItem('socrabot-nombre') || '';

const DOM = {
    chatBox: document.getElementById('chat'),
    userInput: document.getElementById('userInput'),
    sendButton: document.getElementById('sendButton'),
    socratesAvatar: document.getElementById('socratesAvatar'),
    socratesImg: document.getElementById('socratesImg'),
    socratesBubble: document.getElementById('socratesBubble'),
    socratesText: document.getElementById('socratesText'),
    themeIcon: document.getElementById('themeIcon'),
};

const SPRITES = {
    idle: '/static/img/socrates-idle.png',
    speaking: '/static/img/socrates-speaking.png',
    thinking: '/static/img/socrates-thinking.png',
    speakingBlink: '/static/img/socrates-speaking-blink.png',
    listening: '/static/img/socrates-listening.png',
    neutral: '/static/img/socrates-neutral.png',
};

const FRASES_SALUDO = [
    "¡Saludos, buscador de la verdad!",
    "Bienvenido, amigo. ¿Qué te preocupa hoy?",
    "Hola, caminante. ¿Has venido a examinar tu alma?",
    "El conocimiento no se da, se despierta. ¿Empezamos?",
    "Solo sé que no sé nada. ¿Y tú qué sabes?",
];

const FRASES_INACTIVIDAD = [
    "¿Sigues ahí, amigo? El silencio también es una respuesta.",
    "Mientras callas, tus pensamientos hablan. ¿Qué dicen?",
    "¿Sabes? La duda es el principio de la sabiduría.",
    "Una vida sin examen no merece ser vivida.",
    "¿Te has preguntado por qué haces lo que haces?",
    "El tiempo pasa, pero las preguntas quedan.",
    "¿Qué es lo que realmente buscas?",
    "Solo sé que no sé nada. ¿Y tú?",
    "La sabiduría comienza con una pregunta.",
    "¿Cuánto tiempo ha pasado desde que te cuestionaste algo?",
];

const FRASES_PENSANDO = [
    "🤔 Déjame pensar...",
    "🧠 Reflexionando...",
    "💭 Meditando tu pregunta...",
    "📚 Consultando mi sabiduría...",
];

// ===== NOMBRE =====
function guardarNombre() {
    const input = document.getElementById('nombreInput');
    const nombre = input.value.trim();
    
    if (!nombre) {
        input.style.borderColor = '#c0392b';
        setTimeout(() => input.style.borderColor = '', 1000);
        return;
    }
    
    nombreUsuario = nombre;
    localStorage.setItem('socrabot-nombre', nombre);
    document.getElementById('nombreModal').classList.add('oculto');
    
    // ⬇️ ACTUALIZAR SIDEBAR
    actualizarNombreSidebar();
    
    mostrarBurbuja(`¡Saludos, ${nombre}! ¿Qué te preocupa hoy?`);
}

function cambiarNombre() {
    const nombreActual = localStorage.getItem('socrabot-nombre') || '';
    const nuevoNombre = prompt('Escribe tu nuevo nombre:', nombreActual);
    
    if (nuevoNombre && nuevoNombre.trim()) {
        localStorage.setItem('socrabot-nombre', nuevoNombre.trim());
        nombreUsuario = nuevoNombre.trim();
        location.reload();
    }
}

function cerrarSesion() {
    if (confirm('¿Cerrar sesión?\n\nSe borrará tu nombre y el próximo estudiante podrá poner el suyo.')) {
        localStorage.removeItem('socrabot-nombre');
        localStorage.removeItem('socrabot-theme');
        location.reload();
    }
}

function actualizarNombreSidebar() {
    const nombreLabel = document.getElementById('nombreActual');
    if (nombreLabel) {
        nombreLabel.textContent = nombreUsuario || 'Sin nombre';
    }
}

// ===== CAMBIAR SPRITE =====
function cambiarSprite(ruta) {
    if (!DOM.socratesImg) return;
    if (DOM.socratesImg.src.includes(ruta.split('/').pop())) return;
    
    DOM.socratesImg.style.opacity = '0';
    setTimeout(() => {
        DOM.socratesImg.src = ruta;
        DOM.socratesImg.style.opacity = '1';
    }, 80);
}

// ===== PARPADEO =====
function iniciarParpadeo() {
    clearTimeout(blinkTimer);
    const intervalo = Math.random() * (CONFIG.BLINK_INTERVAL_MAX - CONFIG.BLINK_INTERVAL_MIN) + CONFIG.BLINK_INTERVAL_MIN;
    
    blinkTimer = setTimeout(() => {
        if (estadoActual === 'idle' || estadoActual === 'neutral') {
            const spriteOriginal = estadoActual === 'idle' ? SPRITES.idle : SPRITES.neutral;
            cambiarSprite(SPRITES.thinking);
            setTimeout(() => {
                cambiarSprite(spriteOriginal);
                iniciarParpadeo();
            }, CONFIG.BLINK_DURATION);
        } else {
            iniciarParpadeo();
        }
    }, intervalo);
}

// ===== HABLAR =====
function iniciarHablar() {
    clearInterval(talkTimer);
    let frameBoca = 'abierta';
    
    talkTimer = setInterval(() => {
        if (estadoActual !== 'speaking') {
            clearInterval(talkTimer);
            return;
        }
        
        frameBoca = frameBoca === 'abierta' ? 'cerrada' : 'abierta';
        
        if (frameBoca === 'abierta') {
            const debeParpadear = Math.random() < 0.1;
            cambiarSprite(debeParpadear ? SPRITES.speakingBlink : SPRITES.speaking);
        } else {
            cambiarSprite(SPRITES.speaking);
        }
    }, CONFIG.TALK_FRAME_INTERVAL);
}

function detenerHablar() {
    clearInterval(talkTimer);
}

// ===== ESTADO =====
function setEstadoSocrates(estado) {
    estadoActual = estado || 'idle';
    
    DOM.socratesAvatar.classList.remove('thinking', 'speaking', 'idle');
    detenerHablar();
    clearTimeout(blinkTimer);
    
    switch (estado) {
        case 'thinking':
            cambiarSprite(SPRITES.thinking);
            DOM.socratesAvatar.classList.add('thinking');
            break;
        case 'speaking':
            cambiarSprite(SPRITES.speaking);
            DOM.socratesAvatar.classList.add('speaking');
            iniciarHablar();
            break;
        case 'neutral':
            cambiarSprite(SPRITES.neutral);
            iniciarParpadeo();
            break;
        case 'idle':
        default:
            cambiarSprite(SPRITES.idle);
            DOM.socratesAvatar.classList.add('idle');
            iniciarParpadeo();
            break;
    }
}

// ===== BURBUJA =====
function mostrarBurbuja(texto, duracion = CONFIG.BUBBLE_DURATION, alTerminar = null) {
    if (bubbleOcupada) return;
    bubbleOcupada = true;
    
    DOM.socratesText.textContent = texto;
    DOM.socratesBubble.classList.add('visible');
    
    clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(() => {
        DOM.socratesBubble.classList.remove('visible');
        bubbleOcupada = false;
        if (alTerminar) alTerminar();
    }, duracion);
}

// ===== INACTIVIDAD =====
function iniciarTemporizadorInactividad() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
        if (!esperandoRespuesta && !bubbleOcupada) {
            setEstadoSocrates('idle');
            const frase = FRASES_INACTIVIDAD[Math.floor(Math.random() * FRASES_INACTIVIDAD.length)];
            mostrarBurbuja(frase);
        }
        iniciarTemporizadorInactividad();
    }, CONFIG.INACTIVITY_TIME);
}

function reiniciarTemporizadorInactividad() {
    iniciarTemporizadorInactividad();
}

// ===== DIÁLOGO =====
async function dialogar() {
    if (esperandoRespuesta) return;
    
    // Ocultar pantalla de bienvenida si existe
    const welcome = document.getElementById('welcomeScreen');
    if (welcome) welcome.classList.add('hidden');
    
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

    setEstadoSocrates('thinking');
    bubbleOcupada = false;
    mostrarBurbuja(FRASES_PENSANDO[Math.floor(Math.random() * FRASES_PENSANDO.length)], 3000);

    const typingId = mostrarIndicadorEscritura();

    try {
        const response = await fetch(CONFIG.API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                texto: texto,
                nombre: nombreUsuario || 'Anónimo',
                historial: historialConversacion.slice(-5)
            })
        });

        const textoRespuesta = await response.text();
        if (!textoRespuesta) throw new Error('Respuesta vacía');

        const data = JSON.parse(textoRespuesta);
        ocultarIndicadorEscritura(typingId);

        if (data.error) {
            agregarMensaje(`⚠️ ${data.error}`, 'socrates');
            setEstadoSocrates('idle');
            esperandoRespuesta = false;
            DOM.sendButton.disabled = false;
        } else {
            const delay = Math.random() * 800 + 400;
            setTimeout(() => {
                const respuestaFinal = data.respuesta || 'Interesante...';
                agregarMensaje(respuestaFinal, 'socrates');
                historialConversacion.push({ rol: 'socrates', texto: respuestaFinal });
                
                setEstadoSocrates('speaking');
                bubbleOcupada = false;
                clearTimeout(bubbleTimer);
                
                mostrarBurbuja(respuestaFinal, CONFIG.BUBBLE_DURATION, () => {
                    setEstadoSocrates('idle');
                });
                
                esperandoRespuesta = false;
                DOM.sendButton.disabled = false;
                reiniciarTemporizadorInactividad();
            }, delay);
        }

    } catch (error) {
        ocultarIndicadorEscritura(typingId);
        console.error('Error:', error);
        agregarMensaje('Perdona, mi mente se nubla. ¿Puedes repetir eso?', 'socrates');
        setEstadoSocrates('idle');
        esperandoRespuesta = false;
        DOM.sendButton.disabled = false;
    }
}

function agregarMensaje(texto, tipo) {
    const div = document.createElement('div');
    div.className = `message ${tipo} fade-in`;
    const textoFormateado = texto.replace(/\n/g, '<br>');
    
    if (tipo === 'socrates') {
        div.innerHTML = `${textoFormateado} <span class="socrates-label">— Sócrates</span>`;
    } else {
        div.textContent = texto;
    }
    
    DOM.chatBox.appendChild(div);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
}

function mostrarIndicadorEscritura() {
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message socrates typing-indicator';
    div.textContent = FRASES_PENSANDO[Math.floor(Math.random() * FRASES_PENSANDO.length)];
    DOM.chatBox.appendChild(div);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    return id;
}

function ocultarIndicadorEscritura(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function limpiarChat() {
    if (historialConversacion.length > 0 && !confirm('¿Seguro que quieres limpiar el diálogo?')) return;
    
    DOM.chatBox.innerHTML = '';
    historialConversacion = [];
    
    agregarMensaje(
        'El diálogo se renueva. Como el río, el pensamiento fluye constantemente.\n\n¿Qué nueva pregunta te gustaría explorar?',
        'socrates'
    );
    
    fetch(CONFIG.RESET_URL, { method: 'POST' }).catch(() => {});
}

function ejemploFilosofico() {
    const ejemplos = [
        "¿Qué es la felicidad y cómo se alcanza?",
        "¿El conocimiento verdadero viene de la razón o de la experiencia?",
        "¿Qué significa ser una buena persona?",
        "¿Cómo sabemos lo que es real?",
        "¿El amor es un sentimiento o una elección?",
        "¿Qué es la justicia y cómo se aplica?",
        "¿Qué papel juega la libertad en nuestra vida?",
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
    ];
    DOM.userInput.value = dudas[Math.floor(Math.random() * dudas.length)];
    DOM.userInput.focus();
    setTimeout(dialogar, 300);
}

function exportarChat() {
    const mensajes = DOM.chatBox.querySelectorAll('.message:not(.typing-indicator)');
    if (mensajes.length === 0) return alert('No hay mensajes para exportar.');
    
    let contenido = '🏛️ SOCRABOT - DIÁLOGO SOCRÁTICO\n';
    contenido += '='.repeat(50) + '\n';
    contenido += `Usuario: ${nombreUsuario}\n`;
    contenido += `Fecha: ${new Date().toLocaleString()}\n\n`;
    
    mensajes.forEach(msg => {
        let texto = msg.textContent.replace('— Sócrates', '').trim();
        if (msg.classList.contains('user')) contenido += `👤 Tú: ${texto}\n\n`;
        else if (msg.classList.contains('socrates')) contenido += `🎭 Sócrates: ${texto}\n\n`;
    });
    
    const blob = new Blob([contenido], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dialogo_${nombreUsuario}_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const esOscuro = document.body.classList.contains('dark-theme');
    DOM.themeIcon.textContent = esOscuro ? '☀️' : '🌙';
    localStorage.setItem('socrabot-theme', esOscuro ? 'dark' : 'light');
    
    // ⬇️ ACTUALIZAR LABEL DEL TEMA EN EL SIDEBAR
    const label = document.getElementById('themeLabel');
    if (label) label.textContent = esOscuro ? 'Modo claro' : 'Modo oscuro';
}

function cargarTema() {
    const temaGuardado = localStorage.getItem('socrabot-theme');
    if (temaGuardado === 'dark') {
        document.body.classList.add('dark-theme');
        DOM.themeIcon.textContent = '☀️';
    }
}

// ===== SIDEBAR MÓVIL =====
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.toggle('open');
    overlay.classList.toggle('visible');
}

// ===== SUGERENCIAS DE LA PANTALLA DE BIENVENIDA =====
function usarSugerencia(texto) {
    document.getElementById('userInput').value = texto;
    dialogar();
}

// ===== EVENTOS =====
document.addEventListener('DOMContentLoaded', () => {
    cargarTema();
    setEstadoSocrates('neutral');
    
    // Verificar si ya tiene nombre
    if (nombreUsuario) {
        document.getElementById('nombreModal').classList.add('oculto');
    } else {
        setTimeout(() => document.getElementById('nombreInput')?.focus(), 500);
    }
    
    // Enter para enviar
    DOM.userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            dialogar();
        }
    });
    
    DOM.userInput.focus();
    
    // Saludo inicial
    setTimeout(() => {
        const nombre = nombreUsuario || 'buscador';
        mostrarBurbuja(`¡Saludos, ${nombre}! ¿Qué te preocupa hoy?`);
    }, 1000);
    
    iniciarTemporizadorInactividad();
    
    document.addEventListener('mousemove', reiniciarTemporizadorInactividad);
    document.addEventListener('keypress', reiniciarTemporizadorInactividad);
    
    // ⬇️ ACTUALIZAR NOMBRE Y TEMA EN EL SIDEBAR
    actualizarNombreSidebar();
    
    const label = document.getElementById('themeLabel');
    if (label) {
        const esOscuro = document.body.classList.contains('dark-theme');
        label.textContent = esOscuro ? 'Modo claro' : 'Modo oscuro';
    }
});

// ===== CARGAR NOMBRE EXISTENTE =====
function mostrarCargarNombre() {
    document.getElementById('cargarNombreForm').style.display = 'block';
    document.getElementById('nombreExistente').focus();
    document.getElementById('errorCargarNombre').textContent = '';
}

function ocultarCargarNombre() {
    document.getElementById('cargarNombreForm').style.display = 'none';
    document.getElementById('nombreExistente').value = '';
    document.getElementById('errorCargarNombre').textContent = '';
}

async function cargarNombreExistente() {
    const input = document.getElementById('nombreExistente');
    const errorMsg = document.getElementById('errorCargarNombre');
    const nombre = input.value.trim();
    
    if (!nombre) {
        errorMsg.textContent = 'Escribe tu nombre primero.';
        input.style.borderColor = '#c0392b';
        setTimeout(() => input.style.borderColor = '', 1000);
        return;
    }
    
    errorMsg.textContent = '🔍 Buscando...';
    
    try {
        const response = await fetch('/verificar-nombre', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre: nombre })
        });
        
        const data = await response.json();
        
        if (data.existe) {
            // Nombre encontrado: guardar y entrar
            localStorage.setItem('socrabot-nombre', nombre);
            nombreUsuario = nombre;
            
            errorMsg.style.color = '#27ae60';
            errorMsg.textContent = `✅ ¡Bienvenido de nuevo, ${nombre}!`;
            
            setTimeout(() => {
                document.getElementById('nombreModal').classList.add('oculto');
                actualizarNombreSidebar();
                mostrarBurbuja(`¡Saludos de nuevo, ${nombre}! ¿Seguimos filosofando?`);
            }, 800);
        } else {
            errorMsg.style.color = '#c0392b';
            errorMsg.textContent = '❌ Ese nombre no está registrado. ¿Quieres crear uno nuevo?';
            input.style.borderColor = '#c0392b';
            setTimeout(() => input.style.borderColor = '', 1000);
        }
    } catch (error) {
        console.error('Error:', error);
        errorMsg.style.color = '#c0392b';
        errorMsg.textContent = '⚠️ Error de conexión. Intenta de nuevo.';
    }
}

// ===== GLOBALES =====
window.dialogar = dialogar;
window.limpiarChat = limpiarChat;
window.ejemploFilosofico = ejemploFilosofico;
window.ejemploDuda = ejemploDuda;
window.exportarChat = exportarChat;
window.toggleTheme = toggleTheme;
window.guardarNombre = guardarNombre;
window.cambiarNombre = cambiarNombre;
window.cerrarSesion = cerrarSesion;
window.actualizarNombreSidebar = actualizarNombreSidebar;
window.toggleSidebar = toggleSidebar;
window.usarSugerencia = usarSugerencia;
window.mostrarCargarNombre = mostrarCargarNombre;
window.ocultarCargarNombre = ocultarCargarNombre;
window.cargarNombreExistente = cargarNombreExistente;