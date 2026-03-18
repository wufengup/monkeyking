let currentConfig = "";
let currentSoul = "";
let currentTab = "soul";
let ws = null;
let currentAgentMessageDiv = null;
let currentAgentNameText = "MonkeyKing";

const chatHistory = document.getElementById('chat-history');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const agentList = document.getElementById('agent-list');
const currentAgentName = document.getElementById('current-agent-name');
const configContent = document.getElementById('config-content');

const uploadBtn = document.getElementById('upload-btn');
const imageUpload = document.getElementById('image-upload');
const imagePreviewArea = document.getElementById('image-preview-area');
const imagePreview = document.getElementById('image-preview');
const clearImageBtn = document.getElementById('clear-image-btn');
let currentImageBase64 = null;

// 初始化
async function init() {
    await fetchAgents();
    // 默认连接到 MonkeyKing
    connectWebSocket("MonkeyKing");
    await fetchConfig("MonkeyKing");
    
    // 事件监听
    document.getElementById('refresh-agents-btn').addEventListener('click', fetchAgents);
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 图片上传事件
    uploadBtn.addEventListener('click', () => imageUpload.click());
    imageUpload.addEventListener('change', handleImageSelect);
    clearImageBtn.addEventListener('click', clearImage);
}

function handleImageSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // 上传图片到后端获取 base64/url
    uploadImage(file);
}

async function uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        appendSystemMessage("正在上传图片...");
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) throw new Error("Upload failed");
        
        const data = await res.json();
        currentImageBase64 = data.url;
        
        // 显示预览
        imagePreview.src = currentImageBase64;
        imagePreviewArea.style.display = 'flex';
        
        // 移除上传中提示
        chatHistory.lastElementChild.remove();
        
    } catch (e) {
        appendSystemMessage(`图片上传失败: ${e.message}`);
    }
    
    // 清空 input，允许再次选择同一文件
    imageUpload.value = '';
}

function clearImage() {
    currentImageBase64 = null;
    imagePreview.src = '';
    imagePreviewArea.style.display = 'none';
}

// 切换 Tab
window.switchTab = function(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    renderConfig();
}

function renderConfig() {
    if (currentTab === 'soul') {
        configContent.innerHTML = `<strong>Soul 文件路径:</strong><br>${currentSoul || "无"}`;
    } else {
        configContent.innerHTML = `<strong>Config 文件路径:</strong><br>${currentConfig || "无"}`;
    }
}

async function fetchAgents() {
    try {
        const res = await fetch('/api/agents');
        const data = await res.json();
        
        // 渲染列表
        agentList.innerHTML = '';
        data.agents.forEach(agent => {
            const li = document.createElement('li');
            li.textContent = agent;
            if (agent === currentAgentNameText) {
                li.classList.add('active');
            }
            li.onclick = () => {
                switchAgent(agent);
            };
            agentList.appendChild(li);
        });
    } catch (e) {
        console.error("Failed to fetch agents", e);
    }
}

async function fetchConfig(agentName) {
    try {
        const res = await fetch(`/api/agent/config?name=${agentName}`);
        const data = await res.json();
        currentConfig = data.config_path;
        currentSoul = data.soul_path;
        renderConfig();
    } catch (e) {
        console.error("Failed to fetch config", e);
    }
}

function switchAgent(name) {
    if (name === currentAgentNameText) return;
    
    currentAgentNameText = name;
    currentAgentName.textContent = name;
    
    // 更新列表样式
    document.querySelectorAll('#agent-list li').forEach(li => {
        li.classList.toggle('active', li.textContent === name);
    });
    
    // 重新获取配置
    fetchConfig(name);
    
    // 断开旧连接，并屏蔽其 onclose 回调，防止误报断开
    if (ws) {
        ws.onclose = null;
        ws.close();
    }
    chatHistory.innerHTML = ''; // 清空聊天记录
    appendSystemMessage(`正在连接分身: ${name}...`);
    connectWebSocket(name);
}

