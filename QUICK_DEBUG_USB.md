# ⚡ QUICK DEBUGGING - Imagen de USB SanDisk

## El Problema Observado

Tu app muestra:
- Nombre: vacío ❌
- Precio: 0.0 ❌  
- Categoría: vacía ❌

Imagen: SanDisk USB (verde) ✓

## Solución Rápida - 3 Pasos

### Paso 1: Reinicia el servidor
```bash
# Terminal del servidor
python manage.py runserver
```

### Paso 2: Abre Thunder Client

**POST a este endpoint NUEVO DE DEBUG:**
```
http://192.168.100.42:8000/api/images/debug_analysis/
```

**Headers:**
```
Authorization: Bearer [tu_token_jwt]
Content-Type: multipart/form-data
```

**Body:**
- Selecciona `form-data`
- Clave: `image`
- Valor: [selecciona la misma foto del USB]

**Click SEND**

### Paso 3: Lee la respuesta

**En Thunder Client verás:**
```json
{
    "message": "DEBUG - Ver logs del servidor para respuesta RAW",
    "raw_response": "{...}"
}
```

**En la TERMINAL del servidor verás (busca 🔍):**
```
🔍 RESPUESTA RAW DE GROQ:
{"producto": "SanDisk Cruzer USB 2.0", "precio_estimado": 25, "categoria": "Almacenamiento", "descripcion": "..."}
```

O esto si falla:

```
🔍 RESPUESTA RAW DE GROQ:
Producto no reconocido
```

## ¿Qué significa cada resultado?

### ✅ Si ves JSON con datos:
```
🔍 RESPUESTA RAW DE GROQ:
{"producto": "SanDisk Cruzer", "precio_estimado": 25, ...}
```

**Significado:** ✅ **Groq funciona perfectamente**

**Siguiente paso:** El problema está en tu app Android
- Verifica que parseés `analysis_result`
- Asegúrate de leer los campos correctamente

**Código Android correcto:**
```kotlin
val analysisResult = response.getJSONObject("analysis_result")
val producto = analysisResult.getString("producto")
val precio = analysisResult.getDouble("precio_estimado")
```

---

### ❌ Si ves "Producto no reconocido":
```
🔍 RESPUESTA RAW DE GROQ:
Producto no reconocido
```

**Significado:** ❌ **Groq no reconoce la imagen**

**Soluciones:**
1. Toma la foto en mejor luz (no debe tener sombras)
2. Asegúrate de que el USB sea visible y completo
3. Prueba con otro producto diferente
4. Prueba con esta URL alternativa (sin echo de debug):

```
POST /api/images/
```

En lugar de:
```
POST /api/images/debug_analysis/
```

---

### ⚠️ Si ves error de API:
```
Error al analizar imagen (visión): Connection error
```

**Significado:** ❌ **Error de conexión a Groq**

**Verificar:**
1. ¿Tienes internet?
2. ¿Las API keys en `.env` son correctas?
3. ¿Groq está online?

**Para verificar API keys:**
```bash
# En tu terminal (dentro del proyecto)
python
>>> import os
>>> from dotenv import load_dotenv
>>> load_dotenv()
>>> print(os.getenv('GROQ_API_KEY_VISION'))
# Deberá mostrar algo como: gsk_Xa4bsob6tw...
```

---

## Resumen Rápido

| Resultado | Significado | Solución |
|-----------|------------|----------|
| JSON con datos | ✅ Backend OK | Revisar app Android |
| "Producto no reconocido" | ❌ Groq no ve imagen | Mejor foto/iluminación |
| Error de conexión | ❌ Error de API | Verificar internet/keys |

---

## Archivo Completo de Debug

Para referencia completa, ver: `DEBUG_ENDPOINT_GUIDE.md`

**Status:** El endpoint `/api/images/debug_analysis/` ya está listo para usar. 🚀
