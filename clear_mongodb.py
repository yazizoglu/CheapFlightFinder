"""
MongoDB veritabanlarını temizlemek için kullanılan script.
"""
import os
import logging
import pymongo
from dotenv import load_dotenv

# Yapılandırma dosyasını yükle
load_dotenv()

# Logger ayarla
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("clear_mongodb")

# MongoDB bağlantı bilgileri
MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("MONGODB_DB_NAME", "flight_tracker")

def clear_collections():
    """MongoDB koleksiyonlarını temizler."""
    try:
        # MongoDB'ye bağlan
        client = pymongo.MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        
        # Uçuş fiyat verilerini temizle
        result = db.flight_prices.delete_many({})
        logger.info(f"Deleted {result.deleted_count} flight price records")
        
        # Uçuş kombinasyon verilerini temizle
        result = db.flight_combinations.delete_many({})
        logger.info(f"Deleted {result.deleted_count} flight combination records")
        
        # Alarm verilerini temizle
        result = db.alerts.delete_many({})
        logger.info(f"Deleted {result.deleted_count} alert records")
        
        # Bağlantıyı kapat
        client.close()
        logger.info("MongoDB collections cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error clearing MongoDB collections: {e}")
        return False

if __name__ == "__main__":
    clear_collections()