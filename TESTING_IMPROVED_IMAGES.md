# Guía de Testing - Análisis de Imágenes Mejorado

## Mejoras Implementadas

### 1. Prompt Más Específico
El nuevo prompt es más directo y le dice a Groq EXACTAMENTE qué hacer:
- Buscar nombre, precio, categoría, descripción
- Responder SOLO con JSON
- Usar valores por defecto si no encuentra

### 2. Mejor Extracción de Datos
- Si el precio viene como string (ej: "$100"), extrae el número
- Si no hay producto, usa "Producto desconocido"
- Si no hay categoría, usa "Sin categoría"
- Nunca devuelve campos vacíos

### 3. Logging Detallado
Verás en el servidor:
```
✅ Análisis exitoso: {...}
📊 Resultado del análisis: {...}
  - Producto: 'Laptop Dell'
  - Precio: 1200.5
  - Categoría: 'Electrónica'
  - Descripción: 'Laptop de alto rendimiento'
```

## Cómo Probar

### Paso 1: Reiniciar servidor
```bash
python manage.py runserver
```

### Paso 2: Obtener token JWT
POST a `/api/token/`
```json
{
    "username": "tu_usuario",
    "password": "tu_contraseña"
}
```

Response:
```json
{
    "access": "TOKEN_AQUI",
    "refresh": "..."
}
```

### Paso 3: Analizar imagen
POST a `/api/images/`

**Headers:**
```
Authorization: Bearer TOKEN_AQUI
```

**Body (form-data):**
```
image: [seleccionar archivo de imagen]
```

**Qué esperar en el servidor (logs):**
```
Intento 1 de análisis de imagen
Respuesta de Groq: {"producto": "...", "precio_estimado": 100, ...}
✅ Análisis exitoso: {...}
📊 Resultado del análisis: {...}
  - Producto: 'nombre aquí'
  - Precio: número aquí
  - Categoría: 'categoría aquí'
  - Descripción: 'descripción aquí'
Análisis guardado. ID: 1, Resultado: {...}
```

**Response esperada (201):**
```json
{
    "id": 1,
    "user": 1,
    "image": "/media/images/...",
    "analysis_result": {
        "producto": "nombre del producto",
        "precio_estimado": 100.0,
        "categoria": "categoría",
        "descripcion": "descripción aquí"
    },
    "timestamp": "2025-12-11T...",
    "producto_created": null
}
```

## Si Aún No Funciona

### Solucionar en Thunder Client:

1. **Copiar la respuesta exacta de análisis_result**
2. **Ir a ver los logs en el servidor terminal** (es muy importante esto)
3. **Buscar líneas que digan:**
   - `Respuesta de Groq:` → Aquí ves lo que devolvió la IA
   - `✅ Análisis exitoso:` → Aquí ves lo que procesó
   - `📊 Resultado del análisis:` → Aquí ves los 4 campos

### Si el precio es 0:
- La IA no vio precio visible en la imagen
- Esto es normal si la imagen no muestra precio
- Puedes agregar el precio manualmente después

### Si el nombre es "Producto desconocido":
- La IA no reconoció la imagen
- Intenta con una imagen más clara
- Puede ser que sea un objeto muy poco común

### Si la categoría es "Sin categoría":
- La IA no pudo identificar la categoría
- Esto también es normal
- Puedes seleccionar manualmente después

## Testing en Android

```java
// 1. Obtener token (del login)
String token = "TOKEN_JWT_AQUI";

// 2. Subir imagen
File imageFile = new File("/path/to/image.jpg");

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

// 3. Obtener respuesta
Response response = client.newCall(request).execute();
JSONObject jsonResponse = new JSONObject(response.body().string());

// 4. Extraer datos (NUNCA serán null ahora)
JSONObject analysisResult = jsonResponse.getJSONObject("analysis_result");
String productName = analysisResult.getString("producto");
double price = analysisResult.getDouble("precio_estimado");
String category = analysisResult.getString("categoria");
String description = analysisResult.getString("descripcion");

// Los 4 campos SIEMPRE estarán presentes
Log.d("TAG", "Producto: " + productName);
Log.d("TAG", "Precio: " + price);
Log.d("TAG", "Categoría: " + category);
Log.d("TAG", "Descripción: " + description);
```

## Cambios Realizados

### `groq_utils.py`

1. **Prompt mejorado:**
   - Más específico y directo
   - Ejemplo de JSON esperado
   - Reglas claras sobre valores por defecto

2. **Mejor parsing:**
   - Extrae números de strings
   - Valida campos vacíos/null
   - Conversión robusta de precio

3. **Logging completo:**
   - ✅ para análisis exitoso
   - ❌ para errores
   - 🔄 para reintentos

### `views.py`

1. **Logs adicionales:**
   - 📊 Resultado del análisis
   - Detalles de cada campo

2. **Mejor debugging:**
   - Ver exactamente qué se retorna
   - Mensajes claros sobre errores

## Próximas Mejoras (Si Aún Hay Problemas)

1. Cambiar modelo de visión a uno más potente
2. Agregar OCR para extraer texto de la imagen
3. Usar múltiples prompts en paralelo
4. Agregar validación de imagen (brillo, contraste)
5. Guardar raw response de Groq para debugging

---

**Todos los cambios están en lugar. Reinicia el servidor y prueba nuevamente.**