function connectWebSocket(agentName) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // 连接到特定 Agent 的 WebSocket
    ws = new WebSocket(`${protocol}//${window.location.host}/api/ws/chat/${agentName}`);
    
    ws.onopen = () => {
        appendSystemMessage(`已连接到 ${agentName} 🔌`);
        sendBtn.disabled = false;
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleAgentEvent(data);
    };
    
    ws.onclose = () => {
        appendSystemMessage("连接已断开 ❌");
        sendBtn.disabled = true;
    };
}

function handleAgentEvent(data) {
    if (data.type === 'message') {
        // 最终回复
        appendAgentMessage(data.content);
        currentAgentMessageDiv = null; // 重置当前消息块
        sendBtn.disabled = false;
        chatInput.focus();
    } else if (data.type === 'history') {
        // 加载历史记录
        chatHistory.innerHTML = '';
        appendSystemMessage(`已加载与 ${currentAgentNameText} 的最近对话记录`);
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                if (msg.role === 'User') {
                    appendUserMessage(msg.content);
                } else {
                    appendAgentMessage(msg.content);
                    currentAgentMessageDiv = null;
                }
            });
        }
    } else if (data.type === 'thought') {
        ensureAgentMessageDiv();
        const thoughtDiv = document.createElement('div');
        thoughtDiv.className = 'thought-process';
        thoughtDiv.innerHTML = `<strong>[思考中]</strong><br>${marked.parse(data.content)}`;
        currentAgentMessageDiv.appendChild(thoughtDiv);
        scrollToBottom();
    } else if (data.type === 'tool_start') {
        ensureAgentMessageDiv();
        const toolDiv = document.createElement('div');
        toolDiv.className = 'tool-call';
        toolDiv.innerHTML = `🛠️ <strong>调用法宝:</strong> ${data.name}<br>📦 <strong>参数:</strong> ${JSON.stringify(data.args)}`;
        currentAgentMessageDiv.appendChild(toolDiv);
        scrollToBottom();
    } else if (data.type === 'error') {
        appendSystemMessage(`[错误] ${data.content}`);
        sendBtn.disabled = false;
    }
}

function ensureAgentMessageDiv() {
    if (!currentAgentMessageDiv) {
        currentAgentMessageDiv = document.createElement('div');
        currentAgentMessageDiv.className = 'message agent';
        chatHistory.appendChild(currentAgentMessageDiv);
    }
}

function sendMessage() {
    const text = chatInput.value.trim();
    if ((!text && !currentImageBase64) || !ws || ws.readyState !== WebSocket.OPEN) return;
    
    // 构建消息 payload
    let payload;
    if (currentImageBase64) {
        // 多模态消息结构
        payload = { 
            query: [
                { type: "text", text: text || "请分析这张图片" },
                { type: "image_url", image_url: { url: currentImageBase64 } }
            ]
        };
        // 在 UI 上显示图片和文字
        appendUserMessageWithImage(text, currentImageBase64);
        clearImage();
    } else {
        // 纯文本消息
        payload = { query: text };
        appendUserMessage(text);
    }
    
    chatInput.value = '';
    sendBtn.disabled = true;
    
    ws.send(JSON.stringify(payload));
}

function appendUserMessageWithImage(text, imageUrl) {
    const div = document.createElement('div');
    div.className = 'message user';
    let contentHtml = '';
    if (imageUrl) {
        contentHtml += `<img src="${imageUrl}" alt="Uploaded Image">`;
    }
    if (text) {
        contentHtml += `<p>${text}</p>`;
    }
    div.innerHTML = contentHtml;
    chatHistory.appendChild(div);
    scrollToBottom();
}

function appendUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'message user';
    div.textContent = text;
    chatHistory.appendChild(div);
    scrollToBottom();
}

function appendAgentMessage(text) {
    ensureAgentMessageDiv();
    const contentDiv = document.createElement('div');
    contentDiv.innerHTML = marked.parse(text);
    currentAgentMessageDiv.appendChild(contentDiv);
    scrollToBottom();
}

function appendSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'message system';
    div.textContent = text;
    chatHistory.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

init();