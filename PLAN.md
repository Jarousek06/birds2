# Plán: Správa Ptačího Datasetu

## Přehled
Implementace uživatelské správy datasetu ptáků s možností vytvářet, upravovat a mazat záznamy. Všechny operace budou dostupné pouze přihlášeným uživatelům.

---

## Fáze 1: Autentifikace (Přihlášení a Registrace)

### Popis
Uživatelé se budou moci zaregistrovat a přihlásit do systému. Záznamy v databázi budou vázány na konkrétného uživatele.

### Workflow
1. Uživatel přejde na stránku `/register` → Vyplní formulář (jméno, email, heslo)
2. Systém ověří duplikáty → Uloží uživatele do DB s hashovaným heslem
3. Uživatel se přeloží na `/login` → Vyplní email a heslo
4. Systém ověří přihlašovací údaje → Vytvoří session/token
5. Uživatel vidí dashboard a tlačítka pro správu

### Uživatelské rozhraní
- **`/register`** — Formulář s poli: Jméno, Email, Heslo, Potvrzení hesla
  - Ověření validace emailu a síly hesla
  - Chybové hlášky pro duplikátní email/slabé heslo
  
- **`/login`** — Formulář s poli: Email, Heslo
  - Odkaz "Ještě nemám účet" → `/register`
  - Tlačítko "Přihlásit"

- **Navigation bar** — Viditelná na všech stránkách
  - Logo aplikace
  - Odkazy: Domů, Ptáci
  - Pro přihlášené: Jméno uživatele, Tlačítko "Odhlásit"

### Technické detaily
- Tabulka `users` v DB: `id, name, email, password_hash, created_at`
- Hešování hesel: `werkzeug.security`
- Session management: `Flask-Session` nebo JWT token
- Middleware pro ochranu `/manage` routes

---

## Fáze 2: Přidání Nového Záznamu

### Popis
Přihlášený uživatel bude moci přidat nový záznam ptáka do databáze přes formulář.

### Workflow
1. Uživatel klikne na tlačítko „➕ Přidat ptáka" na dashboardu
2. Přesmeruje se na stránku `/birds/add` s prázdným formulářem
3. Vyplní všechna povinná pole (stejná jako v CSV)
4. Klikne „Uložit" → Záznam se přidá do DB
5. Systém potvrdí: „Ptáka úspěšně přidáno"
6. Přesmeruje se zpět na dashboard se zobrazením nového záznamu

### Uživatelské rozhraní
- **`/birds/add`** — Formulář s poli (tabulka `ptaci`):
  - Textové vstupy: nazev, vedecky_nazev, rad, celed
  - Numerické vstupy: delka_cm, rozpeti_cm, hmotnost_g, snuska_ks
  - Selecty: status_ohrozeni, typ_potravy, vyskyt_kontinent
  - Checkbox: migrace (1 = tažný, 0 = netažný)
  - Tlačítka: "Uložit" (zelené), "Zrušit" (šedé)

- **Validace**:
  - Všechna povinná pole
  - Numerické hodnoty > 0
  - Chybové hlášky pod jednotlivými poli

### Technické detaily
- POST route `/birds/add` — Ověření přihlášení, INSERT do DB
- Generování flashi zprávy o úspěchu
- Redirect na `/` s filtrem uživatele

---

## Fáze 3: Úprava Existujícího Záznamu

### Popis
Přihlášený uživatel bude moci upravit data existujícího záznamu.

### Workflow
1. Na dashboardu se zobrazí vedle každého záznamu ikona ✏️ (Edit)
2. Kliknutí na ✏️ → Přechod na `/birds/<id>/edit`
3. Formulář se předvyplní aktuálními údaji
4. Uživatel změní potřebná pole
5. Klikne „Uložit" → Záznam se aktualizuje v DB
6. Systém potvrdí: „Ptáka úspěšně aktualizováno"
7. Přesmeruje se na dashboard

### Uživatelské rozhraní
- **`/birds/<id>/edit`** — Stejný formulář jako přidání, ale:
  - Pole jsou předvyplněná
  - Nadpis: „Úprava: [Název ptáka]"
  - Tlačítka: "Uložit změny" (zelené), "Zrušit" (šedé)

- **V tabulce na dashboardu**:
  - Sloupec s akcemi na konci
  - Ikona ✏️ (Edit) — barva: modrá
  - Ikona 🗑️ (Delete) — barva: červená

### Technické detaily
- Route `/birds/<id>/edit` — GET: načtení dat, POST: aktualizace
- Ověření vlastnictví záznamu (uživatel vs. původce)
- UPDATE query s parametrizovanými hodnotami

---

## Fáze 4: Smazání Záznamu

### Popis
Přihlášený uživatel bude moci smazat záznam z databáze s potvrzením.

### Workflow
1. Na dashboardu vedle každého záznamu ikona 🗑️ (Delete)
2. Kliknutí na 🗑️ → Modální okno s potvrzením
3. Modál: „Opravdu chcete smazat [Název ptáka]?"
4. Uživatel klikne "Smazat" → Záznam se odstraní z DB
5. Systém potvrdí: „Ptáka úspěšně smazáno"
6. Řádek zmizí z tabulky (AJAX) nebo se stránka zloaduje

