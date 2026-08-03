/**
 * Chatbot Widget - Versión con Memoria de Conversación
 * Backend esperado: http://localhost:8000
 */

class ChatbotWidget {
    constructor(config) {
        this.tenantId = config.tenantId;
        this.apiHost = config.apiHost || 'http://localhost:8000';
        this.isOpen = false;
        this.chatHistory = [];
        this.sessionId = null; // Almacena el ID de sesión para mantener el contexto
        this.config = null;
        this.init();
    }

    async init() {
        try {
            const response = await fetch(`${this.apiHost}/api/tenants/${this.tenantId}/widget-config`);
            
            if (!response.ok) {
                console.error('Error al cargar configuración del tenant');
                return;
            }
            
            this.config = await response.json();
            this.createWidget();
        } catch (error) {
            console.error('Error al inicializar chatbot:', error);
        }
    }

    createWidget() {
        this.container = document.createElement('div');
        this.container.id = 'chatbot-widget-container';
        
        const primaryColor = this.config.primary_color || '#667eea';
        const companyName = this.config.company_name || 'Chatbot';
        const welcomeMessage = this.config.welcome_message || '¡Hola! ¿En qué puedo ayudarte?';

        this.container.innerHTML = `
            <style>
                #chatbot-widget-container * {
                    box-sizing: border-box;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                #chatbot-button {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: ${primaryColor};
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    z-index: 99999;
                    font-size: 28px;
                    transition: transform 0.2s, background 0.2s;
                    border: none;
                }
                #chatbot-button:hover {
                    transform: scale(1.1);
                    background: #5568d3;
                }
                #chatbot-window {
                    position: fixed;
                    bottom: 90px;
                    right: 20px;
                    width: 380px;
                    height: 550px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
                    display: none;
                    flex-direction: column;
                    z-index: 99999;
                    overflow: hidden;
                }
                #chatbot-window.open {
                    display: flex;
                }
                #chatbot-header {
                    background: ${primaryColor};
                    color: white;
                    padding: 16px;
                    font-weight: bold;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                #chatbot-close {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 20px;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                #chatbot-close:hover {
                    opacity: 0.8;
                }
                #chatbot-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                    background: #f9f9f9;
                    scroll-behavior: smooth;
                }
                .chat-message {
                    margin-bottom: 12px;
                    padding: 10px 14px;
                    border-radius: 12px;
                    max-width: 85%;
                    word-wrap: break-word;
                    line-height: 1.4;
                    font-size: 14px;
                    animation: fadeIn 0.3s ease;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(5px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .chat-message.user {
                    background: ${primaryColor};
                    color: white;
                    margin-left: auto;
                    border-bottom-right-radius: 4px;
                }
                .chat-message.bot {
                    background: white;
                    color: #333;
                    margin-right: auto;
                    border: 1px solid #e0e0e0;
                    border-bottom-left-radius: 4px;
                }
                .chat-message.loading {
                    opacity: 0.6;
                    font-style: italic;
                }
                #chatbot-input-container {
                    padding: 12px;
                    border-top: 1px solid #e0e0e0;
                    background: white;
                    display: flex;
                    gap: 8px;
                }
                #chatbot-input {
                    flex: 1;
                    padding: 10px 12px;
                    border: 1px solid #ddd;
                    border-radius: 20px;
                    font-size: 14px;
                    outline: none;
                    transition: border-color 0.2s;
                }
                #chatbot-input:focus {
                    border-color: ${primaryColor};
                }
                #chatbot-input:disabled {
                    background: #f5f5f5;
                    cursor: not-allowed;
                }
                #chatbot-send {
                    background: ${primaryColor};
                    color: white;
                    border: none;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    cursor: pointer;
                    font-size: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background 0.2s;
                }
                #chatbot-send:hover {
                    background: #5568d3;
                }
                #chatbot-send:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                @media (max-width: 480px) {
                    #chatbot-window {
                        width: calc(100% - 20px);
                        height: calc(100% - 120px);
                        right: 10px;
                        bottom: 90px;
                    }
                }
            </style>

            <div id="chatbot-window">
                <div id="chatbot-header">
                    <span>${companyName}</span>
                    <button id="chatbot-close">✕</button>
                </div>
                <div id="chatbot-messages"></div>
                <div id="chatbot-input-container">
                    <input type="text" id="chatbot-input" placeholder="Escribe tu mensaje..." autocomplete="off">
                    <button id="chatbot-send">➤</button>
                </div>
            </div>
            <div id="chatbot-button">💬</div>
        `;
        
        document.body.appendChild(this.container);
        
        // Event listeners
        document.getElementById('chatbot-button').addEventListener('click', () => this.toggle());
        document.getElementById('chatbot-close').addEventListener('click', () => this.toggle());
        document.getElementById('chatbot-send').addEventListener('click', () => this.sendMessage());
        document.getElementById('chatbot-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Mensaje de bienvenida inicial
        this.addMessage(welcomeMessage, 'bot');
    }

    toggle() {
        this.isOpen = !this.isOpen;
        const windowEl = document.getElementById('chatbot-window');
        const buttonEl = document.getElementById('chatbot-button');
        
        if (this.isOpen) {
            windowEl.classList.add('open');
            buttonEl.innerHTML = '✕';
            setTimeout(() => document.getElementById('chatbot-input').focus(), 100);
        } else {
            windowEl.classList.remove('open');
            buttonEl.innerHTML = '💬';
        }
    }

    async sendMessage() {
        const input = document.getElementById('chatbot-input');
        const sendButton = document.getElementById('chatbot-send');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Deshabilitar input mientras se procesa
        input.disabled = true;
        sendButton.disabled = true;
        
        // Agregar mensaje del usuario
        this.addMessage(message, 'user');
        input.value = '';
        
        // Mostrar indicador de carga
        const loadingId = this.addMessage('Escribiendo...', 'bot', true);
        
        try {
            // Construir la URL con session_id si existe (para mantener el contexto)
            let chatUrl = `${this.apiHost}/api/chat/${this.tenantId}?message=${encodeURIComponent(message)}`;
            if (this.sessionId) {
                chatUrl += `&session_id=${encodeURIComponent(this.sessionId)}`;
            }
            
            const response = await fetch(chatUrl, { method: 'POST' });
            
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            
            const data = await response.json();
            
            // Guardar el session_id para las siguientes mensagens
            if (data.session_id) {
                this.sessionId = data.session_id;
            }
            
            // Remover loading y agregar respuesta del bot
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            
            this.addMessage(data.response, 'bot');
            
            // Guardar en historial local (opcional, para futuras mejoras de UI)
            this.chatHistory.push({ role: 'user', content: message });
            this.chatHistory.push({ role: 'bot', content: data.response });
            
        } catch (error) {
            console.error('Error de chat:', error);
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            this.addMessage('Lo siento, hubo un error de conexión. Por favor intenta de nuevo.', 'bot');
        } finally {
            // Rehabilitar input
            input.disabled = false;
            sendButton.disabled = false;
            input.focus();
        }
    }

    addMessage(text, sender, isLoading = false) {
        const messagesDiv = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        const id = 'msg-' + Date.now() + Math.random().toString(36).substr(2, 9);
        messageDiv.id = id;
        
        messageDiv.className = `chat-message ${sender}${isLoading ? ' loading' : ''}`;
        
        // Convertir saltos de línea en <br> para mejor formato
        messageDiv.innerHTML = text.replace(/\n/g, '<br>');
        
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        return id;
    }
}

// Función global para inicializar el widget desde la web del cliente
window.initChatbot = function(config) {
    if (!config || !config.tenantId) {
        console.error('Chatbot: Falta el tenantId en la configuración');
        return null;
    }
    return new ChatbotWidget(config);
};