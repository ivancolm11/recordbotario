# models.py
import os 
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

# --- Inicialización de la base de datos (CORREGIDO PARA AZURE SQL) ---

# 1. Recuperar credenciales de las variables de entorno de Azure
SERVER = os.getenv("AZURE_SQL_SERVER")
DATABASE = os.getenv("AZURE_SQL_DATABASE")
USERNAME = os.getenv("AZURE_SQL_USER")
PASSWORD = os.getenv("AZURE_SQL_PASSWORD")

# Driver necesario para Linux en Azure
DRIVER = '{ODBC Driver 17 for SQL Server}' 

# 2. Construir la cadena de conexión para SQLAlchemy + pyodbc
# Nota: La sintaxis de SQLAlchemy para pyodbc requiere que la cadena de conexión se pase como parámetro a la URL.
connection_string = f"DRIVER={DRIVER};SERVER=tcp:{SERVER},1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"

# URL final de SQLAlchemy
AZURE_SQL_URL = f"mssql+pyodbc:///?odbc_connect={connection_string}"

# Usar el nuevo motor de Azure SQL
engine = create_engine(AZURE_SQL_URL, echo=False)
Base.metadata.create_all(engine) # Esto CREARÁ tus tablas en Azure SQL si no existen

Session = sessionmaker(bind=engine)
session = Session()