import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radiosite.settings')
django.setup()

from scanner.models import ScanResult
from django.test import RequestFactory
from scanner.views import history_api

# Create dummy scan
print("Creating dummy scan result...")
scan = ScanResult.objects.create(
    start_freq=88.0,
    stop_freq=108.0,
    image_path="static/scans/test.png",
    raw_data={"test": "data"}
)
print(f"Created ScanResult ID: {scan.id}")

# Test API
factory = RequestFactory()
request = factory.get('/api/history/')
response = history_api(request)

print(f"Response Status: {response.status_code}")
content = json.loads(response.content)
print("Response Content:")
print(json.dumps(content, indent=2))

if content['status'] == 'success' and len(content['history']) > 0:
    print("VERIFICATION SUCCESS: History API returned data.")
else:
    print("VERIFICATION FAILED: Invalid response.")
