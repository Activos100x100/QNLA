/**
 * FTRA - Sistema de Procesamiento de Facturas
 * JavaScript Principal
 */

// ============================================
// TEMA (Claro/Oscuro)
// ============================================

class ThemeManager {
    constructor() {
        this.htmlElement = document.documentElement;
        this.themeToggleBtn = document.getElementById('themeToggle');
        this.init();
    }

    init() {
        // Cargar tema guardado o detectar preferencia del sistema
        const savedTheme = localStorage.getItem('app-theme');
        const systemTheme = this.getSystemTheme();
        const initialTheme = savedTheme || systemTheme;

        this.setTheme(initialTheme);

        // Event listener para el botón
        if (this.themeToggleBtn) {
            this.themeToggleBtn.addEventListener('click', () => this.toggleTheme());
        }

        // Detectar cambios en preferencia del sistema
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('app-theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    setTheme(theme) {
        this.htmlElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('app-theme', theme);

        // Actualizar icono del botón
        if (this.themeToggleBtn) {
            const icon = this.themeToggleBtn.querySelector('i');
            if (icon) {
                icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
            }
        }
    }

    toggleTheme() {
        const currentTheme = this.htmlElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }
}

// ============================================
// SIDEBAR MOBILE
// ============================================

class SidebarManager {
    constructor() {
        this.sidebar = document.querySelector('.sidebar');
        this.toggleBtn = document.getElementById('sidebarToggleBtn');
        this.closeBtn = document.getElementById('sidebarToggle');
        this.init();
    }

    init() {
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggle());
        }

        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.close());
        }

        // Cerrar sidebar al hacer clic en un link (en móvil)
        document.querySelectorAll('.sidebar .nav-link:not(.collapsed)').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    this.close();
                }
            });
        });

        // Cerrar sidebar al hacer clic afuera
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                if (!this.sidebar.contains(e.target) && !this.toggleBtn.contains(e.target)) {
                    this.close();
                }
            }
        });
    }

    toggle() {
        this.sidebar.classList.toggle('show');
    }

    close() {
        this.sidebar.classList.remove('show');
    }
}

// ============================================
// NOTIFICACIONES
// ============================================

class NotificationManager {
    constructor() {
        this.notificationBtn = document.getElementById('notificationBtn');
        this.notificationModal = document.getElementById('notificationModal');
        this.init();
    }

    init() {
        if (this.notificationBtn) {
            this.notificationBtn.addEventListener('click', () => {
                const modal = new bootstrap.Modal(this.notificationModal);
                modal.show();
            });
        }
    }

    show(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const pageWrapper = document.querySelector('.page-wrapper');
        if (pageWrapper) {
            pageWrapper.insertBefore(alertDiv, pageWrapper.firstChild);

            // Auto-cerrar después de 5 segundos
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 300);
            }, 5000);
        }
    }

    updateBadge(count) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = count;
            if (count === 0) {
                badge.style.display = 'none';
            } else {
                badge.style.display = 'inline-block';
            }
        }
    }
}

