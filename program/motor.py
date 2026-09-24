# ============================================================
# MOTOR.PY
# Kontrol Motor 28BYJ-48 + ULN2003
#
# Bisa digunakan:
# - Windows -> mode simulasi
# - Raspberry Pi -> motor GPIO asli
# ============================================================

import time
import threading


# ============================================================
# CEK APAKAH BERJALAN DI RASPBERRY PI
# ============================================================

try:

    import RPi.GPIO as GPIO

    RASPBERRY_PI = True

except ImportError:

    GPIO = None

    RASPBERRY_PI = False


# ============================================================
# PIN MOTOR RASPBERRY PI
# ============================================================

IN1 = 17
IN2 = 18
IN3 = 27
IN4 = 22


MOTOR_PINS = [
    IN1,
    IN2,
    IN3,
    IN4
]


# ============================================================
# KECEPATAN MOTOR
# ============================================================

STEP_DELAY = 0.005


# ============================================================
# URUTAN MOTOR
# ============================================================

MOTOR_SEQUENCE = [

    [1, 0, 0, 0],

    [1, 1, 0, 0],

    [0, 1, 0, 0],

    [0, 1, 1, 0],

    [0, 0, 1, 0],

    [0, 0, 1, 1],

    [0, 0, 0, 1],

    [1, 0, 0, 1]

]


# ============================================================
# STATUS MOTOR
# ============================================================

motor_running = False

motor_thread = None

motor_lock = threading.Lock()


# ============================================================
# SETUP MOTOR
# ============================================================

def setup_motor():

    if not RASPBERRY_PI:

        print(
            "MOTOR: Mode simulasi Windows"
        )

        print(
            "MOTOR: GPIO asli aktif di Raspberry Pi"
        )

        return


    GPIO.setmode(
        GPIO.BCM
    )

    GPIO.setwarnings(
        False
    )


    for pin in MOTOR_PINS:

        GPIO.setup(

            pin,

            GPIO.OUT,

            initial=GPIO.LOW

        )


    print(
        "MOTOR: GPIO siap"
    )


# ============================================================
# MATIKAN COIL
# ============================================================

def matikan_coil():

    if not RASPBERRY_PI:

        return


    GPIO.output(
        IN1,
        GPIO.LOW
    )

    GPIO.output(
        IN2,
        GPIO.LOW
    )

    GPIO.output(
        IN3,
        GPIO.LOW
    )

    GPIO.output(
        IN4,
        GPIO.LOW
    )


# ============================================================
# SATU LANGKAH MOTOR
# ============================================================

def satu_langkah():

    for step in MOTOR_SEQUENCE:

        with motor_lock:

            if not motor_running:

                return


        # ----------------------------------------------------
        # Kalau Raspberry Pi
        # jalankan GPIO asli
        # ----------------------------------------------------

        if RASPBERRY_PI:

            GPIO.output(
                IN1,
                step[0]
            )

            GPIO.output(
                IN2,
                step[1]
            )

            GPIO.output(
                IN3,
                step[2]
            )

            GPIO.output(
                IN4,
                step[3]
            )


        # Delay
        time.sleep(
            STEP_DELAY
        )


# ============================================================
# LOOP MOTOR
# ============================================================

def loop_motor():

    while True:

        with motor_lock:

            status = motor_running


        if not status:

            break


        satu_langkah()


    matikan_coil()


# ============================================================
# MOTOR START
# ============================================================

def motor_start():

    global motor_running
    global motor_thread


    with motor_lock:

        if motor_running:

            return


        motor_running = True


    print(
        "MOTOR: BERPUTAR"
    )


    motor_thread = threading.Thread(

        target=loop_motor,

        daemon=True

    )


    motor_thread.start()


# ============================================================
# MOTOR STOP
# ============================================================

def motor_stop():

    global motor_running


    with motor_lock:

        if not motor_running:

            matikan_coil()

            return


        motor_running = False


    print(
        "MOTOR: BERHENTI"
    )


    if motor_thread is not None:

        if motor_thread.is_alive():

            motor_thread.join(
                timeout=1
            )


    matikan_coil()


# ============================================================
# CEK MOTOR
# ============================================================

def motor_sedang_berjalan():

    with motor_lock:

        return motor_running


# ============================================================
# CLEANUP
# ============================================================

def cleanup_motor():

    motor_stop()


    if RASPBERRY_PI:

        GPIO.cleanup()


    print(
        "MOTOR: selesai"
    )


# ============================================================
# TEST MOTOR
# ============================================================

if __name__ == "__main__":

    print(
        "===================================="
    )

    print(
        "       TEST MOTOR 28BYJ-48"
    )

    print(
        "===================================="
    )


    try:

        setup_motor()

        motor_start()


        while True:

            time.sleep(1)


    except KeyboardInterrupt:

        print()

        print(
            "Motor dihentikan."
        )


    finally:

        cleanup_motor()