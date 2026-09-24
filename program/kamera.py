```python
# ============================================================
# KAMERA.PY
# SISTEM QC PLASTIC
# YOLO best.pt + KAMERA + MOTOR + EXCEL
# ============================================================

import cv2
import os
import time
from datetime import datetime

from ultralytics import YOLO

from motor import (
    setup_motor,
    motor_start,
    motor_stop,
    cleanup_motor
)

from db_exel import (
    simpan_data
)


# ============================================================
# 1. PENGATURAN PROJECT
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# 2. MODEL YOLO
# ============================================================

MODEL_PATH = os.path.join(
    BASE_DIR,
    "best.pt"
)


# ============================================================
# 3. FOLDER FOTO NG
# ============================================================

FOTO_NG_DIR = os.path.join(
    BASE_DIR,
    "foto_ng"
)


# ============================================================
# 4. PENGATURAN KAMERA
# ============================================================

# Kamera USB external
KAMERA_EXTERNAL = 1

# Kamera laptop
KAMERA_LAPTOP = 0

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


# ============================================================
# 5. PENGATURAN YOLO
# ============================================================

# Ukuran input YOLO
YOLO_SIZE = 640

# Confidence minimum
CONFIDENCE = 0.20


# ============================================================
# 6. JEDA FOTO
# ============================================================

JEDA_FOTO = 2.0


# ============================================================
# 7. CLASS YANG DIANGGAP NG
#
# SESUAIKAN DENGAN CLASS DI best.pt
# ============================================================

CLASS_NG = {
    "burn_mark",
    "crack",
    "defect",
    "flash",
    "short_shot"
}


# ============================================================
# 8. NORMALISASI NAMA CLASS
# ============================================================

def normalisasi_nama(nama):

    nama = str(nama)

    nama = nama.lower()

    nama = nama.strip()

    # Contoh:
    # "short shot" -> "short_shot"
    nama = nama.replace(
        " ",
        "_"
    )

    # Contoh:
    # "short-shot" -> "short_shot"
    nama = nama.replace(
        "-",
        "_"
    )

    return nama


# ============================================================
# 9. PROSES HASIL DETEKSI YOLO
# ============================================================

def proses_deteksi(
    result,
    model
):

    # --------------------------------------------------------
    # Tidak ada bounding box
    # --------------------------------------------------------

    if result.boxes is None:

        return (
            "NO_OBJECT",
            "-",
            []
        )


    # --------------------------------------------------------
    # Bounding box kosong
    # --------------------------------------------------------

    if len(result.boxes) == 0:

        return (
            "NO_OBJECT",
            "-",
            []
        )


    # --------------------------------------------------------
    # Semua hasil deteksi
    # --------------------------------------------------------

    daftar_deteksi = []


    for i in range(
        len(result.boxes)
    ):

        # ----------------------------------------------------
        # ID CLASS
        # ----------------------------------------------------

        class_id = int(
            result.boxes.cls[i]
        )


        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        confidence = float(
            result.boxes.conf[i]
        )


        # ----------------------------------------------------
        # NAMA CLASS
        # ----------------------------------------------------

        if isinstance(
            model.names,
            dict
        ):

            nama = model.names.get(
                class_id,
                "unknown"
            )

        else:

            nama = model.names[
                class_id
            ]


        # ----------------------------------------------------
        # NORMALISASI
        # ----------------------------------------------------

        nama = normalisasi_nama(
            nama
        )


        # ----------------------------------------------------
        # SIMPAN HASIL
        # ----------------------------------------------------

        daftar_deteksi.append({

            "class": nama,

            "confidence": confidence,

            "index": i

        })


    # ========================================================
    # CARI CLASS NG
    # ========================================================

    daftar_ng = []


    for deteksi in daftar_deteksi:

        if deteksi["class"] in CLASS_NG:

            daftar_ng.append(
                deteksi
            )


    # ========================================================
    # JIKA ADA NG
    # ========================================================

    if daftar_ng:

        # Ambil NG dengan confidence terbesar

        ng_terbaik = max(

            daftar_ng,

            key=lambda x:
            x["confidence"]

        )


        return (

            "NG",

            ng_terbaik["class"],

            daftar_deteksi

        )


    # ========================================================
    # ADA OBJEK TAPI BUKAN NG
    # ========================================================

    return (

        "OK",

        "-",

        daftar_deteksi

    )


# ============================================================
# 10. BUAT NAMA FOTO
# ============================================================

def buat_nama_foto(
    jenis_ng
):

    waktu = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return (
        f"{jenis_ng}_{waktu}.jpg"
    )


# ============================================================
# 11. SIMPAN FOTO NG
# ============================================================

def simpan_foto_ng(
    result,
    jenis_ng
):

    # --------------------------------------------------------
    # Folder berdasarkan jenis NG
    # --------------------------------------------------------

    folder_ng = os.path.join(

        FOTO_NG_DIR,

        jenis_ng

    )


    # --------------------------------------------------------
    # Buat folder
    # --------------------------------------------------------

    os.makedirs(

        folder_ng,

        exist_ok=True

    )


    # --------------------------------------------------------
    # Nama foto
    # --------------------------------------------------------

    nama_foto = buat_nama_foto(
        jenis_ng
    )


    # --------------------------------------------------------
    # Path foto
    # --------------------------------------------------------

    path_foto = os.path.join(

        folder_ng,

        nama_foto

    )


    # --------------------------------------------------------
    # Ambil gambar dengan bounding box
    # --------------------------------------------------------

    gambar = result.plot()


    # --------------------------------------------------------
    # Simpan
    # --------------------------------------------------------

    berhasil = cv2.imwrite(

        path_foto,

        gambar

    )


    if berhasil:

        print()
        print(
            "======================================"
        )

        print(
            "FOTO NG DISIMPAN"
        )

        print(
            path_foto
        )

        print(
            "======================================"
        )

        return (
            nama_foto,
            path_foto
        )


    print(
        "GAGAL MENYIMPAN FOTO NG"
    )


    return (
        None,
        None
    )


# ============================================================
# 12. TAMPILKAN INFORMASI DETEKSI
# ============================================================

def tampilkan_info_deteksi(
    frame,
    daftar_deteksi
):

    posisi_y = 120

    for deteksi in daftar_deteksi:

        nama = deteksi["class"]

        confidence = deteksi["confidence"]

        teks = (
            f"{nama} : "
            f"{confidence:.2f}"
        )

        cv2.putText(

            frame,

            teks,

            (20, posisi_y),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.6,

            (255, 255, 255),

            2

        )

        posisi_y += 30


# ============================================================
# 13. BUKA KAMERA
# ============================================================

def buka_kamera():

    # --------------------------------------------------------
    # Buat folder foto NG
    # --------------------------------------------------------

    os.makedirs(

        FOTO_NG_DIR,

        exist_ok=True

    )


    # --------------------------------------------------------
    # SETUP MOTOR
    # --------------------------------------------------------

    setup_motor()


    # ========================================================
    # LOAD MODEL
    # ========================================================

    print()
    print(
        "======================================"
    )

    print(
        "           QC PLASTIC"
    )

    print(
        "======================================"
    )

    print(
        "Memuat model YOLO..."
    )

    print(
        "Model:",
        MODEL_PATH
    )


    try:

        model = YOLO(
            MODEL_PATH
        )


    except Exception as e:

        print()
        print(
            "GAGAL MEMUAT MODEL YOLO"
        )

        print(
            e
        )

        cleanup_motor()

        return


    print(
        "Model berhasil dimuat."
    )

    print(
        "Class model:",
        model.names
    )


    # ========================================================
    # BUKA KAMERA EXTERNAL
    # ========================================================

    print()
    print(
        "Mencoba kamera external..."
    )


    cap = cv2.VideoCapture(

        KAMERA_EXTERNAL

    )


    # --------------------------------------------------------
    # Jika kamera external gagal
    # --------------------------------------------------------

    if not cap.isOpened():

        print(
            "Kamera external gagal."
        )

        print(
            "Mencoba kamera laptop..."
        )


        cap = cv2.VideoCapture(

            KAMERA_LAPTOP

        )


    # --------------------------------------------------------
    # Jika semua kamera gagal
    # --------------------------------------------------------

    if not cap.isOpened():

        print()
        print(
            "KAMERA TIDAK DAPAT DIBUKA"
        )

        cleanup_motor()

        return


    # ========================================================
    # SET RESOLUSI
    # ========================================================

    cap.set(

        cv2.CAP_PROP_FRAME_WIDTH,

        CAMERA_WIDTH

    )


    cap.set(

        cv2.CAP_PROP_FRAME_HEIGHT,

        CAMERA_HEIGHT

    )


    print()
    print(
        "Kamera berhasil dibuka."
    )

    print(
        "Tekan Q untuk keluar."
    )


    # ========================================================
    # STATUS PROGRAM
    # ========================================================

    # Mencegah satu produk NG
    # disimpan berkali-kali.

    produk_sudah_dicatat = False


    # Waktu foto terakhir

    waktu_foto_terakhir = 0


    # ========================================================
    # LOOP KAMERA
    # ========================================================

    try:

        while True:

            # ------------------------------------------------
            # BACA FRAME
            # ------------------------------------------------

            berhasil, frame = cap.read()


            if not berhasil:

                print(
                    "Gagal membaca kamera."
                )

                break


            # =================================================
            # YOLO
            # =================================================

            results = model.predict(

                source=frame,

                imgsz=YOLO_SIZE,

                conf=CONFIDENCE,

                verbose=False

            )


            # ------------------------------------------------
            # HASIL PERTAMA
            # ------------------------------------------------

            result = results[0]


            # =================================================
            # PROSES DETEKSI
            # =================================================

            (
                status,
                jenis_ng,
                daftar_deteksi

            ) = proses_deteksi(

                result,

                model

            )


            # =================================================
            # TIDAK ADA BARANG
            # =================================================

            if status == "NO_OBJECT":

                # Motor berhenti

                motor_stop()


                # Reset produk

                produk_sudah_dicatat = False


            # =================================================
            # PRODUK NG
            # =================================================

            elif status == "NG":

                # ------------------------------------------------
                # MOTOR BERHENTI
                # ------------------------------------------------

                motor_stop()


                # ------------------------------------------------
                # SIMPAN FOTO
                # ------------------------------------------------

                sekarang = time.time()


                if (

                    not produk_sudah_dicatat

                    and

                    sekarang -
                    waktu_foto_terakhir
                    >= JEDA_FOTO

                ):

                    (
                        nama_foto,
                        path_foto

                    ) = simpan_foto_ng(

                        result,

                        jenis_ng

                    )


                    # ------------------------------------------------
                    # SIMPAN KE EXCEL
                    # ------------------------------------------------

                    if path_foto is not None:

                        try:

                            simpan_data(

                                status="NG",

                                jenis_ng=jenis_ng,

                                foto=path_foto

                            )


                            print(
                                "DATA NG BERHASIL "
                                "DISIMPAN KE EXCEL"
                            )


                        except Exception as e:

                            print()

                            print(
                                "GAGAL MENYIMPAN "
                                "DATA KE EXCEL:"
                            )

                            print(
                                e
                            )


                    # ------------------------------------------------
                    # Tandai produk
                    # ------------------------------------------------

                    produk_sudah_dicatat = True


                    waktu_foto_terakhir = (
                        sekarang
                    )


            # =================================================
            # PRODUK OK
            # =================================================

            elif status == "OK":

                # ------------------------------------------------
                # MOTOR BERPUTAR
                # ------------------------------------------------

                motor_start()


            # =================================================
            # GAMBAR BOUNDING BOX
            # =================================================

            frame_hasil = result.plot()


            # =================================================
            # STATUS QC
            # =================================================

            if status == "NG":

                teks_status = (
                    f"NG : {jenis_ng}"
                )

                warna = (
                    0,
                    0,
                    255
                )


            elif status == "OK":

                teks_status = "OK"

                warna = (
                    0,
                    255,
                    0
                )


            else:

                teks_status = (
                    "TIDAK ADA BARANG"
                )

                warna = (
                    255,
                    255,
                    0
                )


            # =================================================
            # TULIS STATUS
            # =================================================

            cv2.putText(

                frame_hasil,

                teks_status,

                (20, 40),

                cv2.FONT_HERSHEY_SIMPLEX,

                1,

                warna,

                2

            )


            # =================================================
            # STATUS MOTOR
            # =================================================

            if status == "OK":

                teks_motor = (
                    "MOTOR : BERPUTAR"
                )

            else:

                teks_motor = (
                    "MOTOR : BERHENTI"
                )


            cv2.putText(

                frame_hasil,

                teks_motor,

                (20, 80),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                warna,

                2

            )


            # =================================================
            # INFORMASI CLASS + CONFIDENCE
            # =================================================

            tampilkan_info_deteksi(

                frame_hasil,

                daftar_deteksi

            )


            # =================================================
            # TAMPILKAN KAMERA
            # =================================================

            cv2.imshow(

                "QC PLASTIC",

                frame_hasil

            )


            # =================================================
            # TEKAN Q
            # =================================================

            tombol = cv2.waitKey(
                1
            ) & 0xFF


            if tombol == ord("q"):

                break


    # ========================================================
    # ERROR
    # ========================================================

    except Exception as e:

        print()

        print(
            "======================================"
        )

        print(
            "ERROR PADA KAMERA"
        )

        print(
            "======================================"
        )

        print(
            e
        )


    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        print()
        print(
            "Menutup kamera..."
        )


        # ----------------------------------------------------
        # MOTOR STOP
        # ----------------------------------------------------

        motor_stop()


        # ----------------------------------------------------
        # TUTUP KAMERA
        # ----------------------------------------------------

        cap.release()


        # ----------------------------------------------------
        # TUTUP WINDOW
        # ----------------------------------------------------

        cv2.destroyAllWindows()


        # ----------------------------------------------------
        # CLEANUP GPIO
        # ----------------------------------------------------

        cleanup_motor()


        print(
            "Program selesai."
        )


# ============================================================
# 14. PROGRAM UTAMA
# ============================================================

if __name__ == "__main__":

    buka_kamera()
```

### Yang perlu diperhatikan

Kode di atas **benar-benar menggunakan `best.pt`**, dengan lokasi:

```text
BASE_DIR/
└── best.pt
```

Bagian ini yang memuat model:

```python
MODEL_PATH = os.path.join(
    BASE_DIR,
    "best.pt"
)

model = YOLO(MODEL_PATH)
```

Pada kode Anda sebelumnya juga sudah menggunakan struktur yang sama.

Untuk menjalankan:

```bash
python kamera.py
```

atau kalau program utama Anda adalah `app.py`:

```bash
python app.py
```

**Penting:** `CLASS_NG` harus sesuai dengan nama class yang ada di `best.pt`. Program akan menampilkan nama class saat mulai:

```text
Model berhasil dimuat.
Class model: { ... }
```

Kalau `best.pt` Anda sebenarnya dilatih khusus untuk **spakbor/objek melengkung dengan ukuran tinggi dan panjang**, maka kode di atas masih memakai logika **class OK/NG**, belum menghitung **batas tinggi dan batas panjang spakbor**. Kalau itu yang Anda maksud, saya bisa buatkan versi berikutnya yang langsung memakai **bounding box `best.pt` + batas tinggi + batas panjang yang variabelnya bisa diedit di bagian atas**.
