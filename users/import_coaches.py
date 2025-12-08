import os
import django
import csv
from pathlib import Path
import sys

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent  # kulatih-web folder
APP_DIR = Path(__file__).resolve().parent  # users folder
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kulatih.settings')

# Django setup
try:
    django.setup()
except Exception as e:
    print(f"ERROR: Failed to setup Django. {e}")
    exit()

# Import models
try:
    from django.contrib.auth.models import User
    from users.models import Coach
except ImportError as e:
    print(f"ERROR: Failed to import models. {e}")
    exit()

COACHES_CSV_FILE = APP_DIR / 'data' / 'coaches.csv'

def import_coaches():
    """Import coaches from CSV file"""
    if not COACHES_CSV_FILE.exists():
        print(f"ERROR: File '{COACHES_CSV_FILE}' not found.")
        return

    try:
        with open(COACHES_CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            created_count = 0
            skipped_count = 0
            
            for row in reader:
                # Check if user already exists
                if User.objects.filter(username=row['username']).exists():
                    print(f"SKIPPED: User '{row['username']}' already exists.")
                    skipped_count += 1
                    continue

                # Create user
                try:
                    user = User.objects.create_user(
                        username=row['username'],
                        email=row['email'],
                        password=row['password'],
                        first_name=row['first_name'],
                        last_name=row['last_name']
                    )

                    # Create coach profile
                    Coach.objects.create(
                        user=user,
                        sport=row['sport'],
                        hourly_fee=row['hourly_fee'],
                        city=row['city'],
                        phone=row['phone'],
                        description=row['description'],
                        profile_photo=row['profile_photo']
                    )

                    print(f"✓ Created coach: {row['first_name']} {row['last_name']} ({row['username']})")
                    created_count += 1

                except Exception as e:
                    print(f"ERROR creating coach {row['username']}: {e}")
                    # If coach creation fails, delete the user
                    if User.objects.filter(username=row['username']).exists():
                        User.objects.get(username=row['username']).delete()

            print(f"\n{'='*50}")
            print(f"Import completed!")
            print(f"Created: {created_count} coaches")
            print(f"Skipped: {skipped_count} coaches")
            print(f"{'='*50}")

    except FileNotFoundError:
        print(f"ERROR: File '{COACHES_CSV_FILE}' not found.")
    except Exception as e:
        print(f"ERROR during import: {e}")

if __name__ == "__main__":
    print("Starting coach import from CSV...")
    print(f"CSV file: {COACHES_CSV_FILE}")
    print(f"{'='*50}\n")
    
    import_coaches()