// ============================================
// WEBSOCKET
// ============================================

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.url = this.getWebSocketURL();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.init();
    }

    getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws`;
    }

    init() {
        if (!this.isWebSocketSupported()) {
            console.warn('WebSocket no soportado');
            return;
        }

        this.connect();
    }

    connect() {
        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('WebSocket conectado');
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };

            this.ws.onerror = (error) => {
                console.error('Error en WebSocket:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket desconectado');
                this.reconnect();
            };
        } catch (error) {
            console.error('Error al conectar WebSocket:', error);
            this.reconnect();
        }
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * this.reconnectAttempts;
            console.log(`Reconectando en ${delay}ms...`);
            setTimeout(() => this.connect(), delay);
        }
    }

    handleMessage(message) {
        const { type, data } = message;

        switch (type) {
            case 'status_update':
                this.handleStatusUpdate(data);
                break;
            case 'notification':
                notificationManager.show(data.message, data.type);
                break;
            case 'comentario_nuevo':
                this.handleNuevoComentario(data);
                break;
            case 'comentario_resuelto':
                this.handleComentarioResuelto(data);
                break;
            case 'error':
                notificationManager.show(data.message, 'danger');
                break;
            default:
                console.log('Mensaje desconocido:', message);
        }

        // Disparar evento personalizado
        window.dispatchEvent(new CustomEvent('ws-message', { detail: message }));
    }

    handleNuevoComentario(data) {
        // Recargar comentarios si el ComentariosManager está inicializado
        if (window.comentariosManager) {
            window.comentariosManager.cargarComentarios();
            notificationManager.show(`Nuevo comentario de ${data.usuario}`, 'info');
        }
    }

    handleComentarioResuelto(data) {
        if (window.comentariosManager) {
            window.comentariosManager.cargarComentarios();
            notificationManager.show(`Comentario resuelto por ${data.usuario}`, 'success');
        }
    }

    handleStatusUpdate(data) {
        // Actualizar estado de factura en la UI
        const element = document.querySelector(`[data-factura-id="${data.factura_id}"]`);
        if (element) {
            const statusBadge = element.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.className = `badge badge-status ${data.status}`;
                statusBadge.textContent = this.getStatusLabel(data.status);
            }
        }
    }

    getStatusLabel(status) {
        const labels = {
            'subida': 'Subida',
            'en-cola': 'En cola',
            'procesando-ocr': 'Leyendo PDF',
            'procesando-ia': 'Analizando con IA',
            'pendiente': 'Pendiente revisión',
            'aprobada': 'Aprobada',
            'rechazada': 'Rechazada',
            'error': 'Error',
            'archivada': 'Archivada'
        };
        return labels[status] || status;
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    isWebSocketSupported() {
        return 'WebSocket' in window || 'MozWebSocket' in window;
    }
}

// ============================================
// PWA
// ============================================

class PWAManager {
    constructor() {
        this.init();
    }

    init() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/js/service-worker.js')
                .then(registration => {
                    console.log('Service Worker registrado:', registration);
                })
                .catch(error => {
                    console.error('Error al registrar Service Worker:', error);
                });
        }

        // Detectar instalación
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.showInstallPrompt(e);
        });

        window.addEventListener('appinstalled', () => {
            console.log('PWA instalada');
        });
    }

    showInstallPrompt(deferredPrompt) {
        // Guardar evento para mostrar cuando sea conveniente
        window.deferredPrompt = deferredPrompt;
    }

    async install() {
        if (window.deferredPrompt) {
            window.deferredPrompt.prompt();
            const { outcome } = await window.deferredPrompt.userChoice;
            console.log(`Usuario respondió: ${outcome}`);
            window.deferredPrompt = null;
        }
    }
}

// ============================================
// UTILS
// ============================================

class Utils {
    static formatCurrency(value) {
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'EUR'
        }).format(value);
    }

    static formatDate(date) {
        return new Intl.DateTimeFormat('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(new Date(date));
    }

    static formatTime(date) {
        return new Intl.DateTimeFormat('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }

    static getConfidenceBadge(confidence) {
        let classe, label;
        if (confidence >= 85) {
            clase = 'alta';
            label = 'Alta';
        } else if (confidence >= 70) {
            clase = 'media';
            label = 'Media';
        } else {
            clase = 'baja';
            label = 'Baja';
        }
        return `<span class="badge badge-confianza ${clase}">${confidence}% ${label}</span>`;
    }

    static getStatusBadge(status) {
        return `<span class="badge badge-status ${status}">${this.getStatusLabel(status)}</span>`;
    }

    static getStatusLabel(status) {
        const labels = {
            'subida': 'Subida',
            'en-cola': 'En cola',
            'procesando-ocr': 'Leyendo PDF',
            'procesando-ia': 'Analizando con IA',
            'pendiente': 'Pendiente revisión',
            'aprobada': 'Aprobada',
            'rechazada': 'Rechazada',
            'error': 'Error',
            'archivada': 'Archivada'
        };
        return labels[status] || status;
    }

    static showSpinner(text = 'Cargando...') {
        const spinner = document.createElement('div');
        spinner.className = 'text-center mt-5';
        spinner.innerHTML = `
            <div class="spinner mx-auto mb-2"></div>
            <p class="text-muted">${text}</p>
        `;
        return spinner;
    }
}

// ============================================
// INICIALIZACIÓN
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Inicializar gestores
    const themeManager = new ThemeManager();
    const sidebarManager = new SidebarManager();
    const notificationManager = new NotificationManager();
    // const wsManager = new WebSocketManager(); // ⚠️ Endpoint /ws no existe - comentado
    const pwaManager = new PWAManager();

    // Exponer globalmente para uso en otras scripts
    window.themeManager = themeManager;
    window.sidebarManager = sidebarManager;
    window.notificationManager = notificationManager;
    window.wsManager = wsManager;
    window.pwaManager = pwaManager;
    window.Utils = Utils;
});
