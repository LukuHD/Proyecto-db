import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """Establece y retorna la conexión a la base de datos 'hospital' (RT-04)"""
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            database='hospital',
            user='root',
            password='LuisAng1!' 
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None