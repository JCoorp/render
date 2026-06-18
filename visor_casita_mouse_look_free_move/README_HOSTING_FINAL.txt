VISOR CASITA - HOSTING FINAL
============================

Este proyecto carga automáticamente un solo modelo:

models/Casa_mejor.glb

Este GLB fue tomado del archivo subido:
Casa mejor(2).glb

IMPORTANTE:
El modelo conserva los nombres de materiales, pero no trae imágenes de textura incrustadas.
Por eso app.js reconstruye visualmente materiales tipo:
- pasto
- mármol
- madera
- concreto
- techo grafito
- vidrio
- agua
- neón azul/magenta

PARA PROBAR LOCALMENTE:
1. Abre PowerShell en esta carpeta.
2. Ejecuta:

   npx http-server . -p 5502 -a 0.0.0.0

3. En PC abre:

   http://localhost:5502

4. En Android u otro dispositivo abre:

   http://IP-DE-TU-PC:5502

Ejemplo:
   http://10.182.83.32:5502

PARA HOSTEAR:
Sube todo el contenido de esta carpeta:
- index.html
- styles.css
- app.js
- models/Casa_mejor.glb

No cambies el nombre del archivo ni la carpeta models.


CONTROLES NUEVOS DE MOVIMIENTO LIBRE
====================================

Con la página abierta puedes moverte como en un recorrido:

- Flecha arriba o W: avanzar
- Flecha abajo o S: retroceder
- Flecha izquierda o A: moverte a la izquierda
- Flecha derecha o D: moverte a la derecha
- Q o Page Up: subir
- E o Page Down: bajar
- Shift: moverte más rápido
- Mouse o dedo: rotar la vista
- Rueda/pellizco: zoom

También hay un botón:
Movimiento libre: On/Off

Si estás en Android, las flechas físicas solo funcionan con teclado conectado.
En pantalla touch puedes seguir rotando, haciendo zoom y moviendo con dedos.


MODO MIRADA CON MOUSE
=====================

Se agregó control tipo videojuego:

- Clic sobre el visor: activa mirada con mouse.
- Mover mouse: mirar libremente.
- ESC: salir de mirada con mouse.
- W / Flecha arriba: avanzar hacia donde miras.
- S / Flecha abajo: retroceder.
- A / Flecha izquierda: moverte a la izquierda.
- D / Flecha derecha: moverte a la derecha.
- Q / Page Up: subir.
- E / Page Down: bajar.
- Shift: rápido.

Importante:
El navegador exige hacer clic en el visor para bloquear el mouse.
Al presionar ESC recuperas el cursor normal.
