(function() {
  'use strict';

  function getApiEndpoint() {
    if (window.ANNA_API_URL) return window.ANNA_API_URL;
    
    const scriptTag = document.querySelector('script[src*="widget.js"]');
    if (scriptTag && scriptTag.src) {
      const scriptUrl = new URL(scriptTag.src);
      return scriptUrl.origin + '/api/chat/stream';
    }
    
    return '/api/chat/stream';
  }

  function getLogoUrl() {
    const scriptTag = document.querySelector('script[src*="widget.js"]');
    if (scriptTag && scriptTag.src) {
      const scriptUrl = new URL(scriptTag.src);
      return scriptUrl.origin + '/anna-logo.png';
    }
    return '/anna-logo.png';
  }

  const WIDGET_CONFIG = {
    get apiEndpoint() { return getApiEndpoint(); },
    get logoUrl() { return getLogoUrl(); },
    primaryColor: '#03a9f4',
    position: 'bottom-right'
  };

  const styles = `
    #anna-widget-container * {
      box-sizing: border-box;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    }

    #anna-chat-bubble {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #03a9f4, #0288d1);
      box-shadow: 0 4px 20px rgba(3, 169, 244, 0.4);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999998;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
      border: none;
    }

    #anna-chat-bubble:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 30px rgba(3, 169, 244, 0.6);
    }

    #anna-chat-bubble svg {
      width: 28px;
      height: 28px;
      fill: white;
    }

    #anna-chat-bubble.open svg.chat-icon {
      display: none;
    }

    #anna-chat-bubble.open svg.close-icon {
      display: block;
    }

    #anna-chat-bubble svg.close-icon {
      display: none;
    }

    #anna-chat-window {
      position: fixed;
      bottom: 100px;
      right: 24px;
      width: 380px;
      height: 550px;
      min-width: 300px;
      min-height: 400px;
      max-width: 600px;
      max-height: calc(100vh - 120px);
      background: rgb(10, 10, 15);
      border-radius: 16px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(3, 169, 244, 0.2);
      z-index: 999999;
      display: none;
      flex-direction: column;
      overflow: hidden;
      animation: annaSlideUp 0.3s ease;
      resize: both;
    }

    #anna-chat-window.open {
      display: flex;
    }

    #anna-resize-handle {
      position: absolute;
      top: 0;
      left: 0;
      width: 20px;
      height: 20px;
      cursor: nw-resize;
      z-index: 1000000;
    }

    #anna-resize-handle::before {
      content: '';
      position: absolute;
      top: 4px;
      left: 4px;
      width: 10px;
      height: 10px;
      border-top: 2px solid rgba(3, 169, 244, 0.5);
      border-left: 2px solid rgba(3, 169, 244, 0.5);
      border-radius: 2px 0 0 0;
    }

    #anna-resize-handle:hover::before {
      border-color: rgba(3, 169, 244, 0.8);
    }

    @keyframes annaSlideUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    #anna-chat-header {
      padding: 16px 20px;
      background: linear-gradient(135deg, rgba(3, 169, 244, 0.15), rgba(3, 169, 244, 0.05));
      border-bottom: 1px solid rgba(3, 169, 244, 0.2);
      display: flex;
      align-items: center;
      gap: 12px;
    }

    #anna-chat-header .avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #03a9f4, #0288d1);
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid rgba(3, 169, 244, 0.3);
      overflow: hidden;
    }

    #anna-chat-header .avatar img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    #anna-chat-header .info h3 {
      margin: 0;
      color: white;
      font-size: 16px;
      font-weight: 600;
    }

    #anna-chat-header .info p {
      margin: 2px 0 0;
      color: rgba(255, 255, 255, 0.6);
      font-size: 12px;
    }

    #anna-chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    #anna-chat-messages::-webkit-scrollbar {
      width: 6px;
    }

    #anna-chat-messages::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.1);
    }

    #anna-chat-messages::-webkit-scrollbar-thumb {
      background: rgba(3, 169, 244, 0.5);
      border-radius: 3px;
    }

    .anna-message-wrapper {
      display: flex;
      gap: 8px;
      animation: annaFadeIn 0.3s ease;
    }

    .anna-message-wrapper.user {
      justify-content: flex-end;
    }

    .anna-message-wrapper.assistant {
      justify-content: flex-start;
    }

    .anna-message-avatar {
      width: 28px;
      height: 28px;
      min-width: 28px;
      border-radius: 50%;
      background: linear-gradient(135deg, #03a9f4, #0288d1);
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .anna-message-avatar img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .anna-message {
      max-width: 80%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.5;
      word-wrap: break-word;
    }

    @keyframes annaFadeIn {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .anna-message.user {
      background: rgba(3, 169, 244, 0.2);
      border: 1px solid rgba(3, 169, 244, 0.3);
      color: white;
    }

    .anna-message.assistant {
      background: rgb(30, 30, 45);
      border: 1px solid rgba(3, 169, 244, 0.1);
      color: white;
    }

    .anna-message.assistant a {
      color: #03a9f4;
      text-decoration: underline;
    }

    .anna-message.assistant a:hover {
      color: #4fc3f7;
    }

    .anna-welcome {
      text-align: center;
      padding: 40px 20px;
      color: rgba(255, 255, 255, 0.7);
    }

    .anna-welcome h4 {
      margin: 0 0 8px;
      color: rgba(255, 255, 255, 0.9);
      font-size: 18px;
      font-weight: 400;
    }

    .anna-welcome p {
      margin: 0;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.5);
    }

    .anna-typing-wrapper {
      display: flex;
      gap: 8px;
      align-items: flex-start;
    }

    .anna-typing {
      display: flex;
      gap: 4px;
      padding: 12px 16px;
      background: rgb(30, 30, 45);
      border-radius: 12px;
      border: 1px solid rgba(3, 169, 244, 0.1);
    }

    .anna-typing span {
      width: 8px;
      height: 8px;
      background: rgba(3, 169, 244, 0.6);
      border-radius: 50%;
      animation: annaBounce 1.4s infinite ease-in-out;
    }

    .anna-typing span:nth-child(1) { animation-delay: 0s; }
    .anna-typing span:nth-child(2) { animation-delay: 0.2s; }
    .anna-typing span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes annaBounce {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-6px); }
    }

    #anna-chat-input-container {
      padding: 12px 16px;
      border-top: 1px solid rgba(3, 169, 244, 0.1);
      background: rgb(20, 20, 30);
    }

    #anna-chat-input-wrapper {
      display: flex;
      align-items: center;
      background: rgb(30, 30, 45);
      border: 1px solid rgba(3, 169, 244, 0.3);
      border-radius: 25px;
      overflow: hidden;
      transition: border-color 0.2s ease;
    }

    #anna-chat-input-wrapper:focus-within {
      border-color: rgba(3, 169, 244, 0.6);
      box-shadow: 0 0 0 2px rgba(3, 169, 244, 0.2);
    }

    #anna-chat-input {
      flex: 1;
      padding: 12px 16px;
      background: transparent;
      border: none;
      color: white;
      font-size: 14px;
      outline: none;
    }

    #anna-chat-input::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }

    #anna-send-btn {
      width: 36px;
      height: 36px;
      margin-right: 6px;
      border-radius: 50%;
      background: #03a9f4;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s ease, opacity 0.2s ease;
    }

    #anna-send-btn:hover {
      background: #0288d1;
    }

    #anna-send-btn:disabled {
      background: #555;
      cursor: not-allowed;
      opacity: 0.5;
    }

    #anna-send-btn svg {
      width: 16px;
      height: 16px;
      fill: none;
      stroke: white;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    #anna-powered-by {
      text-align: center;
      padding: 8px;
      font-size: 10px;
      color: rgba(255, 255, 255, 0.3);
      background: rgb(15, 15, 20);
    }

    #anna-powered-by a {
      color: rgba(3, 169, 244, 0.6);
      text-decoration: none;
    }

    #anna-new-chat-btn {
      background: transparent;
      border: none;
      cursor: pointer;
      padding: 6px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-left: auto;
      transition: background 0.2s ease;
    }

    #anna-new-chat-btn:hover {
      background: rgba(255, 255, 255, 0.1);
    }

    #anna-new-chat-btn svg {
      width: 18px;
      height: 18px;
      stroke: rgba(255, 255, 255, 0.6);
      fill: none;
      stroke-width: 2;
    }

    #anna-new-chat-btn:hover svg {
      stroke: rgba(255, 255, 255, 0.9);
    }

    @media (max-width: 480px) {
      #anna-chat-window {
        width: calc(100vw - 20px);
        height: calc(100vh - 120px);
        right: 10px;
        bottom: 90px;
        max-height: none;
        resize: none;
      }

      #anna-resize-handle {
        display: none;
      }

      #anna-chat-bubble {
        width: 54px;
        height: 54px;
        right: 16px;
        bottom: 16px;
      }
    }
  `;

  function injectStyles() {
    const styleEl = document.createElement('style');
    styleEl.id = 'anna-widget-styles';
    styleEl.textContent = styles;
    document.head.appendChild(styleEl);
  }

  let logoLoaded = false;

  function lazyLoadLogo() {
    if (logoLoaded) return;
    logoLoaded = true;
    const logoUrl = WIDGET_CONFIG.logoUrl;
    const avatars = document.querySelectorAll('#anna-widget-container .avatar img, #anna-widget-container .anna-message-avatar img');
    avatars.forEach(img => {
      if (!img.src || img.src.includes('data:')) {
        img.src = logoUrl;
      }
    });
  }

  function createWidget() {
    const container = document.createElement('div');
    container.id = 'anna-widget-container';
    container.innerHTML = `
      <button id="anna-chat-bubble" aria-label="Open chat">
        <svg class="chat-icon" viewBox="0 0 24 24">
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
        </svg>
        <svg class="close-icon" viewBox="0 0 24 24">
          <path d="M18 6L6 18M6 6l12 12" stroke="white" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
      <div id="anna-chat-window">
        <div id="anna-resize-handle" title="Drag to resize"></div>
        <div id="anna-chat-header">
          <div class="avatar"><img data-src="${WIDGET_CONFIG.logoUrl}" alt="Anna" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%2303a9f4'/%3E%3C/svg%3E" /></div>
          <div class="info">
            <h3>Anna</h3>
            <p>Your Anna Kitney Guide</p>
          </div>
          <button id="anna-new-chat-btn" title="Start new chat">
            <svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 5v14M5 12h14"/>
            </svg>
          </button>
        </div>
        <div id="anna-chat-messages">
          <div class="anna-welcome">
            <h4>Hi, I'm Anna</h4>
            <p>Your real-time guide for healing and coaching at Anna Kitney. How can I help you today?</p>
          </div>
        </div>
        <div id="anna-chat-input-container">
          <div id="anna-chat-input-wrapper">
            <input type="text" id="anna-chat-input" placeholder="Ask me anything about Anna Kitney..." />
            <button id="anna-send-btn" disabled aria-label="Send message">
              <svg viewBox="0 0 24 24">
                <path d="M14 5l7 7m0 0l-7 7m7-7H3"/>
              </svg>
            </button>
          </div>
        </div>
        <div id="anna-powered-by">
          Powered by <a href="https://annakitney.com" target="_blank">Anna Kitney</a>
        </div>
      </div>
    `;
    document.body.appendChild(container);
  }

  let sessionId = '';
  let messages = [];
  let isLoading = false;

  const STORAGE_KEY_SESSION = 'anna_session_id';
  const STORAGE_KEY_MESSAGES = 'anna_messages';
  const STORAGE_KEY_CHAT_OPEN = 'anna_chat_open';
  const STORAGE_KEY_NAV_TIME = 'anna_nav_timestamp';

  function generateSessionId() {
    return 'anna_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  function getOrCreateSessionId() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_SESSION);
      if (stored) {
        return stored;
      }
      const newId = generateSessionId();
      localStorage.setItem(STORAGE_KEY_SESSION, newId);
      return newId;
    } catch (e) {
      return generateSessionId();
    }
  }

  function saveMessagesToStorage() {
    try {
      localStorage.setItem(STORAGE_KEY_MESSAGES, JSON.stringify(messages.slice(-50)));
    } catch (e) {}
  }

  function loadMessagesFromStorage() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_MESSAGES);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {}
    return [];
  }

  function restoreMessages(storedMessages) {
    if (!storedMessages || storedMessages.length === 0) return;
    
    const messagesContainer = document.getElementById('anna-chat-messages');
    const welcome = messagesContainer.querySelector('.anna-welcome');
    if (welcome) welcome.remove();

    for (const msg of storedMessages) {
      const { cleanContent } = extractNavigationUrl(msg.content);
      
      const wrapperEl = document.createElement('div');
      wrapperEl.className = `anna-message-wrapper ${msg.role}`;
      
      if (msg.role === 'assistant') {
        const avatarEl = document.createElement('div');
        avatarEl.className = 'anna-message-avatar';
        const avatarImg = document.createElement('img');
        avatarImg.src = WIDGET_CONFIG.logoUrl;
        avatarImg.alt = 'Anna';
        avatarEl.appendChild(avatarImg);
        wrapperEl.appendChild(avatarEl);
      }
      
      const msgEl = document.createElement('div');
      msgEl.className = `anna-message ${msg.role}`;
      msgEl.appendChild(createSafeContent(cleanContent));
      wrapperEl.appendChild(msgEl);
      
      messagesContainer.appendChild(wrapperEl);
    }
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function startNewChat() {
    messages = [];
    isLoading = false;
    
    try {
      localStorage.removeItem(STORAGE_KEY_MESSAGES);
      localStorage.removeItem(STORAGE_KEY_SESSION);
      localStorage.removeItem(STORAGE_KEY_CHAT_OPEN);
      localStorage.removeItem(STORAGE_KEY_NAV_TIME);
    } catch (e) {}
    
    sessionId = generateSessionId();
    try {
      localStorage.setItem(STORAGE_KEY_SESSION, sessionId);
    } catch (e) {}
    
    const messagesContainer = document.getElementById('anna-chat-messages');
    messagesContainer.innerHTML = `
      <div class="anna-welcome">
        <h4>Hi, I'm Anna</h4>
        <p>Your real-time guide for healing and coaching at Anna Kitney. How can I help you today?</p>
      </div>
    `;
    
    hideTyping();
    const input = document.getElementById('anna-chat-input');
    input.value = '';
    updateSendButton();
    input.focus();
  }

  function shouldAutoOpenChat() {
    try {
      const wasOpen = localStorage.getItem(STORAGE_KEY_CHAT_OPEN);
      const navTime = localStorage.getItem(STORAGE_KEY_NAV_TIME);
      
      if (wasOpen === 'true' && navTime) {
        const elapsed = Date.now() - parseInt(navTime, 10);
        localStorage.removeItem(STORAGE_KEY_CHAT_OPEN);
        localStorage.removeItem(STORAGE_KEY_NAV_TIME);
        return elapsed < 10000;
      }
    } catch (e) {}
    return false;
  }

  function toggleChat() {
    const bubble = document.getElementById('anna-chat-bubble');
    const chatWindow = document.getElementById('anna-chat-window');
    const isOpen = chatWindow.classList.contains('open');
    
    if (isOpen) {
      chatWindow.classList.remove('open');
      bubble.classList.remove('open');
    } else {
      chatWindow.classList.add('open');
      bubble.classList.add('open');
      lazyLoadLogo();
      document.getElementById('anna-chat-input').focus();
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  var ALLOWED_NAVIGATION_DOMAINS = [
    'annakitney.com',
    'www.annakitney.com',
    'annakitneyportal.com',
    'www.annakitneyportal.com',
    'bit.ly'
  ];

  function isAllowedUrl(url) {
    try {
      var parsed = new URL(url);
      return ALLOWED_NAVIGATION_DOMAINS.some(function(domain) {
        return parsed.hostname === domain || parsed.hostname.endsWith('.' + domain);
      });
    } catch (e) {
      return false;
    }
  }

  function extractNavigationUrl(content) {
    var navRegex = /\[NAVIGATE:(https?:\/\/[^\]]+)\]\s*/i;
    var match = content.match(navRegex);
    var cleanContent = content.replace(navRegex, '').trim();
    
    if (match) {
      var url = match[1];
      if (isAllowedUrl(url)) {
        return { url: url, cleanContent: cleanContent };
      }
      console.warn('Navigation blocked: URL not in allowlist', url);
    }
    
    return { url: null, cleanContent: cleanContent };
  }

  function performNavigation(url) {
    if (!isAllowedUrl(url)) {
      console.warn('Navigation blocked: URL not in allowlist', url);
      return;
    }
    try {
      localStorage.setItem(STORAGE_KEY_CHAT_OPEN, 'true');
      localStorage.setItem(STORAGE_KEY_NAV_TIME, Date.now().toString());
    } catch (e) {}
    window.location.href = url;
  }

  function createSafeContent(text) {
    const container = document.createDocumentFragment();
    
    // Split by newlines first to handle line breaks
    const lines = text.split('\n');
    
    lines.forEach((line, lineIndex) => {
      // Add line break between lines (not before first line)
      if (lineIndex > 0) {
        container.appendChild(document.createElement('br'));
      }
      
      // Skip empty lines but still add the br
      if (line.trim() === '') {
        return;
      }
      
      // Process each line for bold, links, and URLs
      // Combined regex for: **bold**, [text](url), and raw URLs
      const combinedRegex = /(\*\*([^*]+)\*\*)|(\[([^\]]+)\]\(([^)]+)\))|(https?:\/\/[^\s<>"\)]+)/g;
      let lastIndex = 0;
      let match;

      while ((match = combinedRegex.exec(line)) !== null) {
        if (match.index > lastIndex) {
          const textBefore = line.substring(lastIndex, match.index);
          container.appendChild(document.createTextNode(textBefore));
        }
        
        if (match[1]) {
          // Bold text: **text**
          const boldText = match[2];
          const strong = document.createElement('strong');
          strong.textContent = boldText;
          container.appendChild(strong);
        } else if (match[3]) {
          // Markdown link: [text](url)
          const linkText = match[4];
          const linkUrl = match[5];
          const link = document.createElement('a');
          link.href = linkUrl;
          link.textContent = linkText;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.style.color = '#03a9f4';
          link.style.textDecoration = 'underline';
          container.appendChild(link);
        } else if (match[6]) {
          // Raw URL
          const plainUrl = match[6];
          const link = document.createElement('a');
          link.href = plainUrl;
          link.textContent = plainUrl;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.style.color = '#03a9f4';
          link.style.textDecoration = 'underline';
          container.appendChild(link);
        }
        
        lastIndex = combinedRegex.lastIndex;
      }
      
      if (lastIndex < line.length) {
        container.appendChild(document.createTextNode(line.substring(lastIndex)));
      }
    });
    
    return container;
  }


  function addMessage(role, content, skipNavigation = false) {
    const messagesContainer = document.getElementById('anna-chat-messages');
    const welcome = messagesContainer.querySelector('.anna-welcome');
    if (welcome) welcome.remove();

    const { url: navigationUrl, cleanContent } = extractNavigationUrl(content);
    const displayContent = cleanContent;

    const wrapperEl = document.createElement('div');
    wrapperEl.className = `anna-message-wrapper ${role}`;
    
    if (role === 'assistant') {
      const avatarEl = document.createElement('div');
      avatarEl.className = 'anna-message-avatar';
      const avatarImg = document.createElement('img');
      avatarImg.src = WIDGET_CONFIG.logoUrl;
      avatarImg.alt = 'Anna';
      avatarEl.appendChild(avatarImg);
      wrapperEl.appendChild(avatarEl);
    }
    
    const msgEl = document.createElement('div');
    msgEl.className = `anna-message ${role}`;
    msgEl.appendChild(createSafeContent(displayContent));
    wrapperEl.appendChild(msgEl);
    
    if (role === 'assistant' && navigationUrl && !skipNavigation) {
      const navIndicator = document.createElement('div');
      navIndicator.className = 'anna-nav-indicator';
      navIndicator.innerHTML = '<span style="color: #03a9f4; font-size: 12px; display: flex; align-items: center; gap: 4px; margin-top: 8px;"><svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>Navigating...</span>';
      msgEl.appendChild(navIndicator);
      
      setTimeout(function() {
        performNavigation(navigationUrl);
      }, 1500);
    }
    
    messagesContainer.appendChild(wrapperEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return msgEl;
  }

  function updateMessageContent(msgEl, content) {
    const { cleanContent } = extractNavigationUrl(content);
    msgEl.innerHTML = '';
    msgEl.appendChild(createSafeContent(cleanContent));
  }

  function showTyping() {
    const messagesContainer = document.getElementById('anna-chat-messages');
    const typingWrapper = document.createElement('div');
    typingWrapper.className = 'anna-typing-wrapper';
    typingWrapper.id = 'anna-typing-indicator';
    
    const avatarEl = document.createElement('div');
    avatarEl.className = 'anna-message-avatar';
    const avatarImg = document.createElement('img');
    avatarImg.src = WIDGET_CONFIG.logoUrl;
    avatarImg.alt = 'Anna';
    avatarEl.appendChild(avatarImg);
    typingWrapper.appendChild(avatarEl);
    
    const typingEl = document.createElement('div');
    typingEl.className = 'anna-typing';
    typingEl.innerHTML = '<span></span><span></span><span></span>';
    typingWrapper.appendChild(typingEl);
    
    messagesContainer.appendChild(typingWrapper);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function hideTyping() {
    const typing = document.getElementById('anna-typing-indicator');
    if (typing) typing.remove();
  }

  function updateSendButton() {
    const input = document.getElementById('anna-chat-input');
    const btn = document.getElementById('anna-send-btn');
    btn.disabled = !input.value.trim() || isLoading;
  }

  function initResize() {
    const resizeHandle = document.getElementById('anna-resize-handle');
    const chatWindow = document.getElementById('anna-chat-window');
    
    if (!resizeHandle || !chatWindow) return;
    
    let isResizing = false;
    let startX, startY, startWidth, startHeight, startRight, startBottom;
    
    resizeHandle.addEventListener('mousedown', (e) => {
      isResizing = true;
      startX = e.clientX;
      startY = e.clientY;
      startWidth = chatWindow.offsetWidth;
      startHeight = chatWindow.offsetHeight;
      
      const rect = chatWindow.getBoundingClientRect();
      startRight = window.innerWidth - rect.right;
      startBottom = window.innerHeight - rect.bottom;
      
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'nw-resize';
      
      e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
      if (!isResizing) return;
      
      const deltaX = startX - e.clientX;
      const deltaY = startY - e.clientY;
      
      const newWidth = Math.max(300, Math.min(600, startWidth + deltaX));
      const newHeight = Math.max(400, Math.min(window.innerHeight - 120, startHeight + deltaY));
      
      chatWindow.style.width = newWidth + 'px';
      chatWindow.style.height = newHeight + 'px';
    });
    
    document.addEventListener('mouseup', () => {
      if (isResizing) {
        isResizing = false;
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
      }
    });
    
    resizeHandle.addEventListener('touchstart', (e) => {
      const touch = e.touches[0];
      isResizing = true;
      startX = touch.clientX;
      startY = touch.clientY;
      startWidth = chatWindow.offsetWidth;
      startHeight = chatWindow.offsetHeight;
      e.preventDefault();
    });
    
    document.addEventListener('touchmove', (e) => {
      if (!isResizing) return;
      const touch = e.touches[0];
      
      const deltaX = startX - touch.clientX;
      const deltaY = startY - touch.clientY;
      
      const newWidth = Math.max(300, Math.min(600, startWidth + deltaX));
      const newHeight = Math.max(400, Math.min(window.innerHeight - 120, startHeight + deltaY));
      
      chatWindow.style.width = newWidth + 'px';
      chatWindow.style.height = newHeight + 'px';
    });
    
    document.addEventListener('touchend', () => {
      isResizing = false;
    });
  }

  async function sendMessage() {
    const input = document.getElementById('anna-chat-input');
    const content = input.value.trim();
    
    if (!content || isLoading) return;

    isLoading = true;
    input.value = '';
    updateSendButton();

    addMessage('user', content);
    messages.push({ role: 'user', content });
    saveMessagesToStorage();

    showTyping();

    try {
      const response = await fetch(WIDGET_CONFIG.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          session_id: sessionId,
          conversation_history: messages.slice(-10).map(m => ({ role: m.role, content: m.content })),
          user: null
        }),
      });

      if (!response.ok) throw new Error('Request failed');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamedContent = '';
      let assistantMsgEl = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'content') {
                hideTyping();
                streamedContent += data.content;
                
                if (!assistantMsgEl) {
                  assistantMsgEl = addMessage('assistant', streamedContent, true);
                } else {
                  updateMessageContent(assistantMsgEl, streamedContent);
                }
                
                const container = document.getElementById('anna-chat-messages');
                container.scrollTop = container.scrollHeight;
              } else if (data.type === 'done') {
                const finalContent = data.full_response || streamedContent;
                const { url: navigationUrl, cleanContent } = extractNavigationUrl(finalContent);
                
                if (assistantMsgEl) {
                  assistantMsgEl.innerHTML = '';
                  assistantMsgEl.appendChild(createSafeContent(cleanContent));
                  
                  if (navigationUrl) {
                    const navIndicator = document.createElement('div');
                    navIndicator.className = 'anna-nav-indicator';
                    navIndicator.innerHTML = '<span style="color: #03a9f4; font-size: 12px; display: flex; align-items: center; gap: 4px; margin-top: 8px;"><svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>Navigating...</span>';
                    assistantMsgEl.appendChild(navIndicator);
                    
                    setTimeout(function() {
                      performNavigation(navigationUrl);
                    }, 1500);
                  }
                }
                messages.push({ role: 'assistant', content: finalContent });
                saveMessagesToStorage();
              }
            } catch (e) {}
          }
        }
      }

      if (!assistantMsgEl && streamedContent) {
        addMessage('assistant', streamedContent);
        messages.push({ role: 'assistant', content: streamedContent });
        saveMessagesToStorage();
      }

    } catch (error) {
      console.error('Anna Widget Error:', error);
      hideTyping();
      addMessage('assistant', 'I apologize, but I encountered a connection issue. Please try again.');
    } finally {
      isLoading = false;
      hideTyping();
      updateSendButton();
    }
  }

  function initWidget() {
    if (document.getElementById('anna-widget-container')) return;

    injectStyles();
    createWidget();
    sessionId = getOrCreateSessionId();

    const storedMessages = loadMessagesFromStorage();
    if (storedMessages.length > 0) {
      messages = storedMessages;
      restoreMessages(storedMessages);
    }

    document.getElementById('anna-chat-bubble').addEventListener('click', toggleChat);
    document.getElementById('anna-new-chat-btn').addEventListener('click', startNewChat);
    
    const input = document.getElementById('anna-chat-input');
    input.addEventListener('input', updateSendButton);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    document.getElementById('anna-send-btn').addEventListener('click', sendMessage);
    
    initResize();
    
    if (shouldAutoOpenChat()) {
      const bubble = document.getElementById('anna-chat-bubble');
      const chatWindow = document.getElementById('anna-chat-window');
      chatWindow.classList.add('open');
      bubble.classList.add('open');
      lazyLoadLogo();
      
      setTimeout(function() {
        const messagesContainer = document.getElementById('anna-chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }, 100);
    }
  }

  function deferInit() {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(initWidget, { timeout: 500 });
    } else {
      setTimeout(initWidget, 0);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', deferInit);
  } else {
    deferInit();
  }
})();
