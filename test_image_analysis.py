#!/usr/bin/env python
"""
Script de prueba para análisis de imágenes
Prueba la función analyze_product_image_v2 directamente
"""

import os
import sys
import json
import base64
from pathlib import Path

# Agregar el proyecto al path
sys.path.insert(0, str(Path(__file__).parent / 'Control_de_Venta'))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Control_de_Venta.settings')
import django
django.setup()

from tienda.groq_utils import analyze_product_image_v2

def test_image_analysis(image_path):
    """
    Prueba el análisis de una imagen
    
    Args:
        image_path: Ruta a la imagen a analizar
    """
    if not os.path.exists(image_path):
        print(f"❌ Error: Imagen no encontrada en {image_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"📸 Analizando imagen: {image_path}")
    print(f"{'='*60}\n")
    
    # Leer la imagen
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    print(f"📦 Tamaño de imagen: {len(image_bytes)} bytes")
    print(f"⏳ Procesando con Groq (esto puede tardar ~30 segundos)...\n")
    
    # Analizar
    result = analyze_product_image_v2(image_bytes, max_retries=2)
    
    # Mostrar resultados
    print(f"\n{'='*60}")
    print(f"✅ RESULTADO DEL ANÁLISIS")
    print(f"{'='*60}\n")
    
    print(f"📦 Producto:       {result.get('producto')}")
    print(f"💰 Precio:         ${result.get('precio_estimado')}")
    print(f"🏷️  Categoría:      {result.get('categoria')}")
    print(f"📝 Descripción:     {result.get('descripcion')}")
    
    if result.get('error'):
        print(f"\n⚠️  Error: {result.get('error')}")
    
    print(f"\n{'='*60}")
    print(f"📊 JSON Completo:")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║  SCRIPT DE PRUEBA - ANÁLISIS DE IMÁGENES                 ║
║  Groq Vision (Llama 4 Maverick)                          ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) > 1:
        # Usar imagen del argumento
        image_path = sys.argv[1]
        test_image_analysis(image_path)
    else:
        # Buscar imágenes de prueba
        test_images = []
        for pattern in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']:
            test_images.extend(Path('.').glob(f'**/{pattern}'))
        
        if test_images:
            print(f"📁 Se encontraron {len(test_images)} imágenes\n")
            for i, img in enumerate(test_images[:3], 1):
                print(f"{i}. {img}")
                test_image_analysis(str(img))
        else:
            print("""
❌ No se encontraron imágenes para probar.

Uso:
  python test_image_analysis.py /ruta/a/imagen.jpg

Ejemplo:
  python test_image_analysis.py C:\\Users\\conto\\Pictures\\producto.jpg
            """)
