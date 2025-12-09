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

# Modelos
MODEL_CHAT = "llama-3.3-70b-versatile"  # Para chat y análisis
MODEL_VISION = "llama-4-maverick"  # Para visión (fotos)

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
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64
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
