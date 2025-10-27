# models.py
import os 
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from typing import Optional, Any

Base = declarative_base()

# --- Tabla de registros de agua ---
class RegistroAgua(Base):
    __tablename__ = 'registro_agua'
    id = Column(Integer, primary_key=True)
    cantidad_ml = Column(Float, nullable=False)
    fecha = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Agua {self.cantidad_ml}ml - {self.fecha.strftime('%d/%m %H:%M')}>"

# --- Tabla de registros de comida ---
class RegistroComida(Base):
    __tablename__ = 'registro_comida'
    id = Column(Integer, primary_key=True)
    descripcion = Column(String(200), nullable=False)
    calorias = Column(Float, nullable=False)
    fecha = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Comida {self.descripcion} - {self.calorias} cal - {self.fecha.strftime('%d/%m %H:%M')}>"

# --- Tabla de pesos mensuales ---
class RegistroPeso(Base):
    __tablename__ = 'registro_peso'
    id = Column(Integer, primary_key=True)
    mes = Column(String(20), nullable=False)  # ejemplo: "Octubre 2025"
    peso_inicio = Column(Float, nullable=False)
    peso_final = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Peso {self.mes}: inicio={self.peso_inicio}, final={self.peso_final}>"

# --- Inicialización de la base de datos (TEMPORALMENTE DESACTIVADA) ---

# 1. Recuperar credenciales de las variables de entorno de Azure
SERVER = os.getenv("AZURE_SQL_SERVER")
DATABASE = os.getenv("AZURE_SQL_DATABASE")
USERNAME = os.getenv("AZURE_SQL_USER")
# Codificamos la contraseña (se mantiene por si necesitamos reactivar el código)
PASSWORD = quote_plus(os.getenv("AZURE_SQL_PASSWORD", "")) 
PORT = os.getenv("AZURE_SQL_PORT", "1433") 

DRIVER_NAME = 'ODBC Driver 17 for SQL Server' 

# 2. Construir la URL de SQLAlchemy
connection_string = (
    f"mssql+pyodbc://{USERNAME}:{PASSWORD}@{SERVER}:{PORT}/{DATABASE}"
    f"?driver={DRIVER_NAME}"
)

# Inicializar variables que serán sobreescritas
engine: Any = None
session: Any = None

# --- Bloque try/except para saltar la conexión y cargar Flask ---
try:
    # 3. CREACIÓN DEL MOTOR Y TABLAS DESACTIVADA TEMPORALMENTE
    # engine = create_engine(connection_string, echo=False)
    # Base.metadata.create_all(engine)
    
    # Creamos una sesión DUMMY para que la aplicación Flask pueda cargar sin DB
    Session = sessionmaker() 
    session = Session()
    print("✅ SQL CONNECTION SKIPPED: App should now start and respond to webhooks.")

except Exception as e:
    # Esto ya no debería ejecutarse al inicio, pero se mantiene el bloque
    print("🛑 SQL CONNECTION FAILED AT STARTUP!")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {e}")
    
    safe_connection_string = f"mssql+pyodbc://{USERNAME}:***PASSWORD_HIDDEN***@{SERVER}:{PORT}/{DATABASE}?driver={DRIVER_NAME}"
    print(f"Failing URL (Check USERNAME, SERVER, and DATABASE): {safe_connection_string}")
    
    Session = sessionmaker() 
    session = Session()