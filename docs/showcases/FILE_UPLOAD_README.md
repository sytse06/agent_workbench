# File Upload/Download API

## Overview

The Agent Workbench now includes HTTP endpoints for file upload and download functionality. This provides a channel for external clients to:

- Upload files (documents, images, data files, etc.)
- Download previously uploaded files
- List all uploaded files with metadata
- Delete files when no longer needed

## Why HTTP Endpoints?

This demonstrates the **hybrid architecture** discussed earlier:

1. **Gradio UI** → Direct service calls (avoids deadlock)
2. **External clients** → HTTP endpoints (file uploads, integrations, etc.)

File operations are perfect for HTTP because:
- They require multipart form data (native to HTTP)
- They're typically called by external tools/scripts
- They don't cause the deadlock issue (no Gradio event loop blocking)

## Endpoints

### Base URL

**Local development:**
```
http://localhost:7860/api/v1/files
```

**HuggingFace Spaces:**
```
https://sytse06-agent-workbench-technical.hf.space/api/v1/files
```

### Available Endpoints

#### 1. Upload File

```http
POST /api/v1/files/upload
Content-Type: multipart/form-data

file: <binary file data>
```

**Response:**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000_document.pdf",
  "filename": "document.pdf",
  "size": 102400,
  "content_type": "application/pdf",
  "uploaded_at": "2025-10-05T09:30:00.000000",
  "url": "/api/v1/files/download/550e8400-e29b-41d4-a716-446655440000_document.pdf"
}
```

#### 2. Download File

```http
GET /api/v1/files/download/{file_id}
```

Returns the file with appropriate `Content-Type` and `Content-Disposition` headers.

#### 3. List Files

```http
GET /api/v1/files/list
```

**Response:**
```json
{
  "files": [
    {
      "file_id": "550e8400-e29b-41d4-a716-446655440000_document.pdf",
      "filename": "document.pdf",
      "size": 102400,
      "content_type": "application/pdf",
      "uploaded_at": "2025-10-05T09:30:00.000000",
      "url": "/api/v1/files/download/550e8400-e29b-41d4-a716-446655440000_document.pdf"
    }
  ],
  "total": 1
}
```

#### 4. Delete File

```http
DELETE /api/v1/files/delete/{file_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "File 550e8400-e29b-41d4-a716-446655440000_document.pdf deleted"
}
```

#### 5. Health Check

```http
GET /api/v1/files/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "file_management",
  "upload_dir": "/tmp/agent_workbench_uploads",
  "upload_dir_exists": true,
  "endpoints": ["/upload", "/download/{file_id}", "/list", "/delete/{file_id}"]
}
```

## Storage Architecture

### Local Development (SQLite mode)
- Files stored in: `/tmp/agent_workbench_uploads/`
- Metadata stored in: Hub DB `file_metadata` table

### HuggingFace Spaces (Hub DB mode)
- Files stored in: `/tmp/agent_workbench_uploads/` (ephemeral)
- Metadata stored in: HuggingFace Datasets repository
- **Note:** File storage is ephemeral in HF Spaces. For production, consider:
  - HuggingFace Hub storage via `hf_api.upload_file()`
  - External storage (S3, GCS, etc.)
  - Encoding small files as base64 in Hub DB

## Usage Examples

### Python (requests library)

```python
import requests

# Upload file
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:7860/api/v1/files/upload",
        files={"file": f}
    )
    file_data = response.json()
    print(f"Uploaded: {file_data['file_id']}")

# Download file
file_id = file_data['file_id']
response = requests.get(f"http://localhost:7860/api/v1/files/download/{file_id}")
with open("downloaded.pdf", "wb") as f:
    f.write(response.content)

# List files
response = requests.get("http://localhost:7860/api/v1/files/list")
files = response.json()
print(f"Total files: {files['total']}")

# Delete file
response = requests.delete(f"http://localhost:7860/api/v1/files/delete/{file_id}")
print(response.json()['message'])
```

### cURL

```bash
# Upload file
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:7860/api/v1/files/upload

# Download file
curl http://localhost:7860/api/v1/files/download/{file_id} \
  -o downloaded.pdf

# List files
curl http://localhost:7860/api/v1/files/list

# Delete file
curl -X DELETE \
  http://localhost:7860/api/v1/files/delete/{file_id}
```

### JavaScript (fetch API)

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:7860/api/v1/files/upload', {
  method: 'POST',
  body: formData
});
const fileData = await response.json();

// Download file
const downloadResponse = await fetch(
  `http://localhost:7860/api/v1/files/download/${fileData.file_id}`
);
const blob = await downloadResponse.blob();
const url = window.URL.createObjectURL(blob);
```

## Example Script

See `file_upload_example.py` for a complete working example that demonstrates all endpoints.

Run it with:
```bash
python docs/showcases/file_upload_example.py
```

## Future Enhancements

Potential improvements for production use:

1. **Persistent Storage in HF Spaces**
   - Upload to HuggingFace Hub repository
   - Integration with external storage (S3, GCS)
   - Base64 encoding for small files in Hub DB

2. **File Processing**
   - Document parsing (PDF → text)
   - Image processing (thumbnails, format conversion)
   - Archive extraction (ZIP, TAR)

3. **Security**
   - File type validation
   - Size limits
   - Virus scanning
   - Access control

4. **Integration**
   - Use uploaded files as context for LLM conversations
   - Extract text from documents for RAG
   - Process data files (CSV, JSON) for analysis

## Architecture Decision: Direct Service Calls vs HTTP

This file upload feature demonstrates **when to use each pattern**:

### Use HTTP Endpoints When:
- ✅ Called by external clients (scripts, tools, integrations)
- ✅ File operations (multipart form data)
- ✅ Webhooks/callbacks
- ✅ Testing/debugging with curl/Postman
- ✅ Microservices architecture (separate processes)

### Use Direct Service Calls When:
- ✅ Called from Gradio event handlers (avoids deadlock)
- ✅ Single-process architecture
- ✅ Internal service-to-service calls
- ✅ Need transaction consistency
- ✅ Performance-critical paths

### Our Hybrid Approach:
```python
# Gradio UI handler (direct call)
async def handle_message(msg, ...):
    llm_service = ChatService(model_config)
    response = await llm_service.chat_completion(message=msg)
    return response.reply

# HTTP endpoint (external clients)
@router.post("/api/v1/files/upload")
async def upload_file(file: UploadFile):
    # Handle file upload
    return {"file_id": file_id, ...}
```

This gives us **the best of both worlds**: fast, deadlock-free UI interactions + extensible HTTP API for external integrations.
