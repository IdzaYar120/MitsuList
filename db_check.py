import psycopg2
import sys

# Connection details matching settings.py and docker command
DB_NAME = "mitsulist_db"
DB_USER = "postgres"
DB_PASS = "mitsulist_pass"
DB_HOST = "172.17.0.2"
DB_PORT = "5432"

print(f"Attempting to connect to {DB_HOST}:{DB_PORT}...")

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    print("SUCCESS: Connection established!")
    conn.close()
except Exception as e:
    print("\nFAILURE: Could not connect.")
    print(f"Error Type: {type(e).__name__}")
    # Try to decode message with different encodings if default fails
    try:
        print(f"Message: {e}")
    except Exception:
        print("Message could not be decoded normally.")
        # Attempting to print raw bytes if accessible or handle encoding
        if hasattr(e, 'args'):
            for arg in e.args:
                if isinstance(arg, bytes):
                    print(f"Raw bytes: {arg}")
                    try:
                        print(f"Decoded (cp1251): {arg.decode('cp1251')}")
                    except:
                        pass
                else:
                    print(f"Arg: {arg}")
