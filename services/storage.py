import os
import uuid
from fastapi import UploadFile, HTTPException
from supabase import Client
from typing import List

class StorageService:
    def __init__(self, client: Client):
        self.client = client
        self.bucket = "reimbursement-documents"
        self.allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
        self.max_size = 10 * 1024 * 1024 # 10MB

    async def upload_file(self, file: UploadFile) -> str:
        if file.content_type not in self.allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        contents = await file.read()
        if len(contents) > self.max_size:
            raise HTTPException(status_code=400, detail="File too large")

        file_ext = os.path.splitext(file.filename)[1]
        file_path = f"{uuid.uuid4()}{file_ext}"

        res = self.client.storage.from_(self.bucket).upload(file_path, contents, {"content-type": file.content_type})
        
        public_url = self.client.storage.from_(self.bucket).get_public_url(file_path)
        return public_url
