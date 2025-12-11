# Guía de Análisis de Imágenes - Backend Mejorado

## Cambios Realizados

Se implementó un sistema mejorado de análisis de imágenes con las siguientes características:

### 1. Función `analyze_product_image_v2()` en `groq_utils.py`

**Mejoras implementadas:**
- ✅ Validaciones de imagen (vacía, corrupta, tamaño máximo)
- ✅ Reintentos automáticos (hasta 3 intentos) en caso de fallo
- ✅ Extracción robusta de JSON desde respuestas
- ✅ Timeout de 30 segundos en la API
- ✅ **NUNCA devuelve null** - siempre un diccionario completo
- ✅ Logging detallado para debugging
- ✅ Fallback automático si la IA no reconoce producto

**Estructura de respuesta garantizada:**
```json
{
    "producto": "string (vacío si no se reconoce)",
    "precio_estimado": 0.0,
    "categoria": "string (vacío si no se reconoce)",
    "descripcion": "string",
    "error": "string (opcional, solo si hay error)"
}
```

### 2. ViewSet Mejorado en `views.py`

#### Endpoint: `POST /api/images/`

**Descripción:** Analiza una imagen sin crear producto

**Validaciones:**
- Verifica que la imagen se proporcionó
- Valida tipo MIME (jpeg, png, gif, webp)
- Manejo seguro de excepciones

**Request:**
```
POST /api/images/
Headers:
  Authorization: Bearer TOKEN_JWT
  
Body: form-data
  image: [archivo de imagen]
```

**Response (201 Created):**
```json
{
    "id": 1,
    "user": 1,
    "image": "/media/images/...",
    "analysis_result": {
        "producto": "Laptop Dell XPS",
        "precio_estimado": 1200.50,
        "categoria": "Electrónica",
        "descripcion": "Laptop de alto rendimiento"
    },
    "timestamp": "2025-12-11T12:00:00Z",
    "producto_created": null
}
```

#### Endpoint: `POST /api/images/create_producto_from_image/`

**Descripción:** Analiza imagen Y crea producto automáticamente

**Validaciones:**
- Valida imagen
- Requiere que se reconozca un nombre de producto
- Crea categoría automáticamente si no existe
- Genera código de producto automático

**Request:**
```
POST /api/images/create_producto_from_image/
Headers:
  Authorization: Bearer TOKEN_JWT
  
Body: form-data
  image: [archivo de imagen]
```

**Response (201 Created):**
```json
{
    "success": true,
    "message": "Producto 'Laptop Dell' creado exitosamente",
    "producto": {
        "id": 5,
        "nombre": "Laptop Dell",
        "codigo": "AUTO-image_file",
        "precio": 1200.50,
        "cantidad": 0,
        "categoria": 2
    },
    "analysis": {
        "id": 3,
        "user": 1,
        "image": "/media/images/...",
        "analysis_result": {
            "producto": "Laptop Dell",
            "precio_estimado": 1200.50,
            "categoria": "Electrónica",
            "descripcion": "Laptop de alto rendimiento"
        },
        "timestamp": "2025-12-11T12:00:00Z",
        "producto_created": 5
    }
}
```

**Response (400 Bad Request - Imagen no reconocida):**
```json
{
    "error": "No se pudo reconocer el producto en la imagen",
    "producto": null,
    "analysis": {
        "producto": "",
        "precio_estimado": 0.0,
        "categoria": "",
        "descripcion": "No se pudo reconocer el producto"
    }
}
```

### 3. Serializer Mejorado

El `ImageAnalysisSerializer` ahora:
- ✅ Garantiza que `analysis_result` NUNCA tenga campos null
- ✅ Convierte valores a tipos correctos
- ✅ Proporciona valores por defecto

**Campos garantizados:**
- `producto`: string (nunca null)
- `precio_estimado`: float >= 0 (nunca null)
- `categoria`: string (nunca null)
- `descripcion`: string (nunca null)

