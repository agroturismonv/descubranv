/**
 * LOCAL: Pedra do Elefante
 * Refatorado para suporte à estrutura /layout/ e automação Python.
 */
window.LOCAL_ELEFANTE = Object.freeze({
  id: 'elefante',

  // Capa para listagens (URL externa ou local)
  cover: 'https://cdn.esbrasil.com.br/wp-content/uploads/2025/01/Nova-Venecia_nx081212001-1-1536x1024.jpg',

  // Imagem principal do Hero (Caminho relativo saindo de /layout/)
  hero: 'dados/circuitos/pedra_elefante/pedra_elefante/images/pedra-elefante.jpg',

  // Galeria de fotos
  gallery: [
    'dados/circuitos/pedra_elefante/pedra_elefante/images/pedra-elefante.jpg',
    'dados/circuitos/pedra_elefante/pedra_elefante/images/pedra-elefante-2.jpg',
    'dados/circuitos/pedra_elefante/pedra_elefante/images/pedra-elefante-3.jpg'
  ],

  // Dados de geolocalização e mapas
  location: {
    maps: 'https://www.google.com/maps/search/Pedra+do+Elefante+Nova+Venécia',
    embed: 'https://www.google.com/maps?q=Pedra+do+Elefante+Nova+Venécia&output=embed',
    qr: 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://www.google.com/maps/search/Pedra+do+Elefante+Nova+Venécia'
  },

  // Textos multi-idioma
  texts: {
    pt: {
      title: 'Pedra do Elefante',
      subtitle: 'Um dos símbolos naturais de Nova Venécia',
      about: 'Sobre o local',
      description: 'A Pedra do Elefante é uma formação rochosa de grande porte que se destaca na paisagem de Nova Venécia. Seu nome se deve ao formato peculiar que lembra um elefante.',
      gallery: 'Galeria de Fotos',
      location: 'Como chegar',
      qr: 'Escaneie o QR Code para abrir no Google Maps',
      RAvisionButton: 'Veja em 360°'
    },
    en: {
      title: 'Elephant Rock',
      subtitle: 'One of Nova Venécia’s natural symbols',
      about: 'About',
      description: 'Elephant Rock is a large rock formation that stands out in the landscape of Nova Venécia. Its name comes from its unique shape, which resembles an elephant.',
      gallery: 'Photo Gallery',
      location: 'How to get there',
      qr: 'Scan the QR Code to open Google Maps',
      RAvisionButton: 'View in 360°'
    },
    es: {
      title: 'Piedra del Elefante',
      subtitle: 'Uno de los símbolos naturales de Nova Venécia',
      about: 'Sobre el lugar',
      description: 'La Piedra del Elefante es una gran formación rocosa que se destaca en el paisaje de Nova Venécia. Su nombre proviene de su forma peculiar, que recuerda a un elefante.',
      gallery: 'Galería de Fotos',
      location: 'Cómo llegar',
      qr: 'Escanee el código QR para abrir Google Maps',
      RAvisionButton: 'Ver en 360°'
    }
  },

  // Configurações de Realidade Aumentada / Tour 360
  RAvisionScreen: true,
  RAvisionlink: 'https://novavenecia360.com.br'
});