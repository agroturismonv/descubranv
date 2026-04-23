/* =========================================================
   Tailwind CDN Loader + Config
   Projeto: Turismo Nova Venécia
   ========================================================= */

(function () {
  if (window.tailwind) return;

  // Cria o script CDN
  const script = document.createElement('script');
  script.src = 'https://cdn.tailwindcss.com';
  script.defer = true;

  script.onload = () => {
    window.tailwind.config = {
      theme: {
        extend: {
          colors: {
            primary: '#0f5132',
            secondary: '#343a40'
          },
          fontFamily: {
            title: ['Inter', 'sans-serif'],
            body: ['Inter', 'sans-serif']
          },
          boxShadow: {
            soft: '0 10px 25px rgba(0,0,0,.15)'
          }
        }
      }
    }
  };

  document.head.appendChild(script);
})();
