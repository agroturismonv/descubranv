// admin/auth.js
(function () {
    "use strict";

    // 🔥 PADRÃO ÚNICO DE LOGIN
    const LOGIN_URL = '/admin/login.html';

    /**
     * ============================
     * 🔐 CONTROLE DE AUTENTICAÇÃO
     * ============================
     */
    const isLogged = sessionStorage.getItem('admin_logged');

    const isLoginPage = window.location.pathname.includes('/admin/login.html');

    if (!isLogged && !isLoginPage) {
        window.location.href = LOGIN_URL;
        return;
    }

    /**
     * ============================
     * 🌐 RESOLUÇÃO DE URL DA API
     * ============================
     */
    function apiUrl(path) {
        const normalized = path.startsWith('/') ? path : `/${path}`;
        const savedBase = sessionStorage.getItem('admin_api_base');

        if (savedBase) return `${savedBase}${normalized}`;

        if (window.location.protocol === 'file:') {
            return `http://127.0.0.1:5000${normalized}`;
        }

        if (
            (window.location.hostname === 'localhost' ||
                window.location.hostname === '127.0.0.1') &&
            window.location.port &&
            window.location.port !== '5000'
        ) {
            return `http://127.0.0.1:5000${normalized}`;
        }

        return `${window.location.origin}${normalized}`;
    }

    window.apiUrl = apiUrl;

    /**
     * ============================
     * 🚪 LOGOUT (FIXO)
     * ============================
     */
    window.logout = function () {
        sessionStorage.removeItem('admin_logged');
        sessionStorage.removeItem('admin_api_base');

        window.location.href = LOGIN_URL;
    };

    /**
     * ============================
     * 📡 CLIENTE DE API
     * ============================
     */
    async function apiRequest(path, options = {}) {
        try {
            const response = await fetch(apiUrl(path), {
                headers: {
                    'Content-Type': 'application/json',
                    ...(options.headers || {})
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Erro na API:', error);
            throw error;
        }
    }

    /**
     * ============================
     * 📦 ENDPOINTS
     * ============================
     */
    const API = {
        dashboard: () => apiRequest('/api/dashboard'),
        locais: () => apiRequest('/api/locais'),
        regioes: () => apiRequest('/api/regioes'),
        status: () => apiRequest('/status'),
        rebuild: () => apiRequest('/rebuild', { method: 'POST' }),
        limpar: () => apiRequest('/limpar', { method: 'POST' }),

        delete: (body) => apiRequest('/delete', {
            method: 'POST',
            body: JSON.stringify(body)
        })
    };

    window.API = API;

    /**
     * ============================
     * 📊 DASHBOARD
     * ============================
     */
    async function carregarDashboard() {
        try {
            const data = await API.dashboard();

            console.log('Dashboard:', data);

            const el = document.getElementById('resultado');
            if (!el) return;

            el.innerText =
                `📍 Locais: ${data.total_locais} | 🌎 Regiões: ${data.total_regioes} | ⚙️ Status: ${data.status}`;

        } catch (error) {
            console.error('Erro ao carregar dashboard:', error);
        }
    }

    /**
     * ============================
     * 🔄 AUTO START
     * ============================
     */
    document.addEventListener('DOMContentLoaded', () => {
        if (isLogged) {
            carregarDashboard();
        }
    });

})();
