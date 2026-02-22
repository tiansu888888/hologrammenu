import sqlite3
import os
import json
from menu import MENU

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_order.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with tables and initial menu data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create menu_items table with Malay support
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id TEXT PRIMARY KEY,
            name_cn TEXT NOT NULL,
            name_en TEXT NOT NULL,
            name_ms TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            emoji TEXT NOT NULL
        )
    ''')

    # Upgrade existing table if name_ms is missing
    cursor.execute("PRAGMA table_info(menu_items)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'name_ms' not in columns:
        print("Upgrading menu_items table to include name_ms...")
        cursor.execute("ALTER TABLE menu_items ADD COLUMN name_ms TEXT DEFAULT ''")

    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL,
            items TEXT NOT NULL,
            status TEXT DEFAULT 'confirmed'
        )
    ''')

    # Check if menu_items needs populating or refreshing
    cursor.execute('SELECT COUNT(*) FROM menu_items')
    count = cursor.fetchone()[0]

    if count == 0:
        # Populate from menu.py MENU dictionary
        for category, cat_data in MENU.items():
            for item in cat_data['items']:
                cursor.execute('''
                    INSERT INTO menu_items (id, name_cn, name_en, name_ms, price, category, emoji)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (item['id'], item['name_cn'], item['name_en'], item['name_ms'], item['price'], category, item['emoji']))
    else:
        # If already exists, we might want to refresh name_ms for old entries
        for category, cat_data in MENU.items():
            for item in cat_data['items']:
                cursor.execute('''
                    UPDATE menu_items SET name_ms = ? WHERE id = ?
                ''', (item['name_ms'], item['id']))
        
    conn.commit()
    conn.close()
    print(f"Database initialized/updated at {DB_PATH}")

def get_menu_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu_items')
    rows = cursor.fetchall()
    conn.close()

    # Format back to the MENU structure with Malay support
    menu = {}
    from menu import MENU as STATIC_MENU
    
    for cat_id, cat_info in STATIC_MENU.items():
        menu[cat_id] = {
            "name_cn": cat_info["name_cn"],
            "name_en": cat_info["name_en"],
            "name_ms": cat_info["name_ms"],
            "items": []
        }

    for row in rows:
        cat = row['category']
        if cat in menu:
            menu[cat]['items'].append({
                "id": row['id'],
                "name_cn": row['name_cn'],
                "name_en": row['name_en'],
                "name_ms": row['name_ms'],
                "price": row['price'],
                "emoji": row['emoji']
            })
    
    return menu

def save_order_to_db(total, items):
    conn = get_db_connection()
    cursor = conn.cursor()
    items_json = json.dumps(items)
    cursor.execute('''
        INSERT INTO orders (total, items)
        VALUES (?, ?)
    ''', (total, items_json))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

if __name__ == "__main__":
    init_db()
