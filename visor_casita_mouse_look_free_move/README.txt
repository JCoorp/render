VISOR CASITA - COLOR Y TEXTURAS FIX
===================================

Problema corregido:
El GLB tenía materiales con nombres de texturas, pero no traía imágenes incrustadas.
Por eso en la web se veía gris/blanco.

Esta versión:
- Carga automáticamente models/Casa_mejor.glb.
- No permite cargar otros archivos.
- Aplica colores y texturas web por nombre de material:
  pasto, mármol, madera, concreto, techo, vidrio, agua, neón.
- Centra y escala la casa.
- Mejora iluminación y sombras.

Para probar:

cd "C:\Users\video\OneDrive\Desktop\visor_casita_color_texturas_fix"
npx http-server . -p 5502 -a 0.0.0.0

PC:
http://localhost:5502

Android:
http://TU-IP:5502

Para hostear:
Sube todos estos archivos:
- index.html
- styles.css
- app.js
- models/Casa_mejor.glb
