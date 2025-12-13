from django.shortcuts import render
from django.http import JsonResponse
from .logic import scan_spectrum_web
from .models import ScanResult
import json
import traceback

def index(request):
    return render(request, 'scanner/index.html')

def scan_api(request):
    if request.method == 'POST':
        try:
            # Отримуємо дані з форми
            start = float(request.POST.get('start'))
            stop = float(request.POST.get('stop'))
            
            # Запускаємо сканер
            image_url, raw_data, err = scan_spectrum_web(start, stop)
            
            if err:
                return JsonResponse({'status': 'error', 'message': err}, status=500)
            
            # Save to DB
            scan = ScanResult.objects.create(
                start_freq=start,
                stop_freq=stop,
                image_path=image_url,
                raw_data=raw_data
            )
            
            return JsonResponse({
                'status': 'success',
                'scan': {
                    'id': scan.id,
                    'created_at': scan.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    'image_url': scan.image_path,
                    'start': scan.start_freq,
                    'stop': scan.stop_freq
                }
            })
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Будь ласка, введіть коректні числа!'}, status=400)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def history_api(request):
    try:
        # Get last 50 scans ordered by new code
        scans = ScanResult.objects.all().order_by('-created_at')[:50]
        data = []
        for s in scans:
            data.append({
                'id': s.id,
                'created_at': s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'start': s.start_freq,
                'stop': s.stop_freq,
                'image_url': s.image_path
            })
        return JsonResponse({'status': 'success', 'history': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
