"""
Utilidades para integración con Groq API.
Usa dos modelos:
- Llama 3.3 70B (chat normal, análisis)
- Llama 4 Maverick (visión - fotos)
"""
import os
import json
import base64
from io import BytesIO
from groq import Groq

# APIs keys para cada modelo
GROQ_API_KEY_CHAT = os.getenv('GROQ_API_KEY_CHAT', '')
GROQ_API_KEY_VISION = os.getenv('GROQ_API_KEY_VISION', '')

# Modelos disponibles en Groq (Diciembre 2025)
MODEL_CHAT = "llama-3.3-70b-versatile"  # Para chat y análisis
MODEL_VISION = "meta-llama/llama-4-maverick-17b-128e-instruct"  # Para visión (fotos)

def get_groq_client_chat():
    """Retorna cliente Groq configurado para chat (Llama 3.3 70B)."""
    return Groq(api_key=GROQ_API_KEY_CHAT)


def get_groq_client_vision():
    """Retorna cliente Groq configurado para visión (Llama 4 Maverick)."""
    return Groq(api_key=GROQ_API_KEY_VISION)


def chat_with_groq(user_message, context=None, history=None):
    """
    Envía un mensaje a Llama 3.3 70B y retorna la respuesta.
    
    Args:
        user_message: Mensaje del usuario.
        context: Contexto adicional (ej. lista de productos, tendencias).
        history: Historial de conversación anterior (lista de dicts).
    
    Returns:
        str: Respuesta de Groq.
    """
    client = get_groq_client_chat()
    
    # Construir el prompt con contexto si se proporciona
    system_prompt = """Eres un asistente IA especializado en gestión de inventario y ventas.
Tu rol es ayudar a usuarios a:
- Consultar información sobre productos (precio, stock)
- Analizar tendencias de ventas
- Sugerir niveles de reorden de stock
- Responder preguntas sobre el negocio
- Identificar productos a partir de descripciones

Sé conciso, útil y directo. Responde en español."""
    
    if context:
        system_prompt += f"\n\nContexto actual del negocio:\n{context}"
    
    # Preparar mensajes: historial + nuevo
    messages = history or []
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model=MODEL_CHAT,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al consultar Groq (chat): {str(e)}"


