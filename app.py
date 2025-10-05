from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import ee
import os
import json

print("=" * 60)
print("BloomWatch Backend - Public Access Version")
print("=" * 60)

app = Flask(__name__)
CORS(app)

def initialize_earth_engine():
    """
    Inicializa Earth Engine con Service Account para acceso público
    """
    try:
        # Buscar archivo de credenciales JSON
        service_account_file = 'service-account-key.json'
        
        if os.path.exists(service_account_file):
            with open(service_account_file) as f:
                credentials_info = json.load(f)
            
            credentials = ee.ServiceAccountCredentials(
                email=credentials_info['client_email'],
                key_file=service_account_file
            )
            
            ee.Initialize(
                credentials=credentials,
                project='canola-474118'
            )
            print("✅ Earth Engine initialized with Service Account")
            print(f"   Email: {credentials_info['client_email']}")
            return True
            
        else:
            print("❌ service-account-key.json NOT FOUND")
            print("   Please download it from Google Cloud Console")
            print("   and place it in the same folder as app.py")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing Earth Engine: {e}")
        return False

# Inicializar al arrancar
ee_initialized = initialize_earth_engine()

def apply_scale_factors(image):
    optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    return image.addBands(optical_bands, None, True)

def cloud_mask_simple(image):
    qa = image.select('QA_PIXEL')
    cloud = qa.bitwiseAnd(1 << 3).eq(0)
    cloud_shadow = qa.bitwiseAnd(1 << 4).eq(0)
    mask = cloud.And(cloud_shadow)
    return image.updateMask(mask)

def add_indices(image):
    nir = image.select('SR_B5')
    red = image.select('SR_B4')
    green = image.select('SR_B3')
    blue = image.select('SR_B2')
    
    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
    yi = red.add(green).divide(2).subtract(blue).multiply(100).rename('YI')
    
    return image.addBands(ndvi).addBands(yi)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'Backend running correctly',
        'ee_initialized': ee_initialized,
        'public_access': True
    })

@app.route('/get-canola-layer', methods=['POST'])
def get_canola_layer():
    if not ee_initialized:
        return jsonify({
            'error': 'Earth Engine not initialized',
            'message': 'Service account credentials not configured'
        }), 500
    
    try:
        data = request.json
        
        city = data.get('city', 'regina')
        bounds_data = data.get('bounds')
        start_date = data.get('start_date', '2019-01-01')
        end_date = data.get('end_date', '2019-12-31')
        bloom_start = data.get('bloom_start', '2019-07-01')
        bloom_end = data.get('bloom_end', '2019-08-31')
        
        print(f"\nProcessing request for: {city}")
        print(f"   Dates: {start_date} to {end_date}")
        print(f"   Bloom: {bloom_start} to {bloom_end}")
        
        if bounds_data:
            coords = [bounds_data[0][0], bounds_data[0][1], bounds_data[1][0], bounds_data[1][1]]
            geometry = ee.Geometry.Rectangle(coords)
        else:
            geometry = ee.Geometry.Rectangle([-104.8, 50.2, -104.4, 50.7])
        
        l8_collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filterBounds(geometry) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUD_COVER', 50))
        
        count = l8_collection.size().getInfo()
        print(f"   Images found: {count}")
        
        if count == 0:
            return jsonify({
                'error': 'No images found for this period',
                'count': 0
            }), 404
        
        processed = l8_collection \
            .map(apply_scale_factors) \
            .map(cloud_mask_simple) \
            .map(add_indices)
        
        bloom_image = processed \
            .filterDate(bloom_start, bloom_end) \
            .median()
        
        vis_params = {
            'bands': ['SR_B4', 'SR_B3', 'SR_B2'],
            'min': 0.0,
            'max': 0.25,
            'gamma': 1.4
        }
        
        map_id_dict = bloom_image.getMapId(vis_params)
        tile_url = map_id_dict['tile_fetcher'].url_format
        
        print(f"   Layer generated successfully")
        print(f"   Tile URL: {tile_url[:80]}...")
        
        return jsonify({
            'status': 'success',
            'tile_url': tile_url,
            'city': city,
            'image_count': count,
            'info': {
                'period': f"{start_date} to {end_date}",
                'bloom_period': f"{bloom_start} to {bloom_end}",
                'images_used': count
            }
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Error processing request'
        }), 500

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("BloomWatch Backend Server")
    print("=" * 50)
    print(f"Server: http://localhost:5000")
    print(f"Earth Engine: {'✅ Ready' if ee_initialized else '❌ Not initialized'}")
    print("\nEndpoints:")
    print("   - GET  /")
    print("   - GET  /health")
    print("   - POST /get-canola-layer")
    print("=" * 50 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')