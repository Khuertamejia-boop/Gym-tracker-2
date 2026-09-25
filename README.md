# Mi Gym Tracker

App web para armar tu rutina semanal, registrar tus entrenamientos y ver tu progreso.
Está pensada para usarse desde el celular en el gym.

## Funciones

**Configuración inicial.** Un usuario nuevo indica si es hombre o mujer (para la guía muscular), cuánto tiempo lleva entrenando y qué días puede ir:
- Principiante: recibe una rutina recomendada (Full Body con 2-3 días, Torso/Pierna con 4 o más).
- Intermedio o avanzado: elige entre Push/Pull/Legs, Arnold Split, Torso/Pierna, Full Body, Torso/Pierna · glúteo, o crea la suya desde cero.
- Después revisa y personaliza ejercicios, series y días, y puede crear una cuenta para guardar su progreso.
- Quien ya tiene cuenta toca **Ya tengo cuenta** y recupera todo.

Arriba a la derecha está tu **perfil**: iniciar sesión o ver tu cuenta, *Mi rutina*, *Ajustes* (cuerpo de la guía, unidad de peso, modo simple, esfuerzo y tema) y *Respaldo de datos*.

La app tiene solo **dos pestañas**:
- **Entrenar**: la vista de tu plan con una pestaña por día (✓ en los hechos esta semana), cada ejercicio con su miniatura de músculos, series, reps y tu último peso, y el botón **Empezar**. Debajo, tu rutina con **Editar**.
  - Por cada serie anotas kg y reps (y RIR/RPE fuera del modo simple).
  - Sugerencias de progresión, notas por ejercicio y aviso 🏆 de récord personal.
  - **Modo enfoque**: un ejercicio por pantalla, cronómetro arriba y un carrusel horizontal con la miniatura de músculos de cada ejercicio (✓ en los terminados). Se cambia de ejercicio tocando el carrusel o deslizando a los lados.
  - Series en filas redondeadas (serie, reps, peso, ✓) y un botón inferior que guía: *Marcar todas las series* → *Siguiente ejercicio* → *Terminar entrenamiento*. Descartar queda en el menú ⋯.
  - Resumen a pantalla completa al terminar: tiempo, series, volumen, el cuerpo con los músculos trabajados, récords, progreso de la semana y una frase motivadora.
  - Los entrenamientos terminados se pueden editar.
- **Progreso**: entrenamientos, racha, constancia, tus ejercicios (peso y mejora), peso corporal y medidas, historial y estadísticas de volumen.

Al tocar un ejercicio se abre su ficha: Acerca de (con la **guía muscular**: cuerpo realista de frente y de espalda con los músculos principales en rojo intenso y los secundarios en rojo suave), Historial, Gráficos y Récords. El cuerpo es de hombre o de mujer según el perfil (se cambia en tu perfil → Ajustes). El catálogo tiene más de 110 ejercicios con buscador, y puedes crear los tuyos.

**Kilos o libras**: en tu perfil → Ajustes eliges la unidad por defecto, y cada ejercicio puede tener la suya (por ejemplo, máquinas en libras) con el selector kg/lb de su tarjeta o de su ficha. Los pesos se guardan siempre en kg, así que récords y gráficos no se mezclan.

**Modo simple** (activado por defecto para principiantes, se cambia en tu perfil → Ajustes): oculta RIR/RPE y el 1RM, usa frases sencillas y deja el volumen en "Más estadísticas".

**Cambiar de rutina o de días**: tu perfil (arriba a la derecha) → *Mi rutina* → *Cambiar de rutina*.

## Datos y cuenta en la nube

Los datos se guardan siempre en el navegador (`localStorage`), así que la app funciona sin conexión.
Si inicias sesión (botón de perfil, arriba a la derecha), además se sincronizan con Supabase y puedes usarlos en cualquier dispositivo.
Al sincronizar se fusionan las copias: no se pierde ningún entrenamiento de ningún dispositivo, y lo que borras se borra en todos.

### Configurar Supabase (una sola vez)

1. Crea una cuenta gratis en [supabase.com](https://supabase.com) y un proyecto nuevo.
2. Ve a **SQL Editor → New query**, pega el contenido de [`supabase/setup.sql`](supabase/setup.sql) y pulsa **Run**.
3. Ve a **Authentication → URL Configuration** y pon en **Site URL** la dirección de tu app (por ejemplo `https://<tu-usuario>.github.io/<repo>/`).
4. Ve a **Project Settings → API** y copia la **Project URL** y la clave **anon / publishable** en [`js/config.js`](js/config.js).

La clave *anon* es pública por diseño. La seguridad la dan las políticas de `setup.sql`, que solo permiten a cada usuario leer y escribir su propia fila.
Los proyectos gratuitos de Supabase se pausan tras 7 días sin uso; se reactivan desde el panel de Supabase.

### Importar la rutina del Excel

Abrir la app con `?importar=excel` al final de la dirección añade la rutina *Torso / Pierna · glúteo* con los últimos pesos del Excel original al historial (solo una vez por cuenta).

También puedes descargar una copia `.json` desde tu perfil → **Respaldo de datos**.

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
js/data/muscles.js    músculos principales y secundarios de cada ejercicio
js/body.js            guía muscular (usa js/vendor/muscle-map)
js/vendor/muscle-map  js-rich-body-highlighter 0.1.1 (MIT): ilustraciones del cuerpo
sw.js                 caché sin conexión
```
