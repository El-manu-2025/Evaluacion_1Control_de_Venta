# Debugging - Endpoint de Análisis de Imágenes

## El Problema

Tu app Android está recibiendo campos vacíos en la respuesta del análisis. Esto puede ser porque:

1. El backend no está procesando bien la imagen
2. Groq no está devolviendo JSON válido
3. La app no está parseando la respuesta correctamente

## Solución - Usar Endpoint de Debug

He agregado un nuevo endpoint para ver exactamente qué devuelve Groq sin procesamiento.

### Paso 1: Reiniciar servidor
```bash
python manage.py runserver
```

### Paso 2: Usar Thunder Client para probar

**Endpoint de DEBUG:**
```
POST http://192.168.100.42:8000/api/images/debug_analysis/
```

**Headers:**
```
Authorization: Bearer TOKEN_JWT
```

**Body (form-data):**
```
image: [seleccionar archivo de imagen]
```

### Paso 3: Ver la respuesta RAW en los logs

En la terminal del servidor verás algo como:

```
🔍 RESPUESTA RAW DE GROQ:
{"producto": "SanDisk Cruzer USB 2.0", "precio_estimado": 25, "categoria": "Almacenamiento", "descripcion": "..."}
```

O esto si hay problema:

```
🔍 RESPUESTA RAW DE GROQ:
Producto no reconocido
```

### Paso 4: Interpretar los resultados

**Si ves JSON:**
```json
{
    "producto": "nombre",
    "precio_estimado": 25,
    "categoria": "Almacenamiento"
}
```
✅ **Groq funciona bien** - El problema es en cómo la app parsea la respuesta

**Si ves "Producto no reconocido":**
❌ **Groq no reconoce la imagen** - Necesitamos mejorar el prompt o usar una imagen más clara

**Si ves "Error":**
❌ **Error en API Groq** - Verifica las API keys

## Comparar Endpoints

### `/api/images/` (Normal)
```
POST /api/images/
Response: {
    "analysis_result": {
        "producto": "nombre extraído",
        "precio_estimado": 25,
        ...
    }
}
```

### `/api/images/debug_analysis/` (DEBUG)
```
POST /api/images/debug_analysis/
Server logs: 🔍 RESPUESTA RAW DE GROQ: {...}
Response: {
    "message": "DEBUG - Ver logs del servidor",
    "raw_response": "{...}"
}
```

## Pasos Completos para Debugging

### 1. Prueba con Thunder Client primero

```
POST http://192.168.100.42:8000/api/images/debug_analysis/
```

Mira en los logs qué devuelve Groq exactamente.

### 2. Si Groq devuelve JSON válido

El problema es que tu app Android no está parseando bien.

**Solución en Android:**
```kotlin
// Asegúrate de que estés leyendo "analysis_result"
val analysisResult = jsonResponse.getJSONObject("analysis_result")
val producto = analysisResult.getString("producto")
val precio = analysisResult.getDouble("precio_estimado")
val categoria = analysisResult.getString("categoria")
```

### 3. Si Groq devuelve "Producto no reconocido"

El problema es que Groq no reconoce la imagen.

**Soluciones:**
- Toma una foto más clara y bien iluminada
- Asegúrate de que el producto sea visible
- Prueba con un producto diferente primero

### 4. Si Groq devuelve error

Verifica las API keys en `.env`

## Nuevo Endpoint en URLs

El endpoint `/api/images/debug_analysis/` ya está automáticamente disponible porque está registrado con `@action`.

URL completa:
```
http://192.168.100.42:8000/api/images/debug_analysis/
```

## Qué esperar

### Respuesta exitosa (201):
```json
{
    "message": "DEBUG - Ver logs del servidor para respuesta RAW",
    "raw_response": "{\"producto\": \"SanDisk Cruzer\", \"precio_estimado\": 25, \"categoria\": \"Almacenamiento\", \"descripcion\": \"Memoria USB de almacenamiento portátil\"}"
}
```

### En los logs verás:
```
🔍 RESPUESTA RAW DE GROQ:
{"producto": "SanDisk Cruzer USB 2.0", ...}
```

## Próximas Acciones

Después de usar `/api/images/debug_analysis/`:

1. **Si Groq devuelve datos:**
   - Usa `/api/images/` normal
   - Verifica que tu app Android parsea correctamente

2. **Si Groq devuelve "Producto no reconocido":**
   - Prueba con mejor iluminación
   - Mejora el prompt en `groq_utils.py`

3. **Si hay error de API:**
   - Verifica API keys en `.env`
   - Verifica conexión a internet

## Resumen

**Endpoint de DEBUG agregado:** `POST /api/images/debug_analysis/`

Este endpoint:
- ✅ Acepta una imagen
- ✅ Devuelve la respuesta RAW de Groq
- ✅ No procesa ni valida datos
- ✅ Muestra exactamente qué devuelve la IA

**Usa este endpoint para entender qué está pasando, luego reporta en qué falla.**
