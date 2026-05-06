from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

# Povolené sloupce pro řazení (bezpečnost proti SQL injection)
ALLOWED_SORT_COLUMNS = {
    "nazev", "vedecky_nazev", "rad", "celed",
    "delka_cm", "rozpeti_cm", "hmotnost_g",
    "status_ohrozeni", "typ_potravy", "migrace",
    "vyskyt_kontinent", "snuska_ks",
}

def get_db():
    """Otevře spojení na databázi a nastaví row_factory pro přístup podle názvu sloupce."""
    conn = sqlite3.connect("ptaci.db")
    conn.row_factory = sqlite3.Row
    return conn

def build_query(params):
    """Sestaví WHERE klauzuli a seznam hodnot z parametrů.
    
    Parametry:
    - rad, typ_potravy, vyskyt_kontinent, status_ohrozeni: textové filtry
    - migrace: 0 nebo 1 (nebo prázdný string)
    - hmotnost_min, hmotnost_max: numerické filtry
    
    Vrací: (where_clause, values)
    """
    conditions = []
    values = []
    
    # Textové filtry
    for key, column in [
        ("rad", "rad"),
        ("typ_potravy", "typ_potravy"),
        ("kontinent", "vyskyt_kontinent"),
        ("status", "status_ohrozeni"),
    ]:
        if params.get(key):
            conditions.append(f"{column} = ?")
            values.append(params.get(key))
    
    # Migrace
    if params.get("migrace") in ["0", "1"]:
        conditions.append("migrace = ?")
        values.append(int(params.get("migrace")))
    
    # Hmotnost
    if params.get("hmotnost_min"):
        try:
            conditions.append("hmotnost_g >= ?")
            values.append(int(params.get("hmotnost_min")))
        except ValueError:
            pass
    
    if params.get("hmotnost_max"):
        try:
            conditions.append("hmotnost_g <= ?")
            values.append(int(params.get("hmotnost_max")))
        except ValueError:
            pass
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, values

def get_filter_options(conn):
    """Načte unikátní hodnoty pro dropdowny z databáze."""
    cursor = conn.cursor()
    
    options = {}
    
    # Načtení DISTINCT hodnot pro každý filtr
    cursor.execute("SELECT DISTINCT rad FROM ptaci WHERE rad IS NOT NULL ORDER BY rad")
    options["rady"] = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT typ_potravy FROM ptaci WHERE typ_potravy IS NOT NULL ORDER BY typ_potravy")
    options["potravy"] = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT vyskyt_kontinent FROM ptaci WHERE vyskyt_kontinent IS NOT NULL ORDER BY vyskyt_kontinent")
    options["kontinenty"] = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT status_ohrozeni FROM ptaci WHERE status_ohrozeni IS NOT NULL ORDER BY status_ohrozeni")
    options["statusy"] = [row[0] for row in cursor.fetchall()]
    
    return options

def get_sort_params(params):
    """Validuje a vrací bezpečné parametry řazení.
    
    Parametry:
    - razeni: sloupec pro řazení (kontrola proti ALLOWED_SORT_COLUMNS)
    - smer: ASC nebo DESC
    
    Vrací: (razeni, smer)
    """
    razeni = params.get("razeni", "nazev").lower()
    if razeni not in ALLOWED_SORT_COLUMNS:
        razeni = "nazev"
    
    smer = params.get("smer", "ASC").upper()
    if smer not in ["ASC", "DESC"]:
        smer = "ASC"
    
    return razeni, smer

@app.route("/")
def dashboard():
    """Načte ptáky z databáze podle filtrů a řazení a zobrazí je v dashboardu."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Sestavení WHERE klauzule ze GET parametrů
    where_clause, values = build_query(request.args)
    
    # Validace a získání parametrů řazení
    razeni, smer = get_sort_params(request.args)
    
    # Hlavní dotaz s filtry a řazením
    query = f"SELECT * FROM ptaci WHERE {where_clause} ORDER BY {razeni} {smer}"
    cursor.execute(query, values)
    ptaci = cursor.fetchall()
    
    # Agregační dotaz pro statistiky
    stats_query = f"""
    SELECT
        COUNT(*) as pocet,
        ROUND(AVG(delka_cm), 1) as prum_delka,
        MAX(hmotnost_g) as max_hmotnost,
        MIN(hmotnost_g) as min_hmotnost,
        ROUND(AVG(hmotnost_g), 1) as prum_hmotnost,
        ROUND(AVG(rozpeti_cm), 1) as prum_rozpeti
    FROM ptaci WHERE {where_clause}
    """
    cursor.execute(stats_query, values)
    stats = dict(cursor.fetchone())
    
    # Grafy — agregační dotazy s GROUP BY
    # 1. Počet druhů podle řádu
    graf_rad_query = f"SELECT rad, COUNT(*) as pocet FROM ptaci WHERE {where_clause} GROUP BY rad ORDER BY pocet DESC"
    cursor.execute(graf_rad_query, values)
    druhy_rad = cursor.fetchall()
    graf_rad_labels = [r["rad"] for r in druhy_rad]
    graf_rad_data = [r["pocet"] for r in druhy_rad]
    
    # 2. Průměrná hmotnost podle typu potravy
    graf_potrava_query = f"SELECT typ_potravy, ROUND(AVG(hmotnost_g), 0) as prum FROM ptaci WHERE {where_clause} GROUP BY typ_potravy ORDER BY prum DESC"
    cursor.execute(graf_potrava_query, values)
    hmotnost_potrava = cursor.fetchall()
    graf_potrava_labels = [r["typ_potravy"] for r in hmotnost_potrava]
    graf_potrava_data = [r["prum"] for r in hmotnost_potrava]
    
    # 3. Tažní vs. netažní
    graf_migrace_query = f"SELECT migrace, COUNT(*) as pocet FROM ptaci WHERE {where_clause} GROUP BY migrace"
    cursor.execute(graf_migrace_query, values)
    druhy_migrace = cursor.fetchall()
    graf_migrace_labels = ["Tažní" if r["migrace"] == 1 else "Netažní" for r in druhy_migrace]
    graf_migrace_data = [r["pocet"] for r in druhy_migrace]
    
    # 4. Počet druhů podle kontinentu
    graf_kontinent_query = f"SELECT vyskyt_kontinent, COUNT(*) as pocet FROM ptaci WHERE {where_clause} GROUP BY vyskyt_kontinent ORDER BY pocet DESC"
    cursor.execute(graf_kontinent_query, values)
    druhy_kontinent = cursor.fetchall()
    graf_kontinent_labels = [r["vyskyt_kontinent"] for r in druhy_kontinent]
    graf_kontinent_data = [r["pocet"] for r in druhy_kontinent]
    
    # Načtení možností pro dropdowny
    filter_options = get_filter_options(conn)
    
    conn.close()
    
    return render_template(
        "dashboard.html",
        ptaci=ptaci,
        filter_options=filter_options,
        params=request.args,
        stats=stats,
        graf_rad_labels=graf_rad_labels,
        graf_rad_data=graf_rad_data,
        graf_potrava_labels=graf_potrava_labels,
        graf_potrava_data=graf_potrava_data,
        graf_migrace_labels=graf_migrace_labels,
        graf_migrace_data=graf_migrace_data,
        graf_kontinent_labels=graf_kontinent_labels,
        graf_kontinent_data=graf_kontinent_data
    )

if __name__ == "__main__":
    app.run(debug=True)
    