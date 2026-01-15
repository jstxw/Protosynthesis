"""
Database Management Script
Utility for managing MongoDB indexes and database operations.
"""

from database import mongodb
import sys


def create_indexes():
    """Create all database indexes"""
    try:
        mongodb.connect()
        print("\n✓ Indexes created successfully\n")
    except Exception as e:
        print(f"\n✗ Error creating indexes: {e}\n")
        sys.exit(1)


def verify_indexes():
    """Verify all expected indexes exist"""
    try:
        mongodb.connect()
        db = mongodb.get_db()

        print("\nVerifying indexes...\n")

        # Expected indexes for users collection
        expected_users = ['idx_supabase_user_id', 'idx_email']

        users = db.users
        existing_indexes = list(users.index_information().keys())

        print("Users Collection:")
        for idx in expected_users:
            if idx in existing_indexes:
                print(f"  ✓ {idx}")
            else:
                print(f"  ✗ {idx} MISSING")

        # Check for projects collection if it exists
        if 'projects' in db.list_collection_names():
            expected_projects = ['idx_project_user_id', 'idx_created_at']
            projects = db.projects
            existing_indexes = list(projects.index_information().keys())

            print("\nProjects Collection:")
            for idx in expected_projects:
                if idx in existing_indexes:
                    print(f"  ✓ {idx}")
                else:
                    print(f"  ✗ {idx} MISSING")

        print()

    except Exception as e:
        print(f"\n✗ Error verifying indexes: {e}\n")
        sys.exit(1)


def list_indexes():
    """List all indexes in the database"""
    try:
        mongodb.connect()
        db = mongodb.get_db()

        print("\nDatabase Indexes:\n")

        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            indexes = collection.index_information()

            print(f"{collection_name}:")
            for index_name, index_info in indexes.items():
                keys = index_info.get('key', [])
                unique = ' (unique)' if index_info.get('unique') else ''
                print(f"  - {index_name}: {keys}{unique}")

        print()

    except Exception as e:
        print(f"\n✗ Error listing indexes: {e}\n")
        sys.exit(1)


def drop_indexes():
    """Drop all non-_id indexes (WARNING: Use with caution)"""
    try:
        mongodb.connect()
        db = mongodb.get_db()

        print("\nDropping all custom indexes...\n")

        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            indexes = collection.index_information()

            for index_name in indexes.keys():
                if index_name != '_id_':  # Don't drop default _id index
                    print(f"Dropping: {collection_name}.{index_name}")
                    collection.drop_index(index_name)

        print("\n✓ All custom indexes dropped\n")

    except Exception as e:
        print(f"\n✗ Error dropping indexes: {e}\n")
        sys.exit(1)


def show_help():
    """Show usage information"""
    print("""
Database Management Script

Usage: python manage_db.py [command]

Commands:
  create    Create all database indexes
  verify    Verify that all expected indexes exist
  list      List all indexes in the database
  drop      Drop all custom indexes (WARNING: Use with caution)
  help      Show this help message

Examples:
  python manage_db.py create
  python manage_db.py verify
  python manage_db.py list
    """)


if __name__ == '__main__':
    commands = {
        'create': create_indexes,
        'verify': verify_indexes,
        'list': list_indexes,
        'drop': drop_indexes,
        'help': show_help,
    }

    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command not in commands:
        print(f"\n✗ Unknown command: {command}\n")
        show_help()
        sys.exit(1)

    commands[command]()
