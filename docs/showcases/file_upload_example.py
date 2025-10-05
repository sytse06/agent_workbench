"""
Example: File Upload/Download API Usage

This demonstrates how to use the file management endpoints.
"""

import requests

# Base URL for local testing
BASE_URL = "http://localhost:7860/api/v1"

# For HuggingFace Spaces deployment:
# BASE_URL = "https://sytse06-agent-workbench-technical.hf.space/api/v1"


def upload_file(file_path: str):
    """Upload a file to the server."""
    print(f"📤 Uploading {file_path}...")

    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/files/upload", files=files)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Upload successful!")
        print(f"   File ID: {data['file_id']}")
        print(f"   Filename: {data['filename']}")
        print(f"   Size: {data['size']} bytes")
        print(f"   Download URL: {data['url']}")
        return data
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return None


def list_files():
    """List all uploaded files."""
    print("📋 Listing files...")

    response = requests.get(f"{BASE_URL}/files/list")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} files:")
        for file in data["files"]:
            print(f"   - {file['filename']} ({file['size']} bytes)")
            print(f"     ID: {file['file_id']}")
            print(f"     Uploaded: {file['uploaded_at']}")
        return data
    else:
        print(f"❌ List failed: {response.status_code}")
        return None


def download_file(file_id: str, save_path: str):
    """Download a file from the server."""
    print(f"📥 Downloading {file_id}...")

    response = requests.get(f"{BASE_URL}/files/download/{file_id}")

    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded to {save_path}")
        return True
    else:
        print(f"❌ Download failed: {response.status_code}")
        return False


def delete_file(file_id: str):
    """Delete a file from the server."""
    print(f"🗑️ Deleting {file_id}...")

    response = requests.delete(f"{BASE_URL}/files/delete/{file_id}")

    if response.status_code == 200:
        print(f"✅ Deleted successfully")
        return True
    else:
        print(f"❌ Delete failed: {response.status_code}")
        return False


def check_health():
    """Check file service health."""
    print("🏥 Checking file service health...")

    response = requests.get(f"{BASE_URL}/files/health")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Service status: {data['status']}")
        print(f"   Upload directory: {data['upload_dir']}")
        print(f"   Available endpoints: {data['endpoints']}")
        return data
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return None


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 File Upload/Download API Example")
    print("=" * 80)

    # 1. Check health
    check_health()
    print()

    # 2. Upload a test file
    # Create a test file
    test_file = "/tmp/test_upload.txt"
    with open(test_file, "w") as f:
        f.write("Hello from Agent Workbench file upload!\n")
        f.write("This is a test file.\n")

    upload_result = upload_file(test_file)
    print()

    # 3. List files
    list_files()
    print()

    # 4. Download the file
    if upload_result:
        download_file(upload_result["file_id"], "/tmp/test_download.txt")
        print()

        # Verify download
        with open("/tmp/test_download.txt", "r") as f:
            print("📄 Downloaded file contents:")
            print(f.read())
        print()

        # 5. Delete the file
        delete_file(upload_result["file_id"])
        print()

        # 6. Verify deletion
        list_files()

    print("=" * 80)
    print("✅ Example complete!")
    print("=" * 80)
