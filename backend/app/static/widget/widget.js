(function() {
    var CHATBOT_CONFIG = {
        tenantId: window.CHATBOT_TENANT_ID || 'cliente-01',
        position: 'bottom-right',
        primaryColor: '#3b82f6',
        title: 'Asistente Virtual'
    };

    var sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    var widgetApiBase = (function() {
        var script = document.currentScript;
        if (script && script.src) {
            try { return new URL(script.src).origin; } catch (e) {}
        }
        return '';
    })();

    var widgetHTML = `
        <div id="chatbot-widget" style="position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div id="chatbot-toggle" style="width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
            </div>
            <div id="chatbot-window" style="display: none; width: 380px; height: 550px; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-radius: 20px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2); flex-direction: column; overflow: hidden; position: absolute; bottom: 80px; right: 0; border: 1px solid rgba(255, 255, 255, 0.3); animation: slideUp 0.3s ease-out;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; font-weight: 600; font-size: 18px; border-bottom: 1px solid rgba(255, 255, 255, 0.2);">${CHATBOT_CONFIG.title}</div>
                <div id="chatbot-messages" style="flex: 1; overflow-y: auto; padding: 20px; background: rgba(249, 250, 251, 0.8);"></div>
                <div style="padding: 16px; border-top: 1px solid rgba(229, 231, 235, 0.5); background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px);">
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="chatbot-input" placeholder="Escribe tu mensaje..." style="flex: 1; padding: 12px 16px; border: 1px solid rgba(209, 213, 219, 0.5); border-radius: 12px; font-size: 14px; background: rgba(255, 255, 255, 0.8); transition: all 0.2s;" onfocus="this.style.borderColor='#667eea'; this.style.boxShadow='0 0 0 3px rgba(102, 126, 234, 0.1)'" onblur="this.style.borderColor='rgba(209, 213, 219, 0.5)'; this.style.boxShadow='none'">
                        <button id="chatbot-send" style="padding: 12px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 12px; cursor: pointer; font-weight: 600; transition: all 0.2s; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(102, 126, 234, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.3)'">Enviar</button>
                    </div>
                </div>
            </div>
        </div>
        <style>
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
    `;

    document.body.insertAdjacentHTML('beforeend', widgetHTML);

    var toggle = document.getElementById('chatbot-toggle');
    var window_ = document.getElementById('chatbot-window');
    var messages = document.getElementById('chatbot-messages');
    var input = document.getElementById('chatbot-input');
    var sendBtn = document.getElementById('chatbot-send');

    toggle.addEventListener('click', function() {
        if (window_.style.display === 'none') {
            window_.style.display = 'flex';
            toggle.style.transform = 'scale(0.9)';
            if (messages.children.length === 0) {
                addMessage('assistant', '¡Hola! ¿En qué puedo ayudarte hoy?');
            }
        } else {
            window_.style.display = 'none';
            toggle.style.transform = 'scale(1)';
        }
    });

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });

    function addMessage(role, text) {
        var msgDiv = document.createElement('div');
        msgDiv.style.marginBottom = '16px';
        msgDiv.style.display = 'flex';
        msgDiv.style.justifyContent = role === 'user' ? 'flex-end' : 'flex-start';
        msgDiv.style.animation = 'slideUp 0.3s ease-out';
        
        var bubble = document.createElement('div');
        bubble.style.padding = '12px 18px';
        bubble.style.borderRadius = '16px';
        bubble.style.maxWidth = '80%';
        bubble.style.fontSize = '14px';
        bubble.style.lineHeight = '1.5';
        bubble.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.08)';
        
        if (role === 'user') {
            bubble.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            bubble.style.color = 'white';
        } else {
            bubble.style.background = 'rgba(255, 255, 255, 0.9)';
            bubble.style.color = '#1f2937';
            bubble.style.border = '1px solid rgba(229, 231, 235, 0.5)';
            bubble.style.backdropFilter = 'blur(10px)';
        }
        
        bubble.textContent = text;
        msgDiv.appendChild(bubble);
        messages.appendChild(msgDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage() {
        var question = input.value.trim();
        if (!question) return;

        addMessage('user', question);
        input.value = '';
        sendBtn.disabled = true;
        sendBtn.textContent = '...';

        try {
            var response = await fetch(widgetApiBase + '/api/chat/' + CHATBOT_CONFIG.tenantId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    session_id: sessionId
                })
            });

            var data = await response.json();
            
            if (data.status === 'success') {
                addMessage('assistant', data.answer);
            } else {
                addMessage('assistant', 'Lo siento, hubo un error. Por favor, intenta de nuevo.');
            }
        } catch (error) {
            addMessage('assistant', 'Error de conexión. Por favor, verifica tu internet.');
        }

        sendBtn.disabled = false;
        sendBtn.textContent = 'Enviar';
    }
})();
