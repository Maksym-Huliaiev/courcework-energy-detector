import SoapySDR
from SoapySDR import *
import numpy as np
import time
from scipy.stats import norm
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # Важливо: режим без вікна, щоб працювало на сервері
import os
import uuid
import datetime

# Try to import SoapySDR, if missing, we can fail gracefully or mock
try:
    import SoapySDR
    from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32
    SOAPY_AVAILABLE = True
except ImportError:
    SOAPY_AVAILABLE = False
    print("WARNING: SoapySDR not found. Scanner will not work.")

def scan_spectrum_web(start_freq, stop_freq):
    if not SOAPY_AVAILABLE:
        return None, None, "Error: SoapySDR library not found. Cannot access HackRF."

    try:
        # === 1. Підготовка HackRF ===
        results = SoapySDR.Device.enumerate({"driver": "hackrf"})
        if not results:
            return None, "Помилка: HackRF не знайдено! Перевірте USB-підключення."

        sdr = SoapySDR.Device(results[0])
        # Налаштування підсилення (як у вашому скрипті)
        sdr.setGain(SOAPY_SDR_RX, 0, "AMP", 14.0)
        sdr.setGain(SOAPY_SDR_RX, 0, "LNA", 40.0)
        sdr.setGain(SOAPY_SDR_RX, 0, "VGA", 40.0)
        sdr.setSampleRate(SOAPY_SDR_RX, 0, 1e6)
        
        rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
        sdr.activateStream(rx_stream)
        
        # === 2. Калібрування шуму (на 87.0 МГц) ===
        sdr.setFrequency(SOAPY_SDR_RX, 0, 87.0e6)
        time.sleep(0.3) # Пауза для стабілізації
        
        buff = np.array([0]*4096, np.complex64)
        noise_vals = []
        
        # Робимо 10 швидких замірів
        for _ in range(10):
            sdr.readStream(rx_stream, [buff], len(buff))
            e = np.sum(np.abs(buff)**2) / len(buff)
            if e > 0: noise_vals.append(e)
            
        if not noise_vals:
            avg_noise = 0.001 # Запасне значення, якщо щось пішло не так
        else:
            avg_noise = np.mean(noise_vals)
        
        # Розрахунок порогу (P_f = 0.1)
        # Формула: Threshold = Noise * (1 + Q_inv / sqrt(N))
        threshold = avg_noise * (1 + norm.ppf(1 - 0.1) / np.sqrt(4096))
        
        # === 3. Сканування діапазону ===
        freqs = []
        energies = []
        
        # Переводимо МГц у Гц
        f_start = start_freq * 1e6
        f_stop = stop_freq * 1e6
        
        # Цикл по частотах з кроком 0.1 МГц
        for freq in np.arange(f_start, f_stop, 0.1e6):
            sdr.setFrequency(SOAPY_SDR_RX, 0, freq)
            time.sleep(0.02) # Швидка пауза

            sdr.readStream(rx_stream, [buff], len(buff)) # Чистка буфера
            sr = sdr.readStream(rx_stream, [buff], len(buff)) # Замір
            
            if sr.ret > 0:
                en = np.sum(np.abs(buff)**2) / len(buff)
                freqs.append(freq/1e6) # Зберігаємо як МГц
                energies.append(en)
                
        # Закриваємо потік
        sdr.deactivateStream(rx_stream)
        sdr.closeStream(rx_stream)
        
        # === 4. Малювання графіка ===
        plt.figure(figsize=(10, 5))
        plt.plot(freqs, energies, label='Сигнал (Енергія)', color='blue', linewidth=1)
        plt.axhline(y=threshold, color='red', linestyle='--', label=f'Поріг ({threshold:.5f})')
        
        plt.title(f"Спектр: {start_freq} - {stop_freq} МГц")
        plt.xlabel("Частота (МГц)")
        plt.ylabel("Енергія")
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Створення папки для картинок, якщо її немає
        static_dir = os.path.join(os.getcwd(), 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            
        # Unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        img_filename = f'scan_{timestamp}_{unique_id}.png'
        img_path_abs = os.path.join(scans_dir, img_filename)
        
        plt.savefig(img_path_abs)
        plt.close()
        
        # Return relative path for DB/Frontend
        # static/scans/filename.png
        relative_path = f'static/scans/{img_filename}'
        
        raw_data = {
            "freqs": freqs,
            "energies": energies,
            "threshold": threshold
        }
        
        return relative_path, raw_data, None

    except Exception as e:
        return None, None, str(e)
