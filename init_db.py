import sqlite3

# Inicializace databáze s tabulkou users
conn = sqlite3.connect("ptaci.db")
cursor = conn.cursor()

# Vytvoření tabulky users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Přidání sloupce user_id do tabulky ptaci (pokud neexistuje)
cursor.execute("PRAGMA table_info(ptaci)")
columns = [col[1] for col in cursor.fetchall()]

if 'user_id' not in columns:
    cursor.execute("ALTER TABLE ptaci ADD COLUMN user_id INTEGER DEFAULT 1")
    print("✓ Sloupec user_id přidán do tabulky ptaci")
else:
    print("✓ Sloupec user_id již existuje")

# Vytvoření defaultního uživatele (admin)
cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'admin@birds.local'")
if cursor.fetchone()[0] == 0:
    from werkzeug.security import generate_password_hash
    admin_hash = generate_password_hash("admin123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Admin", "admin@birds.local", admin_hash)
    )
    print("✓ Vytvořen admin účet (email: admin@birds.local, heslo: admin123)")

conn.commit()
conn.close()

print("✓ Databáze inicializována!")
