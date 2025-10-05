import ee
import sys

# El ID de proyecto CORRECTO de tu captura de pantalla
PROJECT_ID = 'canola-474118' 

print("--- Intentando inicializar Earth Engine ---")

try:
    # Intenta inicializar con tu proyecto
    ee.Initialize(project=PROJECT_ID)
    print("\n✅ ÉXITO: La inicialización de Earth Engine fue exitosa.")
    
    # Ahora, intentemos una operación muy simple para confirmar
    print("\n--- Intentando obtener datos de una imagen de prueba ---")
    imagen_prueba = ee.Image('srtm90_v4')
    info = imagen_prueba.getInfo()
    
    print(f"\nInformación de la imagen: {info['id']}")
    print("\n✅ ÉXITO: Se obtuvieron datos correctamente desde Earth Engine.")

except Exception as e:
    print(f"\n❌ FALLÓ: Ocurrió un error durante la prueba.")
    print(f"\nDETALLES DEL ERROR:\n{e}")
    sys.exit(1)

print("\n--- La prueba finalizó ---")