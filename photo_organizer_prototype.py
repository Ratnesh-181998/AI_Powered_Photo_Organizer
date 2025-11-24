import os
import json
import shutil
import time
import random
from datetime import datetime

# --- Configuration ---
BASE_DIR = os.getcwd()
S3_BUCKET_DIR = os.path.join(BASE_DIR, "mock_s3_bucket")
DB_FILE = os.path.join(BASE_DIR, "mock_dynamodb.json")

# Ensure clean state for demo
if not os.path.exists(S3_BUCKET_DIR):
    os.makedirs(S3_BUCKET_DIR)

# --- Mock AWS Services ---

class MockS3:
    """Simulates AWS S3 for file storage."""
    def upload_file(self, source_path, key):
        destination = os.path.join(S3_BUCKET_DIR, key)
        # Ensure the directory for the key exists (e.g., user_123/)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(source_path, destination)
        print(f"[S3] Uploaded {source_path} to bucket key: {key}")
        return destination

    def get_file_url(self, key):
        return os.path.join(S3_BUCKET_DIR, key)

class MockRekognition:
    """Simulates AWS Rekognition for object detection."""
    def detect_labels(self, image_key):
        print(f"[Rekognition] Analyzing image: {image_key}...")
        time.sleep(0.5) # Simulate processing time
        
        # Simulate detecting labels based on filename keywords for realism
        labels = ["Person", "Indoor", "Screenshot"]
        
        lower_key = image_key.lower()
        if "error" in lower_key:
            labels.extend(["Text", "Error Message", "Computer", "Monitor"])
        if "search" in lower_key:
            labels.extend(["Web Page", "Search Results", "UI", "Internet"])
        if "login" in lower_key:
            labels.extend(["Form", "Login Screen", "Security"])
        if "job" in lower_key:
            labels.extend(["Document", "Resume", "Business"])
            
        # Add some random confidence scores
        results = []
        for label in labels:
            results.append({
                "Name": label,
                "Confidence": random.uniform(85.0, 99.9)
            })
        
        print(f"[Rekognition] Detected: {[r['Name'] for r in results]}")
        return results

class MockDynamoDB:
    """Simulates AWS DynamoDB for metadata storage."""
    def __init__(self):
        self.table = {}
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                self.table = json.load(f)

    def put_item(self, item):
        key = item['photo_id']
        self.table[key] = item
        self._save()
        print(f"[DynamoDB] Saved metadata for {key}")

    def get_item(self, photo_id):
        return self.table.get(photo_id)
    
    def scan(self):
        return list(self.table.values())

    def _save(self):
        with open(DB_FILE, 'w') as f:
            json.dump(self.table, f, indent=2)

class MockOpenSearch:
    """Simulates AWS OpenSearch for querying."""
    def __init__(self, db_ref):
        self.db = db_ref

    def search(self, query_text):
        print(f"[OpenSearch] Searching for: '{query_text}'...")
        results = []
        all_items = self.db.scan()
        
        query_tokens = query_text.lower().split()
        
        for item in all_items:
            # Search in tags/labels
            item_tags = [t.lower() for t in item.get('tags', [])]
            # Search in filename
            item_id = item.get('photo_id', '').lower()
            
            match = False
            for token in query_tokens:
                if token in item_tags or token in item_id:
                    match = True
                    break
            
            if match:
                results.append(item)
        
        return results

# --- Core System Logic (The "Lambda" Functions) ---

class PhotoOrganizerSystem:
    def __init__(self):
        self.s3 = MockS3()
        self.rekognition = MockRekognition()
        self.db = MockDynamoDB()
        self.search_engine = MockOpenSearch(self.db)

    def upload_and_process(self, file_path, user_id="user_123"):
        """
        Simulates the entire pipeline: 
        Upload -> S3 -> Trigger -> Rekognition -> DynamoDB -> Indexing
        """
        filename = os.path.basename(file_path)
        timestamp = datetime.now().isoformat()
        
        print(f"\n--- Processing Upload: {filename} ---")
        
        # 1. Upload to S3
        s3_key = f"{user_id}/{filename}"
        self.s3.upload_file(file_path, s3_key)
        
        # 2. Trigger Processing (Simulating Lambda)
        labels_data = self.rekognition.detect_labels(s3_key)
        tags = [l['Name'] for l in labels_data]
        
        # 3. Store Metadata
        metadata = {
            "photo_id": s3_key,
            "user_id": user_id,
            "timestamp": timestamp,
            "tags": tags,
            "original_filename": filename,
            "location": "Unknown" # Placeholder
        }
        self.db.put_item(metadata)
        
        print(f"[SUCCESS] Successfully processed {filename}")
        return metadata

    def search_photos(self, query):
        """Simulates the Search API"""
        print(f"\n--- executing Search Query: {query} ---")
        results = self.search_engine.search(query)
        print(f"Found {len(results)} results:")
        for res in results:
            print(f" - {res['original_filename']} (Tags: {res['tags']})")
        return results

# --- Main Execution ---

def main():
    system = PhotoOrganizerSystem()
    
    # 1. Find some images to "upload"
    # We will use the png files found in the current directory
    current_dir = os.getcwd()
    image_files = [f for f in os.listdir(current_dir) if f.endswith('.png')]
    
    if not image_files:
        print("No .png files found in current directory to test with.")
        # Create a dummy file if none exist
        with open("test_image_dummy.png", "w") as f:
            f.write("dummy image content")
        image_files = ["test_image_dummy.png"]

    print(f"Found {len(image_files)} images to process.")
    
    # 2. Process a few images
    for img in image_files[:3]: # Limit to 3 for demo
        full_path = os.path.join(current_dir, img)
        system.upload_and_process(full_path)
        
    # 3. Perform Searches
    print("\n" + "="*30)
    print("TESTING SEARCH CAPABILITIES")
    print("="*30)
    
    system.search_photos("error")
    system.search_photos("search")
    system.search_photos("login")
    
    print("\nDone. Check 'mock_s3_bucket' and 'mock_dynamodb.json' for artifacts.")

if __name__ == "__main__":
    main()
