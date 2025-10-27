import os
import json
import re
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from io import BytesIO
from googleapiclient.http import MediaIoBaseUpload

class GoogleDocsAgent:
    def __init__(self):
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not creds_json:
            raise ValueError("❌ GOOGLE_CREDENTIALS_JSON tidak ditemukan!")
        
        creds_dict = json.loads(creds_json)
        
        SCOPES = [
            'https://www.googleapis.com/auth/drive',
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
        """Create Google Doc directly in target folder (uses owner's storage, not service account)"""
        if date is None:
            date = datetime.now()
        
        print(f"📝 Membuat Google Doc untuk tanggal {date.strftime('%Y-%m-%d')}...")
        
        try:
            # Step 1: Prepare folder structure
            print("  📁 Step 1: Preparing folder structure...")
            year_folder_id = self._get_or_create_folder(str(date.year), self.parent_folder_id)
            month_folder_id = self._get_or_create_folder(date.strftime('%B'), year_folder_id)
            
            # Step 2: Create Google Doc DIRECTLY in target folder
            print("  📄 Step 2: Creating Google Doc...")
            doc_title = f"AI News Digest - {date.strftime('%Y-%m-%d')}"
            
            file_metadata = {
                'name': doc_title,
                'mimeType': 'application/vnd.google-apps.document',
                'parents': [month_folder_id]
            }
            
            file = self.drive_service.files().create(
                body=file_metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()
            
            doc_id = file.get('id')
            print(f"    ✓ Doc created: {doc_id}")
            
            # Step 3: Add content
            print("  ✍️ Step 3: Adding content...")
            self._populate_document(doc_id, content)
            
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            print(f"✅ Google Doc berhasil dibuat: {doc_title}")
            return doc_url
        
        except HttpError as error:
            print(f"❌ HttpError: {error}")
            return self._create_text_fallback(content, date, month_folder_id)
        
        except Exception as error:
            print(f"❌ Error: {error}")
            return self._create_text_fallback(content, date, month_folder_id)
    
    def _populate_document(self, doc_id, markdown_content):
        """Add content to Google Doc"""
        try:
            plain_text = self._markdown_to_plain_text(markdown_content)
            
            requests = [{
                'insertText': {
                    'location': {'index': 1},
                    'text': plain_text
                }
            }]
            
            self.docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            print(f"    ✓ Content added")
        
        except Exception as e:
            print(f"    ⚠️ Could not add content: {e}")
            print(f"    📝 Doc created but empty - you can edit manually")
    
    def _create_text_fallback(self, content, date, folder_id):
        """Fallback: Create plain text file if Google Docs fails"""
        try:
            print("  🆘 Fallback: Creating plain text file...")
            
            doc_title = f"AI News Digest - {date.strftime('%Y-%m-%d')}.txt"
            plain_text = self._markdown_to_plain_text(content)
            
            file_metadata = {
                'name': doc_title,
                'parents': [folder_id]
            }
            
            media = MediaIoBaseUpload(
                BytesIO(plain_text.encode('utf-8')),
                mimetype='text/plain',
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink',
                supportsAllDrives=True
            ).execute()
            
            file_url = file.get('webViewLink')
            print(f"  ✓ Text file created: {file_url}")
            print(f"  ⚠️ Created as .txt (not Google Doc)")
            
            return file_url
        
        except Exception as e:
            print(f"  ✗ Text fallback failed: {e}")
            return None
    
    def _get_or_create_folder(self, folder_name, parent_id):
        """Get or create folder"""
        query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        try:
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True
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
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                
                print(f"    ✓ Folder '{folder_name}' created")
                return folder.get('id')
        
        except Exception as e:
            print(f"    ✗ Folder error: {e}")
            return parent_id
    
    def _markdown_to_plain_text(self, markdown):
        """Convert markdown to plain text"""
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', markdown)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[\-\*]\s+', '• ', text, flags=re.MULTILINE)
        return text