### Uživatelské rozhraní
- **Modal dialog** (potvrzovací okno):
  - Nadpis: „Smazat záznamu"
  - Text: „Opravdu chcete smazat ptáka [název]? Tuto akci nelze vrátit."
  - Tlačítka: "Smazat" (červené), "Zrušit" (šedé)

- **Ikona 🗑️ v tabulce** — onclick otevře modal

### Technické detaily
- Route `/birds/<id>/delete` — DELETE request
- Ověření vlastnictví záznamu
- JavaScript pro modal dialog
- DELETE query

---

## Fáze 5: Filtrování Záznamů Uživatele

### Popis
Na dashboardu se budou zobrazovat pouze záznamy přihlášeného uživatele. Filtry zůstanou funkční.

### Workflow
1. Přihlášený uživatel vidí pouze svojí data
2. Filtry fungují stejně jako dříve (řád, hmotnost, atd.)
3. Na dashboardu se zobrazí počet vlastních záznamů

### Uživatelské rozhraní
- Žádné viditelné změny pro uživatele
- Interně: WHERE clause s `user_id = current_user_id`
- Info karta: „Váš dataset: X ptáků"

### Technické detaily
- Tabulka `ptaci` rozšířena o sloupec `user_id` (Foreign Key)
- Všechny SELECT queries filtrují podle `user_id`
- Agregace (`COUNT`, `AVG`, apod.) pouze z vlastních záznamů

---

## Fáze 6: Ochrana a Bezpečnost

### Popis
Zabezpečení správy dat před neoprávněným přístupem.

### Implementace
1. **Autentifikace** — Middleware kontrolující session
2. **Autorizace** — Ověření vlastnictví záznamu (user_id)
3. **CSRF ochrana** — Tokeny ve formulářích
4. **SQL Injection ochrana** — Parametrizované dotazy (již používáno)
5. **Rate limiting** — Omezení počtu requestů (volitelné)

### Uživatelské rozhraní
- **Přesměrování** — Neautentizovaný uživatel → `/login`
- **Chybové zprávy** — Pokus o přístup k cizímu záznamu → 403 Forbidden

---

## Databázová Schéma

### Nový sloupec v tabulce `ptaci`
```sql
ALTER TABLE ptaci ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1;
ALTER TABLE ptaci ADD FOREIGN KEY (user_id) REFERENCES users(id);
```

### Nová tabulka `users`
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Architektura Aplikace

### Struktury souborů
```
app.py
├── routes/
│   ├── auth.py (register, login, logout)
│   ├── dashboard.py (GET /birds)
│   └── birds.py (CRUD operace)
├── models/
│   ├── user.py
│   └── bird.py
├── templates/
│   ├── base.html (layout s navigation)
│   ├── auth/
│   │   ├── register.html
│   │   └── login.html
│   ├── birds/
│   │   ├── dashboard.html (seznam ptáků)
│   │   ├── add.html (přidání)
│   │   └── edit.html (úprava)
│   └── error.html
└── static/
    ├── style.css (existující)
    └── js/
        ├── modal.js (potvrzovací dialogy)
        └── delete.js (AJAX delete)
```

---

## Timeline Implementace

| Fáze | Úkol | Předpokl. čas |
|------|------|--------------|
| 1 | Autentifikace | 2-3 hodiny |
| 2 | Přidání záznamu | 1 hodina |
| 3 | Úprava záznamu | 1 hodina |
| 4 | Smazání záznamu | 1 hodina |
| 5 | Filtrování dat | 30 minut |
| 6 | Bezpečnost | 1 hodina |
| **Celkem** | | **6.5 hodin** |

---

## Prioritní Řazení

1. ✅ **Fáze 1** — Autentifikace (bez ní nelze pokračovat)
2. ✅ **Fáze 5** — Filtrování (integrátor bez toho by měl chyby)
3. ✅ **Fáze 2** — Přidání (základní funcionalita)
4. ✅ **Fáze 3** — Úprava (pokračování)
5. ✅ **Fáze 4** — Smazání (pokračování)
6. ✅ **Fáze 6** — Bezpečnost (iteruje všechny předchozí)

---

## Git Commit Strategie

Každá fáze bude mít minimálně 1 commit:

```
Fáze 1: git commit -m "Autentifikace — registrace a přihlášení"
Fáze 2: git commit -m "Správa dat — přidání nového ptáka"
Fáze 3: git commit -m "Správa dat — úprava existujícího ptáka"
Fáze 4: git commit -m "Správa dat — smazání ptáka"
Fáze 5: git commit -m "Filtrování — zobrazení pouze vlastních dat"
Fáze 6: git commit -m "Bezpečnost — ochranu dat a autorizace"
```

---

## Očekávaný Výsledek

Po dokončení všech fází bude aplikace schopna:
- Uživatel se může zaregistrovat a přihlásit
- Přihlášený uživatel vidí pouze svá data
- Přidání nového záznamu přes formulář
- Úprava existujícího záznamu
- Smazání záznamu s potvrzením
- Všechny operace jsou bezpečné a ověřené
