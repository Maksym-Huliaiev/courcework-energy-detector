from django.shortcuts import render
from .logic import scan_spectrum_web

def index(request):
    image_url = None
    error = None
    
    if request.method == 'POST':
        try:
            # Отримуємо дані з форми
            start = float(request.POST.get('start'))
            stop = float(request.POST.get('stop'))
            
            # Запускаємо сканер
            img_path, err = scan_spectrum_web(start, stop)
            
            if err:
                error = err
            else:
                image_url = img_path
        except ValueError:
            error = "Будь ласка, введіть коректні числа!"
        except Exception as e:
            error = str(e)

    return render(request, 'scanner/index.html', {'image_url': image_url, 'error': error})
