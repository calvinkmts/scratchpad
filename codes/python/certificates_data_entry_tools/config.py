from typing import Dict, List, Any

SCHEDULES_INPUT_FILE = "data_sertif_des_24_okt_25_cleaned.csv"

# Output configuration
OUTPUT_DIR: str = "out"
OUTPUT_FILE: str = "insert_programs.sql"

# Database configuration
DB_CONFIG: Dict[str, Any] = {
    "host": "localhost",
    "port": 33061,
    "user": "user",
    "password": "password",
    "database": "laravel",
}

# Category mappings
CATEGORY_IDS: Dict[str, int] = {
    "Engineering": 1,
    "Accounting": 2,
    "Construction": 3,
    "Management": 4,
    "IT": 5,
    "Communication": 6,
    "Academic": 7,
    "HR": 8,
    "Leadership": 9,
    "Forum": 10,
    "Certification": 11,
    "TestPrep": 12,
    "Webinar": 13,
    "GenZ": 14,
}
ID_TO_CATEGORY: Dict[int, str] = {v: k for k, v in CATEGORY_IDS.items()}

# List of new programs to process
NEW_PROGRAM_LIST: List[str] = [
    "Training SAP 2000: Analisa Struktur & Desain",
    "Training CMA",
    "Pelatihan PLC Modicon M221 Schneider – Tingkat Dasar",
    "Public Speaking Hacks",
    "Professional Content Creator",
    "GenZ Investasi Saham",
    "GenZ Sukses Belajar & Bekerja di Luar Negeri",
    "GenZ How to Start a Bakery Business",
    "Gen-Z Setting Up a Beauty Business",
    "Gen-Z Shopee & TikTok Live Hacks for Business",
    "Gen-Z Fashion Design for Beginner",
    "Gen-Z Creating Creative Board Games",
    "Workshop Indonesian Tax Outlook 2025",
    "Makeup Class: Ready, Set, Glow",
    "PPIC untuk PT. ECCO Tannery Indonesia",
    "Training Microsoft Excel Level Basic PT. Sadhana",
    "Training Microsoft Excel Level Advance PT. Sadhana",
    "BerdayaBareng: Bisnis UMKM Naik Kelas",
]

# Rules for categorizing programs
RULES: Dict[str, List[str]] = {
    "Construction": ["sap 2000"],
    "Engineering": ["plc"],
    "Accounting": ["cma", "tax"],
    "IT": ["excel"],
    "Communication": ["public speaking", "content creator"],
    "Management": ["bisnis", "umkm", "ppic"],
    "GenZ": ["gen-z", "genz"],
}
