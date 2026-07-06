# Documento Funcional — Remote Printer Bot

## Propósito

Remote Printer Bot permite imprimir documentos de forma remota a través de Telegram. El usuario envía un archivo desde su teléfono o computadora, configura las opciones de impresión desde el chat, y el documento se imprime físicamente en la impresora conectada al servidor.

---

## Roles

| Rol | Descripción |
|---|---|
| **Administrador** | ID configurado en el servidor. Puede agregar, editar y eliminar usuarios. |
| **Usuario autorizado** | ID habilitado por el admin. Puede imprimir y gestionar sus propias impresiones. |
| **Usuario no autorizado** | Cualquier otro. Solo puede ver su propio ID para pedirle acceso al admin. |

---

## Acceso y bienvenida

### Usuario no autorizado
Cuando alguien que no está habilitado escribe al bot, este le responde informando que el bot es privado y le muestra su ID de Telegram para que se lo pase al administrador y solicite acceso.

### Usuario autorizado
Al escribir `/start` o `/help`, el bot muestra la lista completa de comandos disponibles.

---

## Imprimir un documento

El flujo principal del bot. El usuario envía un archivo al chat y el bot le presenta un menú interactivo para configurar la impresión antes de confirmar.

### Archivos aceptados
PDF, JPG, JPEG, PNG y TXT.

### Flujo

1. El usuario envía el archivo (opcionalmente con un caption indicando páginas específicas).
2. El bot responde con el menú de configuración.
3. El usuario ajusta los parámetros usando los botones.
4. El usuario confirma con **Imprimir** o descarta con **Cancelar**.
5. El bot notifica el resultado.

Si el usuario tiene nombre configurado, los mensajes son personalizados. Si no, son genéricos equivalentes.

### Menú de configuración por trabajo

```
Hola, Alice! 📄 documento.pdf

Ajustá la configuración antes de imprimir:
  Copias:  1
  Color:   color
  Lados:   Simple
  Papel:   A4
  Páginas: Todas

[➖] [1 copia(s)] [➕]
[🎨 Color]
[📄 Simple]
[📐 A4]
[📑 Todas]
[✅ Imprimir]  [❌ Cancelar]
```

Cada botón actualiza el menú en tiempo real sin abrir una pantalla nueva.

### Parámetros disponibles

**Copias** — cantidad de copias a imprimir. Rango: 1 a 99. Se ajusta con los botones ➖ y ➕.

**Color** — alterna entre impresión a color y escala de grises.

**Lados** — cicla entre tres modos:
- Simple (una cara)
- Doble cara borde largo (orientación retrato)
- Doble cara borde corto (orientación paisaje)

**Papel** — cicla entre los tamaños disponibles: A4, Letter, A5, Legal.

**Páginas** — cicla entre tres presets:
- Todas
- Solo páginas impares
- Solo páginas pares

Para un rango personalizado (ej: páginas 1, 3 y 5 a 8), el usuario envía el archivo con el rango en el caption: `1,3,5-8`. El bot lo detecta automáticamente y lo preselecciona en el menú.

### Resultado

- **Éxito**: `"✅ ¡En camino, Alice! Se está imprimiendo documento.pdf."`
- **Error**: `"❌ Alice, no se pudo imprimir documento.pdf. Motivo: [descripción del error]."`

Si se envía un nuevo archivo mientras hay uno pendiente de confirmar, el anterior se descarta automáticamente.

---

## Configuración predeterminada (`/config`)

Cada usuario tiene una configuración predeterminada que se aplica automáticamente cuando envía un archivo. Se accede y modifica con `/config`.

El bot muestra el mismo tipo de menú interactivo con botones. Cada cambio se guarda inmediatamente.

```
⚙️ Configuración predeterminada

  Copias:  1
  Color:   color
  Lados:   Simple
  Papel:   A4

[➖] [1 copia(s)] [➕]
[🎨 Color]
[📄 Simple]
[📐 A4]
[✅ Listo]
```

La configuración predeterminada no afecta trabajos en curso, solo los futuros.

---

## Estado de la impresora (`/status`)

Muestra el estado actual de la impresora: si está activa, inactiva, o con algún error. Si el driver reporta niveles de tinta, se incluyen en la respuesta.

---

## Cola de impresión (`/queue`)

Muestra los trabajos que están actualmente en la cola de impresión con su identificador. Útil para saber si hay trabajos pendientes antes de enviar uno nuevo.

---

## Cancelar trabajos (`/cancel`)

- `/cancel` — cancela todos los trabajos en cola.
- `/cancel <id>` — cancela un trabajo específico usando el ID que muestra `/queue`.

---

## Historial (`/history`)

Muestra las últimas 10 impresiones del usuario con:
- Nombre del archivo
- Fecha y hora
- Estado (exitosa o con error)

El historial es individual — cada usuario solo ve sus propias impresiones.

---

## Gestión de usuarios (administrador)

El administrador gestiona los usuarios desde el servidor mediante scripts de consola. No es necesario acceder al bot ni editar archivos manualmente.

### Agregar usuarios
Solicita IDs de forma interactiva, uno por vez. Para cada uno, permite asignar un nombre opcional. Se ingresa `-1` para terminar.

### Eliminar un usuario
Solicita el ID a eliminar y lo quita del sistema junto con su nombre si lo tenía asignado.

### Editar el nombre de un usuario
Muestra la lista actual, solicita el ID a editar y permite cambiar o quitar el nombre.

### Listar usuarios
Muestra todos los usuarios habilitados con su nombre (si tienen uno asignado).

Cualquier cambio en la lista de usuarios requiere reiniciar el bot para que tome efecto.

---

## Mensajes personalizados

Si el administrador asigna un nombre a un usuario, el bot lo usa en sus mensajes:
- Saludo al recibir un archivo
- Confirmación de impresión exitosa
- Notificación de error

Los usuarios sin nombre asignado reciben mensajes equivalentes en forma genérica.

---

## Registro de actividad

El sistema registra automáticamente todos los eventos relevantes:
- Archivos recibidos
- Impresiones exitosas y fallidas
- Intentos de acceso no autorizado
- Cancelaciones de trabajos
- Cambios de configuración

Este registro queda almacenado localmente en el servidor y no es accesible desde el bot.
