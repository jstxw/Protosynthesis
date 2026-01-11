from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class MongoDB:
    """MongoDB connection handler"""
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def connect(self):
        """Establish connection to MongoDB"""
        if self._client is None:
            try:
                mongodb_uri = os.getenv('MONGODB_URI')
                db_name = os.getenv('MONGODB_DB_NAME', 'nodelink')

                if not mongodb_uri:
                    raise ValueError("MONGODB_URI not found in environment variables")

                self._client = MongoClient(mongodb_uri)
                self._db = self._client[db_name]

                # Test the connection
                self._client.server_info()
                print(f"✓ Successfully connected to MongoDB database: {db_name}")

            except Exception as e:
                print(f"✗ Failed to connect to MongoDB: {e}")
                raise

        return self._db

    def get_db(self) -> Database:
        """Get the database instance"""
        if self._db is None:
            return self.connect()
        return self._db

    def close(self):
        """Close the MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            print("✓ MongoDB connection closed")

# Singleton instance
mongodb = MongoDB()

def get_database() -> Database:
    """Helper function to get database instance"""
    return mongodb.get_db()

def get_collection(collection_name: str):
    """Helper function to get a collection"""
    db = get_database()
    return db[collection_name]
