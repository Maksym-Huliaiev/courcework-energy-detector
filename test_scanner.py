import SoapySDR
from SoapySDR import *
import numpy as np
import time
from scipy.stats import norm 
import matplotlib.pyplot as plt 

# функція розрахунку порогу (рівняння 6)
def calculate_threshold(noise_power, N, P_f):
    Q_inv = norm.ppf(1 - P_f)
    return noise_power * (1 + Q_inv / np.sqrt(N))

def scan_spectrum():
    try:
        # підключення
        results = SoapySDR.Device.enumerate({"driver": "hackrf"})
        if not results:
            print("[ERROR] HackRF не знайдено!")
            return

        sdr = SoapySDR.Device(results[0])
        
        # налаштування (максимум для підвалу)
        sdr.setGain(SOAPY_SDR_RX, 0, "AMP", 14.0)
        sdr.setGain(SOAPY_SDR_RX, 0, "LNA", 40.0)
        sdr.setGain(SOAPY_SDR_RX, 0, "VGA", 40.0)
        sdr.setSampleRate(SOAPY_SDR_RX, 0, 1e6) 
        
        rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
        sdr.activateStream(rx_stream)
        
        # калібрування
        print("\nкалібрування шуму (на 87.0 МГц)...")
        sdr.setFrequency(SOAPY_SDR_RX, 0, 87.0e6)
        time.sleep(0.5)
        
        noise_vals = []
        buff = np.array([0]*4096, np.complex64)
        
        for _ in range(20):
            sdr.readStream(rx_stream, [buff], len(buff))
            e = np.sum(np.abs(buff)**2) / len(buff)
            if e > 0: noise_vals.append(e)
            
        avg_noise = np.mean(noise_vals)
        
        # розрахунок порогу
        P_f = 0.1 
        threshold = calculate_threshold(avg_noise, 4096, P_f)
        
        print(f"шум: {avg_noise:.5f} | поріг: {threshold:.5f}")
        print("-" * 40)
        
        # сканування
        print("сканування частот (88-108 МГц)...")
        
        freqs_mhz = []
        energies = []
        found_signals = []

        for freq in np.arange(88.0e6, 108.0e6, 0.1e6):
            sdr.setFrequency(SOAPY_SDR_RX, 0, freq)
            time.sleep(0.1) # пауза для стабільності

            sdr.readStream(rx_stream, [buff], len(buff)) # очистка
            sr = sdr.readStream(rx_stream, [buff], len(buff)) # дані

            if sr.ret > 0:
                energy = np.sum(np.abs(buff)**2) / len(buff)
                
                # зберігаємо все для графіка
                if energy > 0.000001:
                    freqs_mhz.append(freq / 1e6)
                    energies.append(energy)

                # виводимо в консоль тільки те, що вище порогу
                if energy > threshold:
                    print(f"{freq/1e6:<10.1f} | {energy:.5f}")
                    found_signals.append((freq, energy))

        sdr.deactivateStream(rx_stream)
        sdr.closeStream(rx_stream)

        # малювання графіка
        print("\nмалюю графік...")
        plt.figure(figsize=(12, 6))
        
        plt.plot(freqs_mhz, energies, label='сигнал', color='blue', linewidth=1)
        plt.axhline(y=threshold, color='red', linestyle='--', label=f'поріг ({threshold:.4f})')
        
        plt.title('результат сканування (energy detection)')
        plt.xlabel('частота (МГц)')
        plt.ylabel('енергія')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig('scan_result.png')
        print("[OK] графік збережено у файл: scan_result.png")

        # топ-5 сигналів
        print("\n" + "-"*30)
        print(" топ-5 сигналів")
        found_signals.sort(key=lambda x: x[1], reverse=True)
        for i in range(min(5, len(found_signals))):
            f, e = found_signals[i]
            print(f"#{i+1}: {f/1e6:.1f} МГц | {e:.5f}")

    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    scan_spectrum()