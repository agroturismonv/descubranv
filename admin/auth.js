// admin/auth.js
(function () {
    "use strict";

    const LOGIN_URL = '/admin';

    /**
     * ============================
     * API URL
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
     * CHECK AUTH
     * ============================
     */
   async function checkAuth() {
    const isLoginPage =
        window.location.pathname === '/admin' ||
        window.location.pathname.endsWith('/login.html');

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
     * LOGIN
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
    const data = await res.json();

    // ✅ SALVA NA SESSÃO DO FRONT
    sessionStorage.setItem('admin_user', data.user);
    sessionStorage.setItem('admin_level', data.level);

    window.location.href = '/admin/dashboard.html';
}
         else {
            alert('Login inválido');
        }
    };

    /**
     * ============================
     * LOGOUT
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
     * API REQUEST
     * ============================
     */
    
    async function apiRequest(path, options = {}) {
        const isFormData = options.body instanceof FormData;
        const mergedHeaders = {
            ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
            ...(options.headers || {})
        };

        const res = await fetch(apiUrl(path), {
            credentials: 'include',
            headers: mergedHeaders,
            ...options
        });

        if (res.status === 403) {
            window.location.href = LOGIN_URL;
            return;
        }

        if (!res.ok) {
            let msg = `Erro HTTP: ${res.status}`;
            try {
                const errJson = await res.json();
                msg = errJson.erro || errJson.message || msg;
            } catch (_) {
                // noop
            }
            throw new Error(msg);
        }

        return await res.json();
    }

    window.apiRequest = apiRequest;

    // Compat alias
    window.apiFetch = (path, options = {}) => fetch(apiUrl(path), {
        credentials: 'include',
        ...options
    });

    /**
     * ============================
     * API
     * ============================
     */
    window.API = {
        dashboard: () => apiRequest('/api/dashboard'),

        // GET /api/regioes — lista todas as regioes
        regioes: () => apiRequest('/api/regioes'),

        listar: () => apiRequest('/api/listar'),

        salvar: (body) => apiRequest('/api/cadastro', {
            method: 'POST',
            body: JSON.stringify(body)
        }),

        // CORRIGIDO: era /api/delete (POST), rota adicionada ao servidor
        delete: (body) => apiRequest('/api/delete', {
            method: 'POST',
            body: JSON.stringify(body)
        }),

        uploadZip: (formData) => fetch(apiUrl('/api/upload_zip'), {
            method: 'POST',
            body: formData,
            credentials: 'include'
        }),

        // CORRIGIDO: era /download_zip/${regiao}/${local}, rota correta é /download/${regiao}/${local}
        downloadZip: (regiao, local) => apiFetch(`/download/${regiao}/${local}`)
    };

})();
