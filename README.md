# DISCO DOWNLOAD
### *La Máquina Extractora de Música de Studio 54*

¡Bienvenido/a a la pista, crack! Esta herramienta descarga música de YouTube y la guarda en tu ordenador como **MP3** o **WAV**. Sin anuncios, sin suscripciones, sin cuentas. Solo tú, los enlaces y el boogie.

Además, **detecta automáticamente el BPM** de cada canción y lo guarda dentro del propio archivo MP3 para que tu software de DJing o tu reproductor lo lean directamente.

> **Nota legal:** Descarga únicamente música de la que tengas derecho. Respeta a los artistas, que ellos también tienen que pagar el alquiler.

---

## ¿Qué necesitas instalar? (solo la primera vez)

| Programa | Para qué sirve |
|----------|----------------|
| **uv** | Gestiona Python y todas las dependencias automáticamente |
| **ffmpeg** | Convierte el audio a MP3 o WAV |
| **yt-dlp** | Descarga el audio de YouTube |

Flask, librosa (detección de BPM) y mutagen (escritura de etiquetas) **los instala el propio `.bat` al arrancar**, no tienes que hacer nada.

---

## Paso 1 — Abre PowerShell como administrador

1. Pulsa la tecla **Windows** y escribe `PowerShell`
2. Haz **clic derecho** sobre "Windows PowerShell" y selecciona **Ejecutar como administrador**
3. Si aparece una ventana preguntando "¿Deseas permitir...?", pulsa **Sí**

Deja esa ventana abierta. Vamos a usarla mucho.

---

## Paso 2 — Instala uv

Copia este comando, pégalo en PowerShell y pulsa **Enter**:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verás texto moviéndose. Cuando pare y vuelva a aparecer el cursor, **cierra PowerShell y ábrelo de nuevo** (importante para que se actualice).

---

## Paso 3 — Instala ffmpeg

**ffmpeg** es el que convierte el audio. Sin él, los archivos salen en formato raro en vez de MP3 o WAV.

En PowerShell (el que acabas de abrir de nuevo):

```
winget install ffmpeg
```

Si te pide confirmación, escribe `Y` y pulsa Enter. Espera a que termine.

**¿Ves un error con winget?** Es posible que necesites actualizar el App Installer de Windows desde la Microsoft Store. Búscalo, actualízalo y vuelve a intentarlo.

---

## Paso 4 — Instala yt-dlp

```
uv tool install yt-dlp
```

---

## Paso 5 — Arranca la discoteca

### Haz doble clic en `iniciar.bat`

Eso es todo. Se abrirá una ventana negra: **déjala abierta** mientras usas la app.

La primera vez tardará un poco más porque descarga las dependencias automáticamente (Flask, librosa, mutagen). Las siguientes veces arranca en segundos.

Cuando veas algo como `* Running on http://127.0.0.1:5555`, la discoteca está abierta.

---

## Cómo usar Disco Download

1. Abre tu navegador (Chrome, Firefox, Edge... el que uses)
2. Ve a: **http://localhost:5555**
3. Pega los enlaces de YouTube que quieras descargar, **uno por línea**
4. Si quieres descargar una lista de reproducción completa, marca la casilla **Playlist completa** antes de pulsar el botón. Sin marcarla, solo se descarga el vídeo concreto que apunta el enlace
5. Elige el formato:
   - **MP3** — para escuchar en el móvil, en el coche, en cualquier sitio. El más compatible. El BPM se guarda como etiqueta ID3 dentro del archivo.
   - **WAV** — calidad máxima, sin compresión. Ocupa más espacio. Para los puristas del sonido. El BPM se muestra en pantalla pero no se puede guardar en el archivo (el formato no lo soporta).
6. Pulsa el botón dorado **A BAILAR**
7. La página muestra el estado de cada descarga en tiempo real y se actualiza sola cada dos segundos:

   | Estado | Qué significa |
   |--------|---------------|
   | **en cola** | Esperando su turno |
   | **descargando...** | Bajando el audio de YouTube |
   | **analizando BPM...** | Calculando los pulsos por minuto |
   | **listo** `128 BPM` | Descargado y etiquetado |
   | **error** | Algo fue mal (se muestra el motivo) |

   En playlists el resultado final muestra cuántas canciones se descargaron y el BPM medio: `12 tracks · avg 102 BPM`.

**No cierres la ventana negra** mientras se está descargando. Es el motor de la discoteca.

### ¿Dónde se guardan los archivos?

```
C:\Users\TuNombre\Music\DiscoDownload\
```

(En español puede aparecer como `Música` en vez de `Music`)

---

## Problemas habituales y cómo solucionarlos

**La web muestra "yt-dlp not found"**
Cierra la ventana negra, ábrela de nuevo y asegúrate de haber ejecutado `uv tool install yt-dlp` en el Paso 4.

**Los archivos salen como .webm o .opus en vez de MP3/WAV**
Falta ffmpeg. Vuelve al Paso 3 y ejecútalo.

**No aparece el BPM en los archivos descargados**
El BPM solo se guarda en MP3. Para WAV, solo se muestra en pantalla. Si no aparece ni en pantalla, es posible que la canción sea muy corta o tenga un ritmo muy irregular.

**La web no carga en el navegador**
Comprueba que la ventana negra sigue abierta y no muestra ningún error rojo.

**Error "No module named flask" u otros módulos**
Arranca siempre con el `iniciar.bat`, no con `python ytweb.py` directamente.

---

## Compartir con tus colegas en la misma WiFi

Si quieres que un amigo use la web desde su móvil u ordenador (conectado a la misma red WiFi que tú), dile que entre a:

```
http://[TU-IP]:5555
```

Para saber tu IP, abre PowerShell y escribe `ipconfig`. Busca la línea `Dirección IPv4`. Algo como `192.168.1.XX`.

---

## La próxima vez que quieras usarlo

Los pasos de instalación son solo la primera vez. A partir de ahora:

1. **Doble clic en `iniciar.bat`**
2. Abrir el navegador en **http://localhost:5555**
3. ¡Pegar enlaces y darle al botón!

*Hecho con amor, boogie y mucho Studio 54.*
