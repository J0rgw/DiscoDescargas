# DISCO DOWNLOAD
### *La Máquina Extractora de Música de Studio 54*

¡Bienvenido/a a la pista, crack! Esta herramienta descarga música de YouTube y la guarda en tu ordenador como **MP3** o **WAV**. Sin anuncios, sin suscripciones, sin cuentas. Solo tú, los enlaces y el boogie.

> **Nota legal:**No uses las descargas para usos ilegales ni revendas la musica. Respeta a los artistas, que ellos también tienen que pagar el alquiler.
> Esto es un proyecto para jugar a un juego de ritmo con mis canciones favoritas

---

## ¿Qué necesitas instalar? (solo la primera vez)

Para que todo funcione necesitas cuatro cosas. No te asustes, las instalamos paso a paso:

| Programa | Para qué sirve |
|----------|----------------|
| **uv** | Gestiona Python (el idioma en el que está hecha la app) |
| **ffmpeg** | Convierte el audio a MP3 o WAV |
| **yt-dlp** | Descarga el audio de YouTube |
| **flask** | Pone en marcha la web en tu ordenador |

---

## Paso 1 - Abre PowerShell como administrador

1. Pulsa la tecla **Windows** y escribe `PowerShell`
2. Haz **clic derecho** sobre "Windows PowerShell" y selecciona **Ejecutar como administrador**
3. Si aparece una ventana preguntando "¿Deseas permitir...?", pulsa **Sí**

Deja esa ventana abierta. Vamos a usarla mucho.

---

## Paso 2 - Instala uv

Copia este comando, pégalo en PowerShell y pulsa **Enter**:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verás texto moviéndose. Cuando pare y vuelva a aparecer el cursor, **cierra PowerShell y ábrelo de nuevo** (importante para que se actualice).

---

## Paso 3 - Instala ffmpeg

**ffmpeg** es el que convierte el audio. Sin él, los archivos salen en formato raro en vez de MP3 o WAV.

En PowerShell (el que acabas de abrir de nuevo):

```
winget install ffmpeg
```

Si te pide confirmación, escribe `Y` y pulsa Enter. Espera a que termine.

**¿Ves un error con winget?** Es posible que necesites actualizar el App Installer de Windows desde la Microsoft Store. Búscalo, actualízalo y vuelve a intentarlo.

---

## Paso 4 - Instala yt-dlp

```
uv tool install yt-dlp
```

---

## Paso 5 - Arranca la discoteca

**Opción fácil - doble clic:**
Haz doble clic en el archivo `iniciar.bat` que está en la carpeta del proyecto. Se abrirá una ventana negra: déjala abierta mientras usas la web.

**Opción por PowerShell:**
```
uv run --with flask ytweb.py
```

Cuando veas algo como `* Running on http://127.0.0.1:5555`, ¡la discoteca está abierta!

---

## Cómo usar Disco Download

1. Abre tu navegador (Chrome, Firefox, Edge... el que uses)
2. Ve a: **http://localhost:5555**
3. Pega los enlaces de YouTube que quieras descargar, **uno por línea**.
4. Si quieres descargar una lista de reproducción completa, marca la casilla **Playlist completa** antes de pulsar el botón. Sin marcarla, solo se descarga el vídeo concreto que apunta el enlace.
5. Elige el formato:
   - **MP3** - para escuchar en el móvil, en el coche, en cualquier sitio. El más compatible.
   - **WAV** - calidad máxima, sin compresión. Ocupa más espacio. Para los puristas del sonido.
6. Pulsa el botón dorado **GET DOWN**
7. La página mostrará el estado de cada descarga en tiempo real: **waiting** (en cola), **downloading** (descargando), **done** (listo) o **error** (algo fue mal). Se actualiza sola cada dos segundos hasta que todo termine.

**No cierres la ventana negra de PowerShell** mientras se está descargando. Es el motor de la discoteca.

### ¿Dónde se guardan los archivos?

En tu carpeta de Música, dentro de una carpeta llamada **DiscoDownload**:

```
C:\Users\TuNombre\Music\DiscoDownload\
```

(En español puede aparecer como `Música` en vez de `Music`)

---

## Problemas habituales y cómo solucionarlos

**La web muestra "yt-dlp not found"**
Cierra PowerShell, ábrelo de nuevo y ejecuta `uv tool install yt-dlp` otra vez.

**Los archivos salen como .webm o .opus en vez de MP3/WAV**
Falta ffmpeg. Vuelve al Paso 3 y ejecútalo.

**Error "No module named flask"**
Arranca el servidor con `uv run --with flask ytweb.py` (no con `python ytweb.py`).

**La web no carga en el navegador**
Comprueba que la ventana negra de PowerShell sigue abierta y no muestra ningún error rojo.

---

## Compartir con tus colegas en la misma WiFi

Si quieres que un amigo use la web desde su móvil u ordenador (conectado a la misma red WiFi que tú), dile que entre a:

```
http://[TU-IP]:5555
```

Para saber tu IP, abre PowerShell y escribe:

```
ipconfig
```

Busca la línea `Dirección IPv4`. Algo como `192.168.1.XX`.

---

## ¡A bailar!

Una vez que todo funcione, no necesitas repetir los pasos de instalación. La próxima vez que quieras usarlo, solo tienes que:

1. Doble clic en `iniciar.bat`
2. Abrir el navegador en **http://localhost:5555**
3. ¡Pegar enlaces y darle al botón!

*Hecho con amor, boogie y mucho Studio 54.*
