from pymongo import MongoClient, ASCENDING, DESCENDING
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

                # Create indexes for performance
                self._create_indexes()

            except Exception as e:
                print(f"✗ Failed to connect to MongoDB: {e}")
                raise

        return self._db

    def _create_indexes(self):
        """Create database indexes for performance optimization."""
        if self._db is None:
            print("Cannot create indexes: Database not connected")
            return

        print("Creating database indexes...")

        try:
            users_collection = self._db.users

            # Index on supabase_user_id (unique, for fast user lookups)
            users_collection.create_index(
                [("supabase_user_id", ASCENDING)],
                unique=True,
                name="idx_supabase_user_id"
            )
            print("  ✓ Created index: idx_supabase_user_id")

            # Index on email (for user search/lookup)
            users_collection.create_index(
                [("email", ASCENDING)],
                unique=True,
                sparse=True,
                name="idx_email"
            )
            print("  ✓ Created index: idx_email")

            # If projects are separate collection (not embedded in users):
            if 'projects' in self._db.list_collection_names():
                projects = self._db.projects

                projects.create_index(
                    [("supabase_user_id", ASCENDING)],
                    name="idx_project_user_id"
                )
                print("  ✓ Created index: idx_project_user_id")

                projects.create_index(
                    [("created_at", DESCENDING)],
                    name="idx_created_at"
                )
                print("  ✓ Created index: idx_created_at")

            print("✓ Database indexes created successfully")

        except Exception as e:
            print(f"Warning: Error creating indexes: {e}")
            # Don't raise - app can still run without indexes (just slower)

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
