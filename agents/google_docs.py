import os
import json
import re
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleDocsAgent:
    def __init__(self):
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not creds_json:
            raise ValueError("❌ GOOGLE_CREDENTIALS_JSON tidak ditemukan!")
        
        creds_dict = json.loads(creds_json)
        
        SCOPES = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/documents'
        ]
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, 
            scopes=SCOPES
        )
        
        self.drive_service = build('drive', 'v3', credentials=credentials)
        self.docs_service = build('docs', 'v1', credentials=credentials)
        
        self.parent_folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        if not self.parent_folder_id:
            raise ValueError("❌ GOOGLE_DRIVE_FOLDER_ID tidak ditemukan!")
        
        print("✅ Google Drive & Docs API initialized")
    
    def create_and_save(self, content, date=None):
        if date is None:
            date = datetime.now()
        
        print(f"📝 Membuat Google Doc untuk tanggal {date.strftime('%Y-%m-%d')}...")
        
        try:
            year_folder_id = self._get_or_create_folder(
                str(date.year), 
                self.parent_folder_id
            )
            
            month_folder_id = self._get_or_create_folder(
                date.strftime('%B'),
                year_folder_id
            )
            
            doc_title = f"AI News Digest - {date.strftime('%Y-%m-%d')}"
            doc_id = self._create_document(doc_title, month_folder_id)
            
            self._populate_document(doc_id, content)
            
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            print(f"✅ Google Doc berhasil dibuat: {doc_title}")
            return doc_url
        
        except HttpError as error:
            print(f"❌ Error creating Google Doc: {error}")
            return None
    
    def _get_or_create_folder(self, folder_name, parent_id):
        query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        results = self.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        else:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = self.drive_service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            print(f"  📁 Folder '{folder_name}' dibuat")
            return folder.get('id')
    
    def _create_document(self, title, parent_folder_id):
        doc = self.docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc.get('documentId')
        
        self.drive_service.files().update(
            fileId=doc_id,
            addParents=parent_folder_id,
            removeParents='root',
            fields='id, parents'
        ).execute()
        
        return doc_id
    
    def _populate_document(self, doc_id, markdown_content):
        requests = []
        
        plain_text = self._markdown_to_plain_text(markdown_content)
        
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': plain_text
            }
        })
        
        self.docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
    
    def _markdown_to_plain_text(self, markdown):
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', markdown)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[\-\*]\s+', '• ', text, flags=re.MULTILINE)
        
        return text