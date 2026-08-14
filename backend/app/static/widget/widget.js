(function() {
    var CONFIG = {
        tenantId: window.CHATBOT_TENANT_ID || 'cliente-01',
        title: window.CHATBOT_TITLE || 'Asistente Virtual',
        subtitle: window.CHATBOT_SUBTITLE || 'En línea - responde al instante',
        primaryColor: window.CHATBOT_PRIMARY_COLOR || '#667eea',
        secondaryColor: window.CHATBOT_SECONDARY_COLOR || '#764ba2',
        avatarUrl: window.CHATBOT_AVATAR_URL || '',
        welcome: window.CHATBOT_WELCOME || '¡Hola! 👋 Soy el asistente virtual de la empresa. ¿En qué puedo ayudarte hoy?',
        quickReplies: window.CHATBOT_QUICK_REPLIES || ['¿Qué servicios ofrecen?', '¿Cuál es su horario?', 'Quiero que me contacten']
    };

    var sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    var widgetApiBase = (function() {
        var script = document.currentScript;
        if (script && script.src) {
            try { return new URL(script.src).origin; } catch (e) {}
        }
        return '';
    })();

    var grad = 'linear-gradient(135deg, ' + CONFIG.primaryColor + ' 0%, ' + CONFIG.secondaryColor + ' 100%)';

    var widgetHTML = `
        <div id="chatbot-widget" style="position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div id="chatbot-toggle" style="width: 60px; height: 60px; border-radius: 50%; background: ${grad}; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 24px rgba(0,0,0,0.25); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);" title="Abrir chat">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
            </div>
            <div id="chatbot-window" style="display: none; width: 380px; max-width: calc(100vw - 40px); height: 560px; max-height: calc(100vh - 100px); background: #ffffff; border-radius: 20px; box-shadow: 0 24px 80px rgba(0, 0, 0, 0.25); flex-direction: column; overflow: hidden; position: absolute; bottom: 80px; right: 0; border: 1px solid rgba(255, 255, 255, 0.3); animation: chatbotSlideUp 0.3s ease-out;">
                <div id="chatbot-header" style="background: ${grad}; color: white; padding: 16px 18px; display: flex; align-items: center; gap: 12px; flex-shrink: 0;">
                    <div id="chatbot-avatar" style="width: 42px; height: 42px; border-radius: 50%; background: rgba(255,255,255,0.25); border: 2px solid rgba(255,255,255,0.6); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; overflow: hidden; flex-shrink: 0;"></div>
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: 700; font-size: 15px; line-height: 1.2;">${CONFIG.title}</div>
                        <div style="font-size: 12px; opacity: 0.95; display: flex; align-items: center; gap: 5px;"><span style="width: 8px; height: 8px; border-radius: 50%; background: #4ade80; display: inline-block;"></span>${CONFIG.subtitle}</div>
                    </div>
                    <button id="chatbot-minimize" style="background: rgba(255,255,255,0.2); border: none; color: white; width: 30px; height: 30px; border-radius: 50%; cursor: pointer; font-size: 16px; line-height: 1; display: flex; align-items: center; justify-content: center;" title="Minimizar">&minus;</button>
                </div>
                <div id="chatbot-messages" style="flex: 1; overflow-y: auto; padding: 16px; background: #f7f8fa;"></div>
                <div id="chatbot-quick" style="display: none; padding: 8px 16px 12px; background: #f7f8fa; gap: 8px; flex-wrap: wrap;"></div>
                <div style="padding: 12px 16px; border-top: 1px solid #eceef1; background: #ffffff; flex-shrink: 0;">
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <input type="text" id="chatbot-input" placeholder="Escribe tu mensaje..." style="flex: 1; padding: 11px 14px; border: 1px solid #e2e5ea; border-radius: 12px; font-size: 14px; outline: none; background: #f9fafb; transition: all 0.2s;">
                        <button id="chatbot-send" style="width: 44px; height: 44px; background: ${grad}; color: white; border: none; border-radius: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; box-shadow: 0 4px 12px rgba(0,0,0,0.18); flex-shrink: 0;" title="Enviar">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
        <style>
            @keyframes chatbotSlideUp { from { opacity: 0; transform: translateY(20px);} to { opacity: 1; transform: translateY(0);} }
            @keyframes chatbotFadeIn { from { opacity: 0; transform: translateY(6px);} to { opacity: 1; transform: translateY(0);} }
            @keyframes chatbotTyping { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.4;} 40% { transform: scale(1); opacity: 1;} }
            #chatbot-widget * { box-sizing: border-box; }
            #chatbot-messages::-webkit-scrollbar { width: 6px; }
            #chatbot-messages::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
            .cb-bubble { animation: chatbotFadeIn 0.25s ease-out; }
            .cb-typing-dot { width: 7px; height: 7px; border-radius: 50%; background: #9ca3af; display: inline-block; margin-right: 3px; animation: chatbotTyping 1.2s infinite ease-in-out; }
            .cb-typing-dot:nth-child(2) { animation-delay: 0.2s; }
            .cb-typing-dot:nth-child(3) { animation-delay: 0.4s; }
        </style>
    `;

    document.body.insertAdjacentHTML('beforeend', widgetHTML);

    var toggle = document.getElementById('chatbot-toggle');
    var window_ = document.getElementById('chatbot-window');
    var messages = document.getElementById('chatbot-messages');
    var input = document.getElementById('chatbot-input');
    var sendBtn = document.getElementById('chatbot-send');
    var quick = document.getElementById('chatbot-quick');

    var avatarEl = document.getElementById('chatbot-avatar');
    if (CONFIG.avatarUrl) {
        avatarEl.innerHTML = '<img src="' + CONFIG.avatarUrl + '" style="width:100%;height:100%;object-fit:cover;" alt="">';
    } else {
        avatarEl.textContent = (CONFIG.title || '?').charAt(0).toUpperCase();
    }

    var focusBorder = function(el) { el.style.borderColor = CONFIG.primaryColor; el.style.boxShadow = '0 0 0 3px ' + CONFIG.primaryColor + '22'; };
    var blurBorder = function(el) { el.style.borderColor = '#e2e5ea'; el.style.boxShadow = 'none'; };
    input.addEventListener('focus', function() { focusBorder(input); });
    input.addEventListener('blur', function() { blurBorder(input); });

    toggle.addEventListener('click', function() {
        if (window_.style.display === 'none') {
            openChat();
        } else {
            window_.style.display = 'none';
            toggle.style.transform = 'scale(1)';
        }
    });

    var minimizeBtn = document.getElementById('chatbot-minimize');
    minimizeBtn.addEventListener('click', function() {
        window_.style.display = 'none';
        toggle.style.transform = 'scale(1)';
    });

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });

    function openChat() {
        window_.style.display = 'flex';
        toggle.style.transform = 'scale(0.9)';
        if (messages.children.length === 0) {
            addMessage('assistant', CONFIG.welcome);
            renderQuickReplies();
            setTimeout(function() { input.focus(); }, 300);
        }
    }

    function renderQuickReplies() {
        quick.innerHTML = '';
        quick.style.display = 'flex';
        for (var i = 0; i < CONFIG.quickReplies.length; i++) {
            (function(text) {
                var chip = document.createElement('button');
                chip.textContent = text;
                chip.style.cssText = 'padding: 8px 12px; border-radius: 999px; border: 1px solid ' + CONFIG.primaryColor + '44; background: #ffffff; color: #374151; font-size: 12.5px; cursor: pointer; transition: all 0.2s;';
                chip.onmouseover = function() { chip.style.background = CONFIG.primaryColor + '11'; chip.style.borderColor = CONFIG.primaryColor; };
                chip.onmouseout = function() { chip.style.background = '#ffffff'; chip.style.borderColor = CONFIG.primaryColor + '44'; };
                chip.onclick = function() {
                    input.value = text;
                    sendMessage();
                };
                quick.appendChild(chip);
            })(CONFIG.quickReplies[i]);
        }
    }

    function addMessage(role, text) {
        var msgDiv = document.createElement('div');
        msgDiv.className = 'cb-bubble';
        msgDiv.style.marginBottom = '12px';
        msgDiv.style.display = 'flex';
        msgDiv.style.flexDirection = 'column';
        msgDiv.style.alignItems = role === 'user' ? 'flex-end' : 'flex-start';

        var bubble = document.createElement('div');
        bubble.style.padding = '11px 15px';
        bubble.style.borderRadius = role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px';
        bubble.style.maxWidth = '82%';
        bubble.style.fontSize = '14px';
        bubble.style.lineHeight = '1.5';
        bubble.style.wordWrap = 'break-word';

        if (role === 'user') {
            bubble.style.background = grad;
            bubble.style.color = 'white';
            bubble.style.boxShadow = '0 3px 10px rgba(0,0,0,0.12)';
        } else {
            bubble.style.background = '#ffffff';
            bubble.style.color = '#1f2937';
            bubble.style.border = '1px solid #eceef1';
            bubble.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)';
        }

        bubble.textContent = text;
        msgDiv.appendChild(bubble);

        var time = document.createElement('div');
        time.style.fontSize = '10px';
        time.style.color = '#9ca3af';
        time.style.marginTop = '3px';
        time.style.marginLeft = role === 'user' ? 'auto' : '2px';
        time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        msgDiv.appendChild(time);

        messages.appendChild(msgDiv);
        messages.scrollTop = messages.scrollHeight;
        return msgDiv;
    }

    function showTyping() {
        var typingRow = document.createElement('div');
        typingRow.id = 'cb-typing';
        typingRow.style.marginBottom = '12px';
        typingRow.style.display = 'flex';
        typingRow.style.justifyContent = 'flex-start';
        var bubble = document.createElement('div');
        bubble.style.padding = '12px 15px';
        bubble.style.borderRadius = '16px 16px 16px 4px';
        bubble.style.background = '#ffffff';
        bubble.style.border = '1px solid #eceef1';
        bubble.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)';
        bubble.innerHTML = '<span class="cb-typing-dot"></span><span class="cb-typing-dot"></span><span class="cb-typing-dot"></span>';
        typingRow.appendChild(bubble);
        messages.appendChild(typingRow);
        messages.scrollTop = messages.scrollHeight;
    }

    function hideTyping() {
        var typing = document.getElementById('cb-typing');
        if (typing) typing.remove();
    }

    async function sendMessage() {
        var question = input.value.trim();
        if (!question) return;

        addMessage('user', question);
        input.value = '';
        sendBtn.disabled = true;
        sendBtn.style.opacity = '0.6';
        showTyping();

        try {
            var response = await fetch(widgetApiBase + '/api/chat/' + CONFIG.tenantId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    session_id: sessionId
                })
            });

            var data = await response.json();

            hideTyping();
            if (data.status === 'success') {
                addMessage('assistant', data.answer);
            } else {
                addMessage('assistant', 'Lo siento, hubo un error. Por favor, intenta de nuevo.');
            }
        } catch (error) {
            hideTyping();
            addMessage('assistant', 'Error de conexión. Por favor, verifica tu internet.');
        }

        sendBtn.disabled = false;
        sendBtn.style.opacity = '1';
        input.focus();
    }
})();
