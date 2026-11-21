"""
Menjalankan server produksi menggunakan Waitress (sesuai dokumen Bab 3.1)
Penggunaan:
    python server_production.py
"""
import os
from waitress import serve
from app import create_app
from app.config import ProductionConfig

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app = create_app(ProductionConfig)
    print(f"[*] Server produksi Waitress berjalan di http://localhost:{port}")
    serve(app, host="0.0.0.0", port=port, threads=6)
