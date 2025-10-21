/**
 * SonjayOS AI助手 GNOME扩展
 * 提供智能助手界面和AI交互功能
 */

const { GObject, St, Clutter, GLib, Gio, Meta } = imports.gi;
const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();
const Main = imports.ui.main;
const PanelMenu = imports.ui.panelMenu;
const PopupMenu = imports.ui.popupMenu;
const MessageTray = imports.ui.messageTray;

// AI助手类
var SonjayOSAIAssistant = GObject.registerClass(
class SonjayOSAIAssistant extends PanelMenu.Button {
    _init() {
        super._init(0.0, 'SonjayOS AI助手');
        
        this._aiService = null;
        this._isListening = false;
        this._isProcessing = false;
        this._conversationHistory = [];
        this._settings = null;
        
        this._initUI();
        this._loadSettings();
        this._connectToAIService();
    }
    
    _initUI() {
        // 创建主图标
        this._icon = new St.Icon({
            icon_name: 'sonjayos-ai',
            style_class: 'system-status-icon'
        });
        
        // 创建状态指示器
        this._statusIndicator = new St.Icon({
            icon_name: 'audio-input-microphone',
            style_class: 'ai-status-icon'
        });
        this._statusIndicator.hide();
        
        // 创建容器
        this._container = new St.BoxLayout({
            vertical: false,
            style_class: 'ai-assistant-container'
        });
        
        this._container.add_child(this._icon);
        this._container.add_child(this._statusIndicator);
        this.add_child(this._container);
        
        // 创建菜单
        this._createMenu();
        
        // 添加样式
        this._addStyles();
    }
    
    _createMenu() {
        // 创建主菜单项
        this._mainMenuItem = new PopupMenu.PopupMenuItem('AI助手');
        this._mainMenuItem.actor.add_style_class_name('ai-main-menu-item');
        this.menu.addMenuItem(this._mainMenuItem);
        
        // 添加分隔符
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        // 语音输入项
        this._voiceItem = new PopupMenu.PopupMenuItem('🎤 语音输入');
        this._voiceItem.connect('activate', () => this._toggleVoiceInput());
        this.menu.addMenuItem(this._voiceItem);
        
        // 文本输入项
        this._textItem = new PopupMenu.PopupMenuItem('✏️ 文本输入');
        this._textItem.connect('activate', () => this._showTextInput());
        this.menu.addMenuItem(this._textItem);
        
        // 历史记录项
        this._historyItem = new PopupMenu.PopupMenuItem('📜 对话历史');
        this._historyItem.connect('activate', () => this._showHistory());
        this.menu.addMenuItem(this._historyItem);
        
        // 设置项
        this._settingsItem = new PopupMenu.PopupMenuItem('⚙️ 设置');
        this._settingsItem.connect('activate', () => this._showSettings());
        this.menu.addMenuItem(this._settingsItem);
        
        // 添加分隔符
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        // 状态项
        this._statusItem = new PopupMenu.PopupMenuItem('状态: 就绪');
        this._statusItem.actor.add_style_class_name('ai-status-item');
        this.menu.addMenuItem(this._statusItem);
    }
    
    _addStyles() {
        // 添加CSS样式
        const stylesheet = `
            .ai-assistant-container {
                spacing: 4px;
            }
            
            .ai-status-icon {
                color: #4CAF50;
                icon-size: 12px;
            }
            
            .ai-status-icon.listening {
                color: #FF5722;
                animation: pulse 1s infinite;
            }
            
            .ai-status-icon.processing {
                color: #2196F3;
                animation: spin 1s linear infinite;
            }
            
            .ai-main-menu-item {
                font-weight: bold;
                font-size: 14px;
            }
            
            .ai-status-item {
                font-size: 12px;
                color: #666;
            }
            
            .ai-conversation-item {
                padding: 8px;
                margin: 4px 0;
                background-color: #f5f5f5;
                border-radius: 4px;
            }
            
            .ai-user-message {
                text-align: right;
                color: #2196F3;
            }
            
            .ai-assistant-message {
                text-align: left;
                color: #4CAF50;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        
        const themeContext = St.ThemeContext.get_for_stage(global.stage);
        themeContext.load_stylesheet(stylesheet);
    }
    
    _loadSettings() {
        this._settings = ExtensionUtils.getSettings();
        
        // 监听设置变化
        this._settings.connect('changed', (settings, key) => {
            this._onSettingsChanged(key);
        });
    }
    
    _onSettingsChanged(key) {
        switch (key) {
            case 'auto-listen':
                this._updateVoiceInputState();
                break;
            case 'ai-model':
                this._reconnectToAIService();
                break;
            case 'theme':
                this._updateTheme();
                break;
        }
    }
    
    _connectToAIService() {
        // 连接到AI服务
        try {
            this._aiService = new Gio.DBusProxy({
                g_connection: Gio.DBus.system,
                g_name: 'com.sonjayos.ai',
                g_object_path: '/com/sonjayos/ai',
                g_interface_name: 'com.sonjayos.ai.Service'
            });
            
            this._aiService.connect('g-signal', (proxy, sender, signal, params) => {
                this._onAISignal(signal, params);
            });
            
            log('AI服务连接成功');
        } catch (error) {
            log(`AI服务连接失败: ${error.message}`);
        }
    }
    
    _onAISignal(signal, params) {
        switch (signal) {
            case 'RecognitionResult':
                this._onRecognitionResult(params[0], params[1]);
                break;
            case 'ProcessingComplete':
                this._onProcessingComplete(params[0]);
                break;
            case 'Error':
                this._onAIError(params[0]);
                break;
        }
    }
    
    _toggleVoiceInput() {
        if (this._isListening) {
            this._stopVoiceInput();
        } else {
            this._startVoiceInput();
        }
    }
    
    _startVoiceInput() {
        if (this._isListening) return;
        
        try {
            this._aiService.StartListeningRemote();
            this._isListening = true;
            this._updateStatus('正在监听...');
            this._statusIndicator.show();
            this._statusIndicator.add_style_class_name('listening');
            
            // 显示通知
            this._showNotification('AI助手', '开始语音监听', 'audio-input-microphone');
            
        } catch (error) {
            log(`启动语音输入失败: ${error.message}`);
            this._showNotification('错误', '无法启动语音输入', 'dialog-error');
        }
    }
    
    _stopVoiceInput() {
        if (!this._isListening) return;
        
        try {
            this._aiService.StopListeningRemote();
            this._isListening = false;
            this._updateStatus('处理中...');
            this._statusIndicator.remove_style_class_name('listening');
            this._statusIndicator.add_style_class_name('processing');
            
        } catch (error) {
            log(`停止语音输入失败: ${error.message}`);
        }
    }
    
    _onRecognitionResult(text, confidence) {
        log(`识别结果: ${text} (置信度: ${confidence})`);
        
        this._isListening = false;
        this._statusIndicator.remove_style_class_name('listening');
        this._statusIndicator.add_style_class_name('processing');
        
        // 添加到对话历史
        this._conversationHistory.push({
            type: 'user',
            content: text,
            timestamp: Date.now()
        });
        
        this._updateStatus('处理中...');
    }
    
    _onProcessingComplete(response) {
        log(`AI响应: ${response}`);
        
        this._isProcessing = false;
        this._statusIndicator.hide();
        this._statusIndicator.remove_style_class_name('processing');
        
        // 添加到对话历史
        this._conversationHistory.push({
            type: 'assistant',
            content: response,
            timestamp: Date.now()
        });
        
        this._updateStatus('就绪');
        
        // 显示通知
        this._showNotification('AI助手', response.substring(0, 100) + '...', 'sonjayos-ai');
        
        // 执行AI命令
        this._executeAICommand(response);
    }
    
    _onAIError(error) {
        log(`AI错误: ${error}`);
        
        this._isListening = false;
        this._isProcessing = false;
        this._statusIndicator.hide();
        this._statusIndicator.remove_style_class_name('listening');
        this._statusIndicator.remove_style_class_name('processing');
        
        this._updateStatus('错误');
        this._showNotification('AI错误', error, 'dialog-error');
    }
    
    _executeAICommand(response) {
        // 解析AI响应并执行相应命令
        const commands = this._parseAICommands(response);
        
        commands.forEach(command => {
            this._executeCommand(command);
        });
    }
    
    _parseAICommands(response) {
        const commands = [];
        
        // 解析文件操作命令
        if (response.includes('打开文件') || response.includes('打开文档')) {
            const fileMatch = response.match(/打开(.+?)(?:文件|文档)/);
            if (fileMatch) {
                commands.push({
                    type: 'open_file',
                    target: fileMatch[1].trim()
                });
            }
        }
        
        // 解析应用程序命令
        if (response.includes('打开应用') || response.includes('启动')) {
            const appMatch = response.match(/打开(.+?)应用|启动(.+?)/);
            if (appMatch) {
                commands.push({
                    type: 'open_app',
                    target: (appMatch[1] || appMatch[2]).trim()
                });
            }
        }
        
        // 解析系统命令
        if (response.includes('优化系统') || response.includes('清理')) {
            commands.push({
                type: 'system_optimize'
            });
        }
        
        return commands;
    }
    
    _executeCommand(command) {
        switch (command.type) {
            case 'open_file':
                this._openFile(command.target);
                break;
            case 'open_app':
                this._openApplication(command.target);
                break;
            case 'system_optimize':
                this._optimizeSystem();
                break;
        }
    }
    
    _openFile(filename) {
        try {
            const file = Gio.File.new_for_path(filename);
            if (file.query_exists(null)) {
                Gio.AppInfo.launch_default_for_uri(file.get_uri(), null);
                this._showNotification('文件操作', `已打开文件: ${filename}`, 'document-open');
            } else {
                this._showNotification('错误', `文件不存在: ${filename}`, 'dialog-error');
            }
        } catch (error) {
            log(`打开文件失败: ${error.message}`);
        }
    }
    
    _openApplication(appName) {
        try {
            const appInfo = Gio.AppInfo.get_default_for_type('application/x-desktop', false);
            if (appInfo) {
                appInfo.launch([], null);
                this._showNotification('应用程序', `已启动: ${appName}`, 'application-x-executable');
            }
        } catch (error) {
            log(`启动应用程序失败: ${error.message}`);
        }
    }
    
    _optimizeSystem() {
        // 执行系统优化
        this._showNotification('系统优化', '正在执行系统优化...', 'system-run');
        
        // 这里可以调用系统优化脚本
        GLib.spawn_command_line_async('sonjayos-optimize');
    }
    
    _showTextInput() {
        // 显示文本输入对话框
        const dialog = new St.BoxLayout({
            vertical: true,
            style_class: 'ai-text-input-dialog'
        });
        
        const input = new St.Entry({
            text: '',
            hint_text: '输入您的问题或命令...'
        });
        
        const button = new St.Button({
            label: '发送',
            style_class: 'ai-send-button'
        });
        
        button.connect('clicked', () => {
            const text = input.get_text();
            if (text.trim()) {
                this._processTextInput(text);
                dialog.destroy();
            }
        });
        
        dialog.add_child(input);
        dialog.add_child(button);
        
        // 显示对话框
        Main.uiGroup.add_child(dialog);
    }
    
    _processTextInput(text) {
        this._conversationHistory.push({
            type: 'user',
            content: text,
            timestamp: Date.now()
        });
        
        this._updateStatus('处理中...');
        this._statusIndicator.show();
        this._statusIndicator.add_style_class_name('processing');
        
        // 发送到AI服务
        try {
            this._aiService.ProcessTextRemote(text);
        } catch (error) {
            log(`处理文本输入失败: ${error.message}`);
        }
    }
    
    _showHistory() {
        // 显示对话历史
        const historyDialog = new St.BoxLayout({
            vertical: true,
            style_class: 'ai-history-dialog'
        });
        
        this._conversationHistory.forEach(entry => {
            const item = new St.BoxLayout({
                vertical: true,
                style_class: `ai-conversation-item ${entry.type}-message`
            });
            
            const content = new St.Label({
                text: entry.content,
                style_class: 'ai-message-content'
            });
            
            const timestamp = new St.Label({
                text: new Date(entry.timestamp).toLocaleString(),
                style_class: 'ai-message-timestamp'
            });
            
            item.add_child(content);
            item.add_child(timestamp);
            historyDialog.add_child(item);
        });
        
        // 显示历史对话框
        Main.uiGroup.add_child(historyDialog);
    }
    
    _showSettings() {
        // 显示设置对话框
        const settingsDialog = new St.BoxLayout({
            vertical: true,
            style_class: 'ai-settings-dialog'
        });
        
        // 添加设置选项
        const autoListenToggle = new St.Switch({
            active: this._settings.get_boolean('auto-listen')
        });
        
        autoListenToggle.connect('notify::active', (switch_) => {
            this._settings.set_boolean('auto-listen', switch_.active);
        });
        
        settingsDialog.add_child(new St.Label({ text: '自动监听' }));
        settingsDialog.add_child(autoListenToggle);
        
        // 显示设置对话框
        Main.uiGroup.add_child(settingsDialog);
    }
    
    _updateStatus(status) {
        this._statusItem.label.text = `状态: ${status}`;
    }
    
    _showNotification(title, message, icon) {
        const source = new MessageTray.Source('SonjayOS AI', icon);
        const notification = new MessageTray.Notification(source, title, message);
        
        source.connect('destroy', () => {
            Main.messageTray.remove(source);
        });
        
        Main.messageTray.add(source);
        source.showNotification(notification);
    }
    
    _updateTheme() {
        const theme = this._settings.get_string('theme');
        // 更新主题相关样式
        this._container.remove_style_class_name('light-theme');
        this._container.remove_style_class_name('dark-theme');
        this._container.add_style_class_name(`${theme}-theme`);
    }
    
    _reconnectToAIService() {
        this._connectToAIService();
    }
    
    _updateVoiceInputState() {
        if (this._settings.get_boolean('auto-listen')) {
            this._startVoiceInput();
        } else {
            this._stopVoiceInput();
        }
    }
});

// 扩展初始化
function init() {
    return new SonjayOSAIAssistant();
}

// 扩展启用
function enable() {
    Main.panel.addToStatusArea('sonjayos-ai-assistant', new SonjayOSAIAssistant());
}

// 扩展禁用
function disable() {
    // 清理资源
}
