"""
Sıfır Atık YZ - Servo Motorlu Mekanik Yönlendirici Flap Kontrolü
Raspberry Pi üzerinde 50Hz PWM sinyali ile 0-180 derece arasında flap kontrolü sağlar.
RPi.GPIO bulunmayan geliştirme bilgisayarlarında simülasyon modunda çalışır.
"""

import time
import sys
import os

sys.path.append(os.path.dirname(__file__))
from actuator_controller import IS_HARDWARE_AVAILABLE, gpio_driver

SERVO_PIN = 18

def setup_servo():
    if IS_HARDWARE_AVAILABLE:
        gpio_driver.setmode(gpio_driver.BCM)
        gpio_driver.setup(SERVO_PIN, gpio_driver.OUT)
        pwm = gpio_driver.PWM(SERVO_PIN, 50) # 50Hz standard servo periyodu
        pwm.start(0)
        return pwm
    else:
        print("[ServoControl] Sanal PWM nesnesi oluşturuldu (Simülasyon Modu).")
        return None

def set_angle(pwm, angle: int):
    """
    Verilen açıyı (0 - 180 derece) duty cycle değerine dönüştürüp servoya uygular.
    0°  -> PET Haznesi
    45° -> HDPE Haznesi
    90° -> Naylon Haznesi
    135°-> PUR Haznesi
    180°-> Metal Haznesi
    """
    duty = angle / 18.0 + 2.0
    print(f"[ServoControl] Açı: {angle}° -> Duty Cycle: {duty:.2f}%")
    if pwm is not None:
        gpio_driver.output(SERVO_PIN, True)
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.4)
        gpio_driver.output(SERVO_PIN, False)
        pwm.ChangeDutyCycle(0)
    else:
        time.sleep(0.2)

def main():
    print("Servo Motor Flap Yönlendirme Testi Başlatılıyor...")
    pwm = setup_servo()
    try:
        positions = [
            (0, "PET Haznesi"),
            (45, "HDPE Haznesi"),
            (90, "Naylon Haznesi"),
            (135, "PUR Haznesi"),
            (180, "Metal Haznesi")
        ]

        for angle, desc in positions:
            print(f">>> Yönlendiriliyor: {desc} ({angle} derece)")
            set_angle(pwm, angle)
            time.sleep(1.0)

        print("Test başarıyla tamamlandı. Flap nötr (0°) konumuna alınıyor.")
        set_angle(pwm, 0)

    except KeyboardInterrupt:
        print("Kullanıcı tarafından durduruldu.")
    finally:
        if pwm is not None:
            pwm.stop()
        gpio_driver.cleanup()
        print("GPIO ve Servo temizlendi.")

if __name__ == "__main__":
    main()
