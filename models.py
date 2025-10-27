# models.py
import os 
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus # <--- Importación clave para manejar caracteres especiales

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

# --- Inicialización de la base de datos (CORREGIDO PARA CODIFICACIÓN DE CONTRASEÑA) ---

# 1. Recuperar credenciales de las variables de entorno de Azure
SERVER = os.getenv("AZURE_SQL_SERVER")
DATABASE = os.getenv("AZURE_SQL_DATABASE")
USERNAME = os.getenv("AZURE_SQL_USER")
# **Codificamos la contraseña usando quote_plus para manejar el símbolo '$'**
PASSWORD = quote_plus(os.getenv("AZURE_SQL_PASSWORD")) 
PORT = os.getenv("AZURE_SQL_PORT", "1433")

# Driver necesario para Linux en Azure App Service
DRIVER = '{ODBC Driver 17 for SQL Server}' 

# 2. Construir la cadena de conexión optimizada para pyodbc
# La contraseña ya está codificada y se pasa directamente a la URL.
connection_string = (
    f"mssql+pyodbc://{USERNAME}:{PASSWORD}@{SERVER}:{PORT}/{DATABASE}"
    f"?driver={DRIVER}"
)

# Crear el motor de la base de datos
engine = create_engine(connection_string, echo=False)
Base.metadata.create_all(engine) # Esto creará las tablas si la conexión es exitosa

Session = sessionmaker(bind=engine)
session = Session()