# models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os # Necesario para leer las variables de entorno

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

# --- Inicialización de la base de datos para Azure SQL ---
# Carga las credenciales desde las variables de entorno (Azure App Service Configuration)
db_user = os.getenv('AZURE_SQL_USER', 'waterbot-server-admin')
db_pass = os.getenv('AZURE_SQL_PASSWORD', 'KOKv54$hOz4$l2rW')
db_server = os.getenv('AZURE_SQL_SERVER', 'waterbot-server.database.windows.net')
db_port = os.getenv('AZURE_SQL_PORT', '1433')
db_name = os.getenv('AZURE_SQL_DATABASE', 'waterbot-database')

# Cadena de conexión usando el driver mssql+pyodbc.
# IMPORTANTE: El driver 'ODBC Driver 17 for SQL Server' debe estar disponible en el entorno de Azure.
DATABASE_URL = (
    f"mssql+pyodbc://{db_user}:{db_pass}@{db_server}:"
    f"{db_port}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server"
)

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL, echo=False)
# Crea las tablas en Azure SQL si no existen
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()