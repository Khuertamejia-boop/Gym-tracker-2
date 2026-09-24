# Mi Gym Tracker

App web para armar tu rutina semanal, registrar tus entrenamientos y ver tu progreso.
Está pensada para usarse desde el celular en el gym.

## Funciones

- **Entrenar**: muestra lo que toca hoy según tu rutina. Por cada serie anotas kg, reps y RIR/RPE, y ves lo que hiciste la vez anterior.
- **Rutinas**: incluye plantillas clásicas (Push/Pull/Legs, Arnold Split, Torso/Pierna y Full Body) y un editor para crear o personalizar las tuyas. Puedes asignar un día de entrenamiento a cada día de la semana.
- **Ejercicios**: catálogo de más de 110 ejercicios con buscador (no distingue acentos) y filtro por grupo muscular. También puedes crear ejercicios propios.
- **Progreso**: vista semanal o mensual con:
  - volumen total
  - series o volumen por grupo muscular
  - calendario de constancia y racha de semanas
  - peso corporal y medidas

## Datos

Todo se guarda en el navegador (`localStorage`), sin servidor ni cuentas.
En **Ajustes (⚙) → Descargar respaldo** puedes exportar tus datos a un archivo `.json` y restaurarlos en otro dispositivo.

## Publicar con GitHub Pages

1. Sube este repositorio a GitHub.
2. Ve a **Settings → Pages**, elige la rama `main` y la carpeta `/ (root)`, y guarda.
3. En un par de minutos estará en `https://<tu-usuario>.github.io/<repo>/`.
4. En el celular, ábrela y elige **Añadir a pantalla de inicio**. Funciona sin conexión.

## Desarrollo local

No necesita compilación. Basta con servir la carpeta:

```bash
python3 -m http.server 8000
# abre http://localhost:8000
```

Estructura:

```
index.html            página principal
css/styles.css        estilos (modo claro y oscuro)
js/app.js             vistas e interacción
js/store.js           datos y persistencia
js/charts.js          gráficos (Chart.js)
js/data/exercises.js  catálogo de ejercicios
js/data/templates.js  rutinas predefinidas
sw.js                 caché sin conexión
```
