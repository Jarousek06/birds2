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
    
    # Načtení možností pro dropdowny
    filter_options = get_filter_options(conn)
    
    conn.close()
    
    return render_template(
        "dashboard.html",
        ptaci=ptaci,
        filter_options=filter_options,
        params=request.args
    )

if __name__ == "__main__":
    app.run(debug=True)
    