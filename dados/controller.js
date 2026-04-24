(function () {
    const path = window.location.pathname;
    const isLayout = path.includes('/layout/');
    const isAdmin = path.includes('/admin/');
    
    // Define o prefixo relativo para subir pastas se necessário
    const prefixo = (isAdmin || isLayout) ? "../" : "";

    const ESTRUTURA = {
        "cachoeira_boavista": {
            "config": "dados/circuitos/cachoeira_boavista/config.js",
            "pontos": [
                {
                    "id": "boavista",
                    "src": "dados/circuitos/cachoeira_boavista/boavista/boavista.js",
                    "var": "LOCAL_BOAVISTA"
                }
            ]
        },
        "centro_nv": {
            "config": "dados/circuitos/centro_nv/config.js",
            "pontos": [
                {
                    "id": "casa_de_pedra_do_perletti",
                    "src": "dados/circuitos/centro_nv/casa_de_pedra_do_perletti/casa_de_pedra_do_perletti.js",
                    "var": "LOCAL_CASA_DE_PEDRA_DO_PERLETTI"
                },
                {
                    "id": "igreja_sao_marcos",
                    "src": "dados/circuitos/centro_nv/igreja_sao_marcos/igreja_sao_marcos.js",
                    "var": "LOCAL_IGREJA_SAO_MARCOS"
                }
            ]
        },
        "pedra_elefante": {
            "config": "dados/circuitos/pedra_elefante/config.js",
            "pontos": [
                {
                    "id": "gameleira",
                    "src": "dados/circuitos/pedra_elefante/gameleira/gameleira.js",
                    "var": "LOCAL_GAMELEIRA"
                },
                {
                    "id": "elefante",
                    "src": "dados/circuitos/pedra_elefante/pedra_elefante/elefante.js",
                    "var": "LOCAL_ELEFANTE"
                }
            ]
        },
        "pedra_fortaleza": {
            "config": "dados/circuitos/pedra_fortaleza/config.js",
            "pontos": [
                {
                    "id": "fortaleza",
                    "src": "dados/circuitos/pedra_fortaleza/pedra_fortaleza/fortaleza.js",
                    "var": "LOCAL_FORTALEZA"
                }
            ]
        }
    };

    let carregados = 0;
    let total = 0;

    // Conta total de arquivos (configs + pontos)
    Object.values(ESTRUTURA).forEach(c => {
        total += 1;
        total += c.pontos.length;
    });

    function checkFinalizacao() {
        if (carregados === total) {
            montarSistema();
        }
    }

    function carregouScript(src) {
        carregados++;
        console.log("✔️ Carregado:", src);
        checkFinalizacao();
    }

    function erroScript(src) {
        carregados++;
        console.error("❌ Erro ao carregar:", src);
        checkFinalizacao();
    }

    function montarSistema() {
        window.LOCAIS = {};
        window.LISTA_CIRCUITOS = [];

        Object.entries(ESTRUTURA).forEach(([key, circuito]) => {
            const varConfig = "CONFIG_" + key.toUpperCase();

            // CONFIG DO CIRCUITO
            if (window[varConfig]) {
                let cfg = JSON.parse(JSON.stringify(window[varConfig]));
                if (cfg.cover) cfg.cover = prefixo + cfg.cover;
                window.LISTA_CIRCUITOS.push(cfg);
            } else {
                console.warn("⚠️ Config não encontrado:", varConfig);
            }

            // LOCAIS
            circuito.pontos.forEach(ponto => {
                if (window[ponto.var]) {
                    let d = JSON.parse(JSON.stringify(window[ponto.var]));

                    if (d.hero) d.hero = prefixo + d.hero;
                    if (d.cover) d.cover = prefixo + d.cover;
                    if (d.gallery) d.gallery = d.gallery.map(img => prefixo + img);

                    window.LOCAIS[ponto.id] = d;
                } else {
                    console.warn("⚠️ Local não encontrado:", ponto.var);
                }
            });
        });

        console.log("🚀 Sistema Pronto | Prefixo:", prefixo || "raiz");
        console.log("📍 LOCAIS:", Object.keys(window.LOCAIS));
        console.log("🧭 CIRCUITOS:", window.LISTA_CIRCUITOS.length);

        window.dispatchEvent(new Event('locais-ready'));
    }

    // Carrega todos os scripts
    Object.values(ESTRUTURA).forEach(circuito => {

        // CONFIG
        const sConf = document.createElement('script');
        sConf.src = prefixo + circuito.config;
        sConf.onload = () => carregouScript(sConf.src);
        sConf.onerror = () => erroScript(sConf.src);
        document.head.appendChild(sConf);

        // PONTOS
        circuito.pontos.forEach(ponto => {
            const sLoc = document.createElement('script');
            sLoc.src = prefixo + ponto.src;
            sLoc.onload = () => carregouScript(sLoc.src);
            sLoc.onerror = () => erroScript(sLoc.src);
            document.head.appendChild(sLoc);
        });
    });

})();
