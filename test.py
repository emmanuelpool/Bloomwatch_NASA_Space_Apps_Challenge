import ee
import sys


PROJECT_ID = 'canola-474118' 

try:
   
    ee.Initialize(project=PROJECT_ID)
    print("✅")
  

    img = ee.Image('srtm90_v4')
    info = img.getInfo()
except Exception as e:
    print("❌")
    sys.exit(1)
