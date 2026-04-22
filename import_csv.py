import csv
import sqlite3

# 1. Připojení k databázi (vytvoří se, pokud neexistuje)
conn = sqlite3.connect("ptaci.db")
cursor = conn.cursor()

# 2. Vytvoření tabulky podle zadání
cursor.execute("DROP TABLE IF EXISTS ptaci")  # Smaže starou tabulku, pokud existuje (pro čistý start)
cursor.execute("""
CREATE TABLE ptaci (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nazev TEXT,
    vedecky_nazev TEXT,
    rad TEXT,
    celed TEXT,
    delka_cm INTEGER,
    rozpeti_cm INTEGER,
    hmotnost_g INTEGER,
    status_ohrozeni TEXT,
    typ_potravy TEXT,
    migrace INTEGER,
    vyskyt_kontinent TEXT,
    snuska_ks REAL
)
""")

# 3. Načtení CSV a vložení dat
pocet_zaznamu = 0
with open("dataset_ptaci_final.csv", mode="r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cursor.execute("""
            INSERT INTO ptaci (
                nazev, vedecky_nazev, rad, celed, delka_cm, 
                rozpeti_cm, hmotnost_g, status_ohrozeni, 
                typ_potravy, migrace, vyskyt_kontinent, snuska_ks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["nazev"],
            row["vedecky_nazev"],
            row["rad"],
            row["celed"],
            int(row["delka_cm"]),
            int(row["rozpeti_cm"]),
            int(row["hmotnost_g"]),
            row["status_ohrozeni"],
            row["typ_potravy"],
            int(row["migrace"]),
            row["vyskyt_kontinent"],
            float(row["snuska_ks"])
        ))
        pocet_zaznamu += 1

# 4. Uložení a zavření
conn.commit()
conn.close()

print(f"Hotovo! Importováno bylo {pocet_zaznamu} záznamů.")