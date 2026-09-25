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

La app tiene **tres pestañas**:
- **Mi plan**: tu rutina y los 7 días de la semana (hecho, hoy, descanso). Toca un día para **moverlo solo esta semana** (se intercambia con otro día o se salta) y vuelve al plan original cuando quieras. Incluye el **volumen semanal** por músculo (series hechas frente a las del plan, con la zona de 10–20 series recomendada para hipertrofia; los secundarios cuentan como media serie) y los botones **Editar** y **Cambiar de rutina**.
- **Entrenar**: la vista de tu plan con una pestaña por día (✓ en los hechos esta semana), cada ejercicio con su miniatura de músculos, series, reps y tu último peso, y el botón **Empezar**.
  - Por cada serie anotas kg y reps (y RIR/RPE fuera del modo simple).
  - Sugerencias de progresión, notas por ejercicio y aviso 🏆 de récord personal.
  - **Modo enfoque**: un ejercicio por pantalla, cronómetro arriba y un carrusel horizontal con la miniatura de músculos de cada ejercicio (✓ en los terminados). Se cambia de ejercicio tocando el carrusel o deslizando a los lados.
  - Opción **Por lado (unilateral)** en ejercicios como step-up, búlgaras, zancadas, jalones, remo con mancuerna o curls: cada serie se registra para la izquierda (I) y la derecha (D). Step-up, búlgaras, remo con mancuerna y curl concentrado vienen activados; la elección se recuerda por ejercicio.
  - En modo avanzado, al tocar el número de una serie se puede convertir en aproximación (o volver a efectiva) o eliminar.
  - Series de aproximación opcionales (interruptor por ejercicio, filas «A»): no cuentan en volumen, récords ni progresión, y se recuerdan para la próxima vez.
  - Series en filas redondeadas (serie, reps, peso, ✓) y un botón inferior que guía: *Marcar todas las series* → *Siguiente ejercicio* → *Terminar entrenamiento*. Descartar queda en el menú ⋯.
  - **Temporizador de descanso**: arranca solo al marcar una serie (en ejercicios por lado, tras el lado derecho). Duración según las reps objetivo (≤6: 2:30, ≤10: 2:00, resto: 1:30); con −15 / +15 la app recuerda tu descanso para ese ejercicio. Suena y vibra al terminar (si el teléfono lo permite). Se puede desactivar en Ajustes.
  - La pantalla se mantiene encendida mientras entrenas.
  - Cuando toca subir de peso, aparece **↑ +2,5 kg** con el motivo.
  - Resumen limpio al terminar: check verde, tiempo, series y volumen en tarjetas, la lista de ejercicios hechos (series, reps, peso y 🏆 si hubo récord), el progreso de la semana y una frase motivadora.
  - Los entrenamientos terminados se pueden editar.
- **Progreso**: analíticas por periodo (1M · 3M · 1A · Todo): 6 fichas (entrenos, duración, ejercicios, series, reps, volumen), barras de **músculos** (sólido = series directas, rayado = secundarias), mini‑gráficos de **evolución de cada ejercicio** (Máx = peso máximo, Vol = volumen por sesión), constancia con racha, peso corporal y medidas, e historial.

Al tocar un ejercicio se abre su ficha: Acerca de (con la **guía muscular**: cuerpo realista de frente y de espalda con los músculos principales en rojo intenso y los secundarios en rojo suave), Historial, Gráficos y Récords. El cuerpo es de hombre o de mujer según el perfil (se cambia en tu perfil → Ajustes). El catálogo tiene más de 110 ejercicios con buscador (se abre arriba para que el teclado no tape los resultados), y puedes crear los tuyos. Los ejercicios con variantes (prensa, sentadilla búlgara, sentadilla en Smith) aparecen una sola vez y al elegirlos se escoge el enfoque: cuádriceps o glúteos.

**Kilos o libras**: en tu perfil → Ajustes eliges la unidad por defecto, y cada ejercicio puede tener la suya (por ejemplo, máquinas en libras) con el selector kg/lb de su tarjeta o de su ficha. Los pesos se guardan siempre en kg, así que récords y gráficos no se mezclan.

**Modo simple** (activado por defecto para principiantes, se cambia en tu perfil → Ajustes): oculta RIR/RPE y el 1RM, usa frases sencillas y deja el volumen en "Más estadísticas".

**Cambiar de rutina o de días**: tu perfil (arriba a la derecha) → *Mi rutina* → *Cambiar de rutina*.

## Datos y cuenta en la nube

Los datos se guardan siempre en el navegador (`localStorage`), así que la app funciona sin conexión. La app abre al instante desde la copia guardada, aunque en el gym no haya señal; las versiones nuevas se descargan solas en segundo plano.
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