def analyze_image_with_groq(image_bytes, prompt=None):
    """
    Analiza una imagen con Llama 4 Maverick (visión).
    
    Args:
        image_bytes: Bytes de la imagen.
        prompt: Prompt opcional para el análisis.
    
    Returns:
        str: Análisis de la imagen.
    """
    client = get_groq_client_vision()
    
    # Convertir a base64
    image_b64 = base64.standard_b64encode(image_bytes).decode('utf-8')
    
    default_prompt = prompt or """Analiza esta imagen y extrae la siguiente información si está disponible:
1. Nombre o descripción del producto
2. Código o SKU del producto
3. Precio (si es visible)
4. Cantidad o unidad de medida
5. Marca (si aplica)
6. Cualquier otra información relevante

Responde en formato JSON con las claves: nombre, codigo, precio, cantidad, marca, observaciones"""
    
    try:
        # Formato correcto para Groq Vision API
        image_url = f"data:image/jpeg;base64,{image_b64}"
        
        response = client.chat.completions.create(
            model=MODEL_VISION,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": default_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            temperature=0.5,
            max_tokens=512,
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({"error": f"Error al analizar imagen (visión): {str(e)}"})


def generate_stock_suggestions(productos_info):
    """
    Genera sugerencias de reorden de stock basadas en historial.
    Usa Llama 3.3 70B para análisis.
    
    Args:
        productos_info: Dict con info de productos y ventas.
    
    Returns:
        str: Sugerencias en texto.
    """
    client = get_groq_client_chat()
    
    prompt = f"""Basándote en los siguientes datos de inventario y ventas, sugiere qué productos deberían reordenarse:

{json.dumps(productos_info, indent=2, ensure_ascii=False)}

Considera:
- Stock actual vs. demanda
- Velocidad de venta
- Margen de seguridad recomendado (20-30% sobre demanda promedio)
- Productos sin movimiento reciente

Responde con una lista priorizada de productos a reabastecer, incluyendo cantidad sugerida."""
    
    try:
        response = client.chat.completions.create(
            model=MODEL_CHAT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al generar sugerencias (chat): {str(e)}"


def analyze_sales_trends(ventas_info):
    """
    Analiza tendencias de ventas.
    Usa Llama 3.3 70B para análisis.
    
    Args:
        ventas_info: Dict con data de ventas por período/producto.
    
    Returns:
        str: Análisis de tendencias.
    """
    client = get_groq_client_chat()
    
    prompt = f"""Analiza las siguientes tendencias de ventas y proporciona insights:

{json.dumps(ventas_info, indent=2, ensure_ascii=False)}

Identifica:
1. Productos con mayor crecimiento/decrecimiento
2. Patrones estacionales o semanales
3. Clientes más activos
4. Oportunidades de venta cruzada
5. Recomendaciones estratégicas

Sé conciso pero informativo."""
    
    try:
        response = client.chat.completions.create(
            model=MODEL_CHAT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al analizar tendencias (chat): {str(e)}"


def analyze_product_image_v2(image_bytes, max_retries=2):
    """
    Analiza una imagen de producto con Groq Vision (Llama 4 Maverick).
    Versión mejorada con validaciones, reintentos y fallbacks.
    
    Args:
        image_bytes: Bytes de la imagen.
        max_retries: Número máximo de reintentos si falla.
    
    Returns:
        dict: Siempre retorna un diccionario con los campos:
            - producto (str): Nombre del producto
            - precio_estimado (float): Precio estimado
            - categoria (str): Categoría del producto
            - descripcion (str): Descripción
            - error (str, opcional): Si hay error, se incluye aquí
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Validaciones iniciales
    if not image_bytes or len(image_bytes) == 0:
        logger.warning("Imagen vacía recibida")
        return {
            "producto": "",
            "precio_estimado": 0.0,
            "categoria": "",
            "descripcion": "Imagen vacía o corrupta",
            "error": "La imagen está vacía"
        }
    
    # Limitar tamaño máximo (10MB)
    if len(image_bytes) > 10 * 1024 * 1024:
        logger.warning(f"Imagen demasiado grande: {len(image_bytes)} bytes")
        return {
            "producto": "",
            "precio_estimado": 0.0,
            "categoria": "",
            "descripcion": "Archivo de imagen muy grande",
            "error": "La imagen excede el tamaño máximo (10MB)"
        }
    
    client = get_groq_client_vision()
    
    # Convertir a base64
    try:
        image_b64 = base64.standard_b64encode(image_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Error al codificar imagen a base64: {str(e)}")
        return {
            "producto": "",
            "precio_estimado": 0.0,
            "categoria": "",
            "descripcion": "Error al procesar la imagen",
            "error": "La imagen está corrupta"
        }
    
    prompt = """Analiza esta imagen y responde SOLO con JSON válido.

Identifica:
1. Producto: nombre, marca, modelo
2. Precio: si es visible (o 0)
3. Categoría: OBLIGATORIO elegir UNA:
   • Almacenamiento (USB, discos, memorias)
   • Electrónica (computadoras, cables, cámaras, teléfonos, mouses, teclados)
   • Ropa (prendas, calzado)
   • Alimentos (comida, bebidas)
   • Hogar (muebles, decoración)
   • Oficina (papelería, útiles)
   • Otro
4. Descripción: detalla lo que ves (mínimo 10 palabras)

Ejemplo de respuesta:
{
    "producto": "SanDisk Cruzer USB 16GB",
    "precio_estimado": 15.99,
    "categoria": "Almacenamiento",
    "descripcion": "Memoria USB portátil de color verde marca SanDisk"
}

REGLAS:
- categoria SIEMPRE debe tener valor de la lista
- precio_estimado = 0 si no es visible
- SOLO JSON, sin texto extra"""
    
    retry_count = 0
    last_error = None
    
    while retry_count <= max_retries:
        try:
            logger.info(f"Intento {retry_count + 1} de análisis de imagen")
            
            # Formato correcto para Groq Vision API
            image_url = f"data:image/jpeg;base64,{image_b64}"
            
            response = client.chat.completions.create(
                model=MODEL_VISION,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                temperature=0.3,
                max_tokens=512,
                timeout=30  # Timeout de 30 segundos
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Respuesta de Groq: {response_text}")
            
            # Intentar parsear JSON
            try:
                analysis_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Si no es JSON válido, intentar extraer JSON de la respuesta
                logger.warning("Respuesta no es JSON válido, intentando extraer...")
                try:
                    # Buscar JSON entre { }
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        analysis_data = json.loads(json_str)
                    else:
                        raise ValueError("No se encontró JSON en la respuesta")
                except Exception as json_error:
                    logger.error(f"No se pudo extraer JSON: {str(json_error)}")
                    analysis_data = None
            
            if analysis_data:
                # Validar y limpiar datos con conversión segura
                try:
                    # Extraer y limpiar nombre del producto
                    producto = str(analysis_data.get("producto", "")).strip()
                    if not producto or producto.lower() in ["", "null", "undefined"]:
                        producto = "Producto desconocido"
                    
                    # Extraer y convertir precio
                    precio_raw = analysis_data.get("precio_estimado", 0)
                    try:
                        if isinstance(precio_raw, str):
                            # Si es string, extraer números
                            import re
                            numeros = re.findall(r'\d+\.?\d*', precio_raw)
                            precio_estimado = float(numeros[0]) if numeros else 0.0
                        else:
                            precio_estimado = float(precio_raw) if precio_raw else 0.0
                    except (ValueError, TypeError):
                        precio_estimado = 0.0
                    
                    # Extraer categoría
                    categoria = str(analysis_data.get("categoria", "")).strip()
                    if not categoria or categoria.lower() in ["", "null", "undefined", "sin categoría"]:
                        categoria = "Sin categoría"
                    
                    # Extraer descripción
                    descripcion = str(analysis_data.get("descripcion", "")).strip()
                    if not descripcion or descripcion.lower() in ["", "null", "undefined"]:
                        descripcion = f"Imagen de {producto}"
                    
                    resultado = {
                        "producto": producto,
                        "precio_estimado": precio_estimado,
                        "categoria": categoria,
                        "descripcion": descripcion
                    }
                    
                    logger.info(f"✅ Análisis exitoso: {resultado}")
                    return resultado
                    
                except Exception as conversion_error:
                    logger.error(f"❌ Error al procesar datos: {str(conversion_error)}")
                    logger.error(f"Datos crudos: {analysis_data}")
                    raise
            else:
                raise ValueError("Análisis devolvió datos vacíos")
        
        except Exception as e:
            last_error = str(e)
            logger.warning(f"❌ Intento {retry_count + 1} falló: {last_error}")
            retry_count += 1
            
            if retry_count <= max_retries:
                logger.info(f"🔄 Reintentando análisis (intento {retry_count + 1}/{max_retries + 1})...")
                continue
    
    # Fallback: devolver estructura válida sin datos
    logger.error(f"Análisis falló después de {max_retries + 1} intentos. Último error: {last_error}")
    return {
        "producto": "",
        "precio_estimado": 0.0,
        "categoria": "",
        "descripcion": "No se pudo reconocer el producto",
        "error": f"Error en IA después de {max_retries + 1} intentos: {last_error}"
    }
