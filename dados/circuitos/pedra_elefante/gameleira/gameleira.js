/**
 * LOCAL: Santuário da Mãe Peregrina (Gameleira)
 * Gerado/Refatorado para suporte à estrutura /layout/
 */
window.LOCAL_GAMELEIRA = Object.freeze({
  id: 'gameleira',

  // Link externo mantido
  cover: 'https://terracapixaba.com/wp-content/uploads/2024/02/gameleira-de-nova-venecia-2.webp',

  // Ajuste de caminho: saindo de /layout/ para a raiz /imagens/
  hero: 'dados/circuitos/pedra_elefante/gameleira/images/santuario-1.jpg',

  gallery: [
    'dados/circuitos/pedra_elefante/gameleira/images/santuario.webp',
    'dados/circuitos/pedra_elefante/gameleira/images/santuario-1.jpg',
    'dados/circuitos/pedra_elefante/gameleira/images/santuario-2.jpg'
  ],

  location: {
    maps: 'https://www.google.com/maps/search/Santuário+Mãe+Peregrina+Gameleira+Nova+Venécia',
    embed: 'https://www.google.com/maps?q=Santuário+Mãe+Peregrina+Gameleira+Nova+Venécia&output=embed', // Ajustado para 'embed'
   qr: 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://www.google.com/maps/search/Santuário+Mãe+Peregrina+Gameleira+Nova+Venécia',
  },

  texts: {
    pt: {
      title: 'Santuário da Mãe Peregrina',
      subtitle: 'Fé, espiritualidade e paz',
      about: 'Sobre o local',
      description: 'Localizado na comunidade da Gameleira, o Santuário da Mãe Peregrina é um importante ponto de devoção religiosa em Nova Venécia. O espaço oferece um ambiente de paz, reflexão e espiritualidade, recebendo visitantes e fiéis durante todo o ano.',
      gallery: 'Galeria de Fotos',
      location: 'Como chegar',
      RAvisionButton: 'Veja em 360°', // Movi para dentro do idioma
      qr: 'Escaneie o QR Code para abrir no Google Maps'
    },
    en: {
      title: 'Mother Pilgrim Shrine',
      subtitle: 'Faith and spirituality',
      about: 'About',
      description: 'Located in the Gameleira community, the Mother Pilgrim Shrine is an important religious site in Nova Venécia. It offers a peaceful environment for prayer, reflection, and spiritual connection.',
      gallery: 'Photo Gallery',
      location: 'How to get there',
      RAvisionButton: 'View 360°',
      qr: 'Scan the QR Code to open Google Maps'
    },
    es: {
      title: 'Santuario de la Madre Peregrina',
      subtitle: 'Fe y espiritualidad',
      about: 'Sobre el lugar',
      description: 'Ubicado en la comunidad de Gameleira, el Santuario de la Madre Peregrina es un importante punto religioso de Nova Venécia. Ofrece un ambiente de paz, oración y reflexión espiritual.',
      gallery: 'Galería de Fotos',
      location: 'Cómo llegar',
      RAvisionButton: 'Ver en 360°',
      qr: 'Escanee el código QR para abrir Google Maps'
    }
  },

  RAvisionScreen: true,
  RAvisionlink: 'https://novavenecia360.com.br', // Link sugerido
})