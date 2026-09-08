import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port="5433",
        database="rentas_db",
        user="postgres",
        password="postgres"
    )
    print("✅ ¡Conexión exitosa con usuario rentas!")
    conn.close()
except psycopg2.OperationalError as e:
    print(f"❌ Error: {e}")
    print("\n🔧 Posibles soluciones:")
    print("1. Verifica que la contraseña sea correcta")
    print("2. Verifica que la base de datos 'rentas_db' exista")
    print("3. Verifica que el usuario 'rentas' tenga permisos")
    print("4. Verifica que PostgreSQL esté corriendo en el puerto 5433")
except Exception as e:
    print(f"❌ Error inesperado: {e}")