import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.api_core.exceptions import GoogleAPIError


def initialize_db():
    try:
        
        cred = credentials.Certificate("firebase-key.json")
        firebase_admin.initialize_app(cred)
     
        db = firestore.client()
        print("[SUCCESS] Connected securely to Google Firestore Cloud Database.\n")
        return db
    except FileNotFoundError:
        print("[CRITICAL ERROR] 'firebase-key.json' not found.")
        print("Please ensure your service key file is in the root directory.")
        exit(1)
    except Exception as e:
        print(f"[AUTHENTICATION/LATENCY ERROR] Could not connect to the cloud: {e}")
        exit(1)

db = initialize_db()


def add_asset():
    print("\n--- Add New Asset to Cloud ---")
    asset_id = input("Enter Asset Tag ID (e.g., AST-001): ").strip()
    name = input("Enter Asset Name (e.g., Dell Laptop): ").strip()
    assigned_to = input("Enter Assigned Staff Name: ").strip()
    
   
    while True:
        status = input("Enter Status (active / assigned / maintenance): ").lower().strip()
        if status in ['active', 'assigned', 'maintenance']:
            break
        print("Invalid status. Please type 'active', 'assigned', or 'maintenance'.")

  
    asset_data = {
        "name": name,
        "assigned_to": assigned_to,
        "status": status,
        "timestamp": firestore.SERVER_TIMESTAMP 
    }

    try:
        
        doc_ref = db.collection("assets").document(asset_id)
        doc_ref.set(asset_data)
        print(f"[SUCCESS] Asset '{asset_id}' successfully ingested into Firestore.")
    except GoogleAPIError as e:
        print(f"[NETWORK ERROR] Failed to push data to cloud. Latency/Timeout details: {e}")


def view_filtered_assets():
    print("\n--- Query Cloud Assets ---")
    filter_status = input("Enter status to filter by (active/assigned/maintenance) or 'all': ").lower().strip()
    
    try:
        assets_ref = db.collection("assets")
        
        if filter_status == 'all':
            docs = assets_ref.stream()
        elif filter_status in ['active', 'assigned', 'maintenance']:
            docs = assets_ref.where("status", "==", filter_status).stream()
        else:
            print("Invalid selection. Returning to main menu.")
            return

        print(f"\n--- Results for Status: '{filter_status}' ---")
        count = 0
        for doc in docs:
            count += 1
            data = doc.to_dict()
            print(f"ID: {doc.id} | Name: {data.get('name')} | Assigned To: {data.get('assigned_to')} | Status: {data.get('status')}")
        
        if count == 0:
            print("No assets found matching that criteria.")
            
    except GoogleAPIError as e:
        print(f"[QUERY ERROR] Unable to retrieve records from the cloud. Network issue: {e}")

def update_asset_status():
    print("\n--- Update Asset Status ---")
    asset_id = input("Enter the Asset Tag ID to modify: ").strip()
    
    doc_ref = db.collection("assets").document(asset_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        print("[ERROR] Asset ID does not exist in the cloud.")
        return
        
    new_status = input("Enter new status (active/assigned/maintenance): ").lower().strip()
    if new_status not in ['active', 'assigned', 'maintenance']:
        print("Invalid status. Operational modification canceled.")
        return
        
    try:
        doc_ref.update({"status": new_status})
        print(f"[SUCCESS] Asset '{asset_id}' updated to '{new_status}' in real-time.")
    except GoogleAPIError as e:
        print(f"[LATENCY ERROR] Failed to update cloud record: {e}")

def delete_asset():
    print("\n--- Decommission/Delete Asset ---")
    asset_id = input("Enter the Asset Tag ID to permanently remove: ").strip()
    
    doc_ref = db.collection("assets").document(asset_id)
    if not doc_ref.get().exists:
        print("[ERROR] Asset ID does not exist in the cloud.")
        return
        
    confirm = input(f"Are you absolutely sure you want to delete {asset_id}? (yes/no): ").lower().strip()
    if confirm == 'yes':
        try:
            doc_ref.delete()
            print(f"[SUCCESS] Asset '{asset_id}' completely purged from Firestore collection.")
        except GoogleAPIError as e:
            print(f"[TERMINAL ERROR] Database interception occurred: {e}")


def main_menu():
    while True:
        print("\n==================================")
        print("   CLOUD-BACKED ASSET TRACKER     ")
        print("==================================")
        print("1. Ingest New Asset (Create)")
        print("2. Query/Filter Assets (Read)")
        print("3. Update Asset Status (Update)")
        print("4. Remove/Decommission Asset (Delete)")
        print("5. Exit Application")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == '1':
            add_asset()
        elif choice == '2':
            view_filtered_assets()
        elif choice == '3':
            update_asset_status()
        elif choice == '4':
            delete_asset()
        elif choice == '5':
            print("\nClosing connection safely. Goodbye!")
            break
        else:
            print("Invalid input. Please choose an option between 1 and 5.")

if __name__ == "__main__":
    main_menu()
