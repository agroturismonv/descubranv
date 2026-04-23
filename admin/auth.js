// admin/auth.js
(function () {
    "use strict";

    // ✅ PADRONIZA LOGIN
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

        // ✅ CORREÇÃO AQUI
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
     * 🔐 CHECK LOGIN REAL
     * ============================
     */
    async function checkAuth() {
        try {
            const res = await fetch(apiUrl('/api/check'), {
                credentials: 'include'
            });

            const data = await res.json();

            const isLoginPage = window.location.pathname.includes('/admin/login.html');

            // ✅ CORREÇÃO AQUI
            if (!data.logado && !isLoginPage) {
                window.location.href = LOGIN_URL;
            }

        } catch {
            window.location.href = LOGIN_URL;
        }
    }

    checkAuth();

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

        // ✅ CORREÇÃO AQUI
        window.location.href = LOGIN_URL;
    };

    /**
     * ============================
     * 📦 API CENTRAL
     * ============================
     */
    const API = {
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

    window.API = API;

    /**
     * ============================
     * 📊 DASHBOARD
     * ============================
     */
    async function carregarDashboard() {
        try {
            const data = await API.listar();

            const el = document.getElementById('resultado');
            if (!el || !data.success) return;

            const totalRegioes = data.data.length;
            const totalLocais = data.data.reduce((acc, r) => acc + r.locais.length, 0);

            el.innerText =
                `📍 Locais: ${totalLocais} | 🌎 Regiões: ${totalRegioes} | ⚙️ Status: OK`;

        } catch (error) {
            console.error('Erro dashboard:', error);
        }
    }

    /**
     * ============================
     * 🧰 UTILS
     * ============================
     */
    window.TurismoUtils = {
        slug: (v) =>
            (v || '')
                .toLowerCase()
                .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
                .replace(/\s+/g, '_')
                .replace(/[^a-z0-9_]/g, ''),

        async traduzir(texto, lang) {
            if (!texto) return '';
            try {
                const res = await fetch(
                    `https://api.mymemory.translated.net/get?q=${encodeURIComponent(texto)}&langpair=pt|${lang}`
                );
                const d = await res.json();
                return d?.responseData?.translatedText || '';
            } catch {
                return '';
            }
        }
    };

    /**
     * ============================
     * 🔄 AUTO START
     * ============================
     */
    document.addEventListener('DOMContentLoaded', () => {
        carregarDashboard();
    });

})();
