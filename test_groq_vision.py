"""
Test simple para verificar que Groq + Llama 4 Scout funciona con visión
"""

import base64
from groq import Groq

# === CONFIGURACIÓN ===
GROQ_API_KEY = "GROQ_API_KEY"  # ← REEMPLAZAR CON TU KEY
IMAGE_PATH = "test_image.png"  # ← Imagen de prueba (screenshot de Pokémon)

def test_groq_vision():
    print("🧪 TEST: Groq + Llama 4 Scout con Visión\n")
    
    # Inicializar cliente
    client = Groq(api_key=GROQ_API_KEY)
    print("✅ Cliente Groq inicializado")
    
    # Leer imagen y convertir a base64
    try:
        with open(IMAGE_PATH, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        print(f"✅ Imagen cargada: {IMAGE_PATH}")
    except FileNotFoundError:
        print(f"❌ ERROR: No se encuentra la imagen '{IMAGE_PATH}'")
        print("   Guarda un screenshot de Pokémon como 'test_image.png'")
        return
    
    # Crear prompt de prueba
    prompt = """You are a Pokémon game expert. Look at this screenshot and answer:

1. What do you see in this image?
2. Where is the player located?
3. What should the player do next?

Respond in a single key. Just with A or B or UP or DOWN or LEFT or RIGHT OR START
Do not add a dot at the end of the answer.
"""
    
    print("\n📤 Enviando request a Groq...")
    
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }],
            max_tokens=200,
            temperature=0.7
        )
        
        print("✅ Respuesta recibida\n")
        print("="*70)
        print("🤖 RESPUESTA DEL LLM:")
        print("="*70)
        print(response.choices[0].message.content)
        print("="*70)
        
        # Mostrar metadata
        print(f"\n📊 METADATA:")
        print(f"   - Modelo: {response.model}")
        print(f"   - Tokens usados: {response.usage.total_tokens}")
        print(f"   - Tiempo: {response.usage.total_time if hasattr(response.usage, 'total_time') else 'N/A'}")
        
        print("\n✅ TEST EXITOSO - Groq con visión funciona correctamente")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR en la llamada a Groq:")
        print(f"   {type(e).__name__}: {e}")
        
        if "API key" in str(e):
            print("\n💡 Verifica que tu API key sea correcta")
        elif "rate limit" in str(e):
            print("\n💡 Has excedido el rate limit (30 req/min)")
        elif "model" in str(e):
            print("\n💡 El modelo puede no estar disponible o el nombre es incorrecto")
        
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    success = test_groq_vision()
    print("="*70 + "\n")
    
    if success:
        print("🎉 Todo listo para usar el agente!")
    else:
        print("⚠️  Corrige los errores antes de continuar")
