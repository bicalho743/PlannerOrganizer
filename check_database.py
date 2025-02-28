
import os
import sys
import psycopg2
import time

def check_database_connection():
    """
    Check the database connection and provide helpful diagnostics
    """
    print("Database Connection Checker")
    print("--------------------------")
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        print("Please set this variable in the Secrets (Environment Variables) tab")
        return False
    
    # Mask credentials for safe display
    safe_url = database_url.split('@')
    if len(safe_url) > 1:
        print(f"✓ DATABASE_URL is set and points to: ...@{safe_url[1]}")
    else:
        print("⚠️ DATABASE_URL is set but doesn't match expected format")
    
    # Try to connect
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        print(f"\nAttempt {attempt}/{max_retries} to connect to database...")
        try:
            conn = psycopg2.connect(database_url, connect_timeout=10)
            cur = conn.cursor()
            print("✓ Successfully connected to database!")
            
            # Check if database is responsive
            cur.execute("SELECT 1")
            result = cur.fetchone()
            print(f"✓ Database query successful: {result}")
            
            # Close connection
            cur.close()
            conn.close()
            print("✓ Connection closed properly")
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ Connection error: {str(e)}")
            if "endpoint is disabled" in str(e):
                print("\n⚠️ DATABASE ENDPOINT IS DISABLED")
                print("This is common with serverless databases like Neon PostgreSQL")
                print("You need to reactivate your database endpoint")
                print("Go to your database provider dashboard and restart the endpoint")
            
            # Wait before retrying
            if attempt < max_retries:
                wait_time = 5
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            break
    
    print("\n❌ Failed to connect to the database after multiple attempts")
    print("Please check your database configuration and make sure the endpoint is active")
    return False

if __name__ == "__main__":
    success = check_database_connection()
    sys.exit(0 if success else 1)
