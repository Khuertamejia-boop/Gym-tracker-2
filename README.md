# Mi Gym Tracker

App web para armar tu rutina semanal, registrar tus entrenamientos y ver tu progreso.
Está pensada para usarse desde el celular en el gym.

## Funciones

- **Entrenar**: muestra lo que toca hoy según tu rutina. Por cada serie anotas kg, reps y RIR/RPE, y ves lo que hiciste la vez anterior.
  - Sugerencias de progresión: sube el peso cuando llegas al tope del rango de reps.
  - Notas por ejercicio y aviso 🏆 al batir un récord personal.
  - Resumen al terminar: duración, volumen, comparación con la sesión anterior y récords.
  - Los entrenamientos terminados se pueden editar (series, reps, fecha y notas).
- **Rutinas**: incluye plantillas clásicas (Push/Pull/Legs, Arnold Split, Torso/Pierna y Full Body) y un editor para crear o personalizar las tuyas. Puedes asignar un día de entrenamiento a cada día de la semana.
- **Ejercicios**: catálogo de más de 110 ejercicios con buscador (no distingue acentos) y filtro por grupo muscular. También puedes crear ejercicios propios.
  Cada ejercicio tiene una ficha con pestañas: Acerca de, Historial, Gráficos (1RM estimado, peso máximo, volumen) y Récords.
- **Progreso**: vista semanal o mensual con:
  - volumen total
  - series o volumen por grupo muscular
  - calendario de constancia y racha de semanas
  - peso corporal y medidas

## Datos y cuenta en la nube

Los datos se guardan siempre en el navegador (`localStorage`), así que la app funciona sin conexión.
Si inicias sesión (**Ajustes ⚙ → Cuenta**), además se sincronizan con Supabase y puedes usarlos en cualquier dispositivo.
Al sincronizar se fusionan las copias: no se pierde ningún entrenamiento de ningún dispositivo, y lo que borras se borra en todos.

### Configurar Supabase (una sola vez)

1. Crea una cuenta gratis en [supabase.com](https://supabase.com) y un proyecto nuevo.
2. Ve a **SQL Editor → New query**, pega el contenido de [`supabase/setup.sql`](supabase/setup.sql) y pulsa **Run**.
3. Ve a **Authentication → URL Configuration** y pon en **Site URL** la dirección de tu app (por ejemplo `https://<tu-usuario>.github.io/<repo>/`).
4. Ve a **Project Settings → API** y copia la **Project URL** y la clave **anon / publishable** en [`js/config.js`](js/config.js).

La clave *anon* es pública por diseño. La seguridad la dan las políticas de `setup.sql`, que solo permiten a cada usuario leer y escribir su propia fila.
Los proyectos gratuitos de Supabase se pausan tras 7 días sin uso; se reactivan desde el panel de Supabase.

También puedes descargar un respaldo `.json` desde **Ajustes**.

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
js/cloud.js           inicio de sesión y sincronización (Supabase)
js/config.js          datos de conexión de Supabase
supabase/setup.sql    tabla y permisos en Supabase
js/data/exercises.js  catálogo de ejercicios
js/data/templates.js  rutinas predefinidas
sw.js                 caché sin conexión
```
