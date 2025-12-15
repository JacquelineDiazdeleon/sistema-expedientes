import sqlite3
import os

# Path to the SQLite database
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the list of all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Find the table for AreaTipoExpediente
area_table = None
for table in tables:
    if 'areatipoexpediente' in table[0].lower():
        area_table = table[0]
        break

if area_table:
    print(f"Found table: {area_table}")
    
    # Get all columns in the table
    cursor.execute(f"PRAGMA table_info({area_table});")
    columns = cursor.fetchall()
    print("\nColumns in the table:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # Get all areas
    cursor.execute(f"SELECT * FROM {area_table} WHERE tipo_expediente = 'licitacion'")
    areas = cursor.fetchall()
    
    if areas:
        print("\nAreas for tipo_expediente='licitacion':")
        for area in areas:
            print(f"ID: {area[0]}, Title: {area[2]}, Tipo: {area[3]}, Subtipo: {area[4]}, Activa: {area[10]}")
    else:
        print("\nNo areas found for tipo_expediente='licitacion'")
        
    # Get all areas with subtipo containing 'licitacion' or 'recurso' or 'fondo'
    cursor.execute(f"""
        SELECT * FROM {area_table} 
        WHERE tipo_expediente = 'licitacion' 
        AND (subtipo_expediente LIKE '%licitacion%' 
             OR subtipo_expediente LIKE '%recurso%' 
             OR subtipo_expediente LIKE '%fondo%')
    """)
    
    areas = cursor.fetchall()
    if areas:
        print("\nAreas with subtipo related to licitacion:")
        for area in areas:
            print(f"ID: {area[0]}, Title: {area[2]}, Tipo: {area[3]}, Subtipo: {area[4]}, Activa: {area[10]}")
    else:
        print("\nNo areas found with subtipo related to licitacion")
        
    # Get all distinct tipo_expediente and subtipo_expediente values
    cursor.execute(f"""
        SELECT tipo_expediente, subtipo_expediente, COUNT(*) as count 
        FROM {area_table} 
        GROUP BY tipo_expediente, subtipo_expediente
        ORDER BY tipo_expediente, subtipo_expediente
    """)
    
    print("\nCount of areas by tipo and subtipo:")
    for row in cursor.fetchall():
        print(f"Tipo: {row[0]}, Subtipo: {row[1] or 'None'}, Count: {row[2]}")
else:
    print("Could not find AreaTipoExpediente table in the database.")
    print("Available tables:")
    for table in tables:
        print(f"- {table[0]}")

# Close the connection
conn.close()
