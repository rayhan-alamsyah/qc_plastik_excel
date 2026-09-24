# ==========================================================
# LOGIKA DETEKSI QC PLASTIC
# ==========================================================


# ==========================================================
# JENIS NG
# ==========================================================

CLASS_NG = {
    "burn_mark",
    "crack",
    "defect",
    "flash",
    "short_shot"
}


# ==========================================================
# NORMALISASI NAMA CLASS
# ==========================================================

def normalisasi_nama(nama):

    nama = str(nama)

    nama = nama.lower()

    nama = nama.strip()

    # "short shot" → "short_shot"
    nama = nama.replace(
        " ",
        "_"
    )

    # "short-shot" → "short_shot"
    nama = nama.replace(
        "-",
        "_"
    )

    return nama


# ==========================================================
# PROSES DETEKSI
# ==========================================================

def proses_deteksi(
    result,
    model
):

    daftar_deteksi = []


    # ======================================================
    # TIDAK ADA OBJEK
    # ======================================================

    if (
        result.boxes is None
        or len(result.boxes) == 0
    ):

        return (
            "NO_OBJECT",
            "-",
            daftar_deteksi
        )


    # ======================================================
    # AMBIL SEMUA DETEKSI
    # ======================================================

    for i in range(
        len(result.boxes)
    ):

        class_id = int(
            result.boxes.cls[i]
        )

        confidence = float(
            result.boxes.conf[i]
        )


        # --------------------------------------------------
        # Ambil nama class
        # --------------------------------------------------

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


        # --------------------------------------------------
        # Normalisasi
        # --------------------------------------------------

        nama = normalisasi_nama(
            nama
        )


        # --------------------------------------------------
        # Masukkan ke daftar
        # --------------------------------------------------

        daftar_deteksi.append({

            "class": nama,

            "confidence": confidence,

            "index": i

        })


    # ======================================================
    # CARI DETEKSI NG
    # ======================================================

    daftar_ng = []


    for deteksi in daftar_deteksi:

        nama = deteksi[
            "class"
        ]

        confidence = deteksi[
            "confidence"
        ]


        if nama in CLASS_NG:

            daftar_ng.append(
                deteksi
            )


    # ======================================================
    # JIKA ADA NG
    # ======================================================

    if daftar_ng:

        ng_terbaik = max(
            daftar_ng,
            key=lambda x:
                x["confidence"]
        )


        return (

            "NG",

            ng_terbaik[
                "class"
            ],

            daftar_deteksi

        )


    # ======================================================
    # ADA PRODUK TAPI TIDAK ADA NG
    # = OK
    # ======================================================

    return (

        "OK",

        "-",

        daftar_deteksi

    )