// admin/auth.js
(function () {
    "use strict";

    const LOGIN_URL = '/admin/login.html';

    /**
     * ============================
     * 🌐 API URL
     * ============================
     */
    function apiUrl(path) {
        const normalized = path.startsWith('/') ? path : `/${path}`;

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
     * 🔐 CHECK AUTH
     * ============================
     */
    async function checkAuth() {
        const isLoginPage = window.location.pathname.includes('/admin/login.html');

        try {
            const res = await fetch(apiUrl('/api/check'), {
                credentials: 'include'
            });

            if (!res.ok) return;

            const data = await res.json();

            if (!data.logado && !isLoginPage) {
                window.location.href = LOGIN_URL;
            }

        } catch (e) {
            console.error("Erro auth:", e);
        }
    }

    checkAuth();

    /**
     * ============================
     * 🔑 LOGIN
     * ============================
     */
    window.login = async function (user, password) {
        const res = await fetch(apiUrl('/api/login'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ user, password })
        });

        if (res.ok) {
            window.location.href = '/admin/dashboard.html';
        } else {
            alert('Login inválido');
        }
    };

    /**
     * ============================
     * 🚪 LOGOUT
     * ============================
     */
    window.logout = async function () {
        await fetch(apiUrl('/api/logout'), {
            method: 'POST',
            credentials: 'include'
        });

        window.location.href = LOGIN_URL;
    };

    /**
     * ============================
     * 📡 API REQUEST
     * ============================
     */
    async function apiRequest(path, options = {}) {
        const res = await fetch(apiUrl(path), {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            },
            ...options
        });

        if (res.status === 403) {
            window.location.href = LOGIN_URL;
            return;
        }

        if (!res.ok) {
            throw new Error(`Erro HTTP: ${res.status}`);
        }

        return await res.json();
    }

    window.apiRequest = apiRequest;

    /**
     * ============================
     * 📦 API
     * ============================
     */
    window.API = {
        dashboard: () => apiRequest('/api/dashboard'),
        locais: () => apiRequest('/api/locais'),
        regioes: () => apiRequest('/api/regioes'),
        listar: () => apiRequest('/api/listar'),

        salvar: (body) => apiRequest('/api/cadastro', {
            method: 'POST',
            body: JSON.stringify(body)
        }),

        delete: (body) => apiRequest('/api/delete', {
            method: 'POST',
            body: JSON.stringify(body)
        }),

        uploadZip: (formData) => fetch(apiUrl('/api/upload_zip'), {
            method: 'POST',
            body: formData,
            credentials: 'include'
        })
    };

})();
