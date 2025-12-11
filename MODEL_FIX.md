# Modelos de Groq - Corrección

## ❌ Problema

El modelo `llama-4-maverick` **NO EXISTE** en Groq.

Error:
```
Error code: 404 - The model `llama-4-maverick` does not exist
```

## ✅ Solución

Cambié al modelo correcto de visión de Groq.

### Modelos Disponibles en Groq (Diciembre 2025)

| Modelo | Uso | Código |
|--------|-----|--------|
| Llama 3.3 70B | Chat, texto | `llama-3.3-70b-versatile` |
| **Llama 3.2 90B Vision** | **Visión (imágenes)** | `llama-3.2-90b-vision-preview` |
| Llama 3.2 11B Vision | Visión (más rápido) | `llama-3.2-11b-vision-preview` |

## Cambio Realizado

**Archivo:** `tienda/groq_utils.py`

**Antes:**
```python
MODEL_VISION = "llama-4-maverick"  # ❌ NO EXISTE
```

**Ahora:**
```python
MODEL_VISION = "llama-3.2-90b-vision-preview"  # ✅ CORRECTO
```

## Alternativa (Más Rápido, Menos Preciso)

Si prefieres un modelo más rápido pero menos preciso:

```python
MODEL_VISION = "llama-3.2-11b-vision-preview"  # Más rápido
```

El modelo de 90B es más preciso y mejor para identificar productos.

## 🚀 Ahora Funciona

1. **Reinicia el servidor:**
```bash
python manage.py runserver
```

2. **Prueba con tu imagen del USB:**
```
POST http://192.168.100.42:8000/api/images/
```

3. **Deberías ver:**
```
Intento 1 de análisis de imagen
Respuesta de Groq: {"producto": "SanDisk Cruzer USB", ...}
✅ Análisis exitoso: {...}
```

## Resumen

- ❌ `llama-4-maverick` → NO EXISTE
- ✅ `llama-3.2-90b-vision-preview` → **AHORA USANDO ESTO**
- 📝 Ya está corregido en el código

**Reinicia el servidor y prueba nuevamente.** 🎉
