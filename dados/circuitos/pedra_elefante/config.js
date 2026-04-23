window.CONFIG_PEDRA_ELEFANTE = Object.freeze({
  id: 'pedra_elefante',
  
  // Caminho para o index.html (Raiz)
  cover: 'dados/circuitos/pedra_elefante/pedra_elefante/images/pedra-elefante.jpg', 
  
  // Caminho para o circuitos.html (layout/)
  banner: 'dados/circuitos/pedra_elefante/pedra_elefante/images/pedra-elefante.jpg', 

  texts: {
    pt: { title: 'Pedra do Elefante', subtitle: 'O símbolo máximo de Nova Venécia' },
    en: { title: 'Elephant Rock', subtitle: 'The ultimate symbol of Nova Venécia' },
    es: { title: 'Piedra del Elefante', subtitle: 'El símbolo máximo' }
  },

  // ESTES NOMES DEVEM SER IGUAIS AOS ARQUIVOS .JS
  // Se os arquivos são elefante.js e gameleira.js, aqui fica assim:
  locais: ['elefante', 'gameleira'] 
});