## Android - Integración

### Ejemplo de uso en Kotlin/Java

```java
// 1. Obtener token JWT primero
String token = getJWTToken(); // De tu login

// 2. Subir imagen y obtener análisis
File imageFile = new File(imagePath);

RequestBody requestBody = new MultipartBody.Builder()
    .setType(MultipartBody.FORM)
    .addFormDataPart("image", imageFile.getName(),
        RequestBody.create(imageFile, MediaType.parse("image/*")))
    .build();

Request request = new Request.Builder()
    .url("http://192.168.100.42:8000/api/images/")
    .addHeader("Authorization", "Bearer " + token)
    .post(requestBody)
    .build();

// 3. Procesar respuesta
Response response = client.newCall(request).execute();
String jsonResponse = response.body().string();
JSONObject analysisResult = new JSONObject(jsonResponse);

// Los campos SIEMPRE estarán presentes
String productName = analysisResult.getJSONObject("analysis_result")
    .getString("producto"); // Nunca null
double price = analysisResult.getJSONObject("analysis_result")
    .getDouble("precio_estimado"); // Nunca null
```

### Crear producto desde imagen

```java
// Usar el endpoint create_producto_from_image
Request request = new Request.Builder()
    .url("http://192.168.100.42:8000/api/images/create_producto_from_image/")
    .addHeader("Authorization", "Bearer " + token)
    .post(requestBody)
    .build();

// Response incluye el producto creado
JSONObject productData = new JSONObject(response.body().string())
    .getJSONObject("producto");
int productId = productData.getInt("id");
String productCode = productData.getString("codigo");
```

## Manejo de Errores

### Errores posibles y cómo manejarlos:

```json
{
    "error": "No se proporcionó una imagen.",
    "analysis_result": {
        "producto": "",
        "precio_estimado": 0.0,
        "categoria": "",
        "descripcion": "Imagen no proporcionada"
    }
}
```

**Códigos HTTP:**
- `201 Created` - Análisis exitoso
- `400 Bad Request` - Imagen inválida o no reconocida
- `401 Unauthorized` - Token JWT inválido
- `500 Internal Server Error` - Error en servidor

## Debugging

Para ver logs detallados, revisa:

```bash
# En el servidor Django
python manage.py runserver

# Verás logs como:
# INFO - Intento 1 de análisis de imagen
# INFO - Respuesta de Groq: {...}
# INFO - Análisis exitoso: {...}
# INFO - Análisis guardado. ID: 1, Resultado: {...}
```

## Pruebas en Thunder Client

### Test 1: Análisis simple

```
POST http://192.168.100.42:8000/api/images/
Headers:
  Authorization: Bearer TOKEN_JWT
  
Body: form-data
  image: [seleccionar archivo de imagen]
```

### Test 2: Crear producto

```
POST http://192.168.100.42:8000/api/images/create_producto_from_image/
Headers:
  Authorization: Bearer TOKEN_JWT
  
Body: form-data
  image: [seleccionar archivo de imagen]
```

## Notas importantes

1. **Las imágenes SIEMPRE se procesan** - Si falla la IA, se reintentan hasta 2 veces
2. **Los campos NUNCA son null** - Usa valores vacíos para strings y 0 para números
3. **Timeout de 30 segundos** - Si tarda más, se marca como error
4. **Tamaño máximo: 10 MB** - Imágenes más grandes se rechazan
5. **Tipos permitidos: JPEG, PNG, GIF, WebP**

## Cambios en la base de datos

No se requieren migraciones nuevas. El modelo `ImageAnalysis` ya almacena `analysis_result` como JSONField.

## Próximos pasos opcionales

1. Agregar caché de análisis para imágenes idénticas
2. Implementar feedback de usuario para mejorar el modelo
3. Agregar webhook para notificar al cliente cuando termina el análisis
4. Implementar análisis en lote para múltiples imágenes
