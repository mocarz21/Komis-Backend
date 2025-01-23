import asyncpg
import yaml
from contextlib import asynccontextmanager

# Wczytanie ustawień z pliku YAML
with open("settings.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# Ustawienia połączenia do bazy danych
username = config['global']['database']['username']
password = config['global']['database']['password']
address = config['global']['database']['address']
port = config['global']['database']['port']
database = config['global']['database']['database']

global_dsn = f"postgres://{username}:{password}@{address}:{port}/{database}"

class Database:
    def __init__(self):
        self.pool = None
    
    async def create_pool(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(dsn=global_dsn)
    
    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
            
    async def get_connection(self):
        return await self.pool.acquire()
    
    async def release_connection(self, connection):
        await self.pool.release(connection)

db = Database()

async def lifespan(app):
    print("Tworzenie puli połączeń...")  # Debugowanie
    await db.create_pool()  # Tworzy pulę połączeń
    app.state.pgpool = db.pool  # Przypisuje pulę połączeń do state
    print("Pula połączeń została utworzona.")
    yield
    print("Zamykanie puli połączeń...")  # Debugowanie
    await db.disconnect()  # Zamyka pulę połączeń
    print("Pula połączeń została zamknięta.")