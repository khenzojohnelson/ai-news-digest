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
        
        # SCOPES yang lebih luas untuk ensure permission
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
        """
        HYBRID APPROACH:
        1. Buat struktur folder via Drive API (proven works)
        2. Buat Google Doc kosong via Docs API
        3. Pindahkan doc ke folder via Drive API
        4. Isi konten via Docs API
        """
        if date is None:
            date = datetime.now()
        
        print(f"📝 Membuat Google Doc untuk tanggal {date.strftime('%Y-%m-%d')}...")
        
        try:
            # STEP 1: Buat struktur folder (Via Drive API - Already Works!)
            print("  📁 Step 1: Preparing folder structure...")
            year_folder_id = self._get_or_create_folder(
                str(date.year), 
                self.parent_folder_id
            )
            
            month_folder_id = self._get_or_create_folder(
                date.strftime('%B'),
                year_folder_id
            )
            
            # STEP 2: Buat Google Doc KOSONG (Via Docs API)
            print("  📄 Step 2: Creating empty Google Doc...")
            doc_title = f"AI News Digest - {date.strftime('%Y-%m-%d')}"
            doc_id = self._create_empty_doc(doc_title)
            
            if not doc_id:
                raise Exception("Failed to create Google Doc")
            
            # STEP 3: Pindahkan doc ke folder (Via Drive API - Already Works!)
            print("  📦 Step 3: Moving doc to folder...")
            self._move_doc_to_folder(doc_id, month_folder_id)
            
            # STEP 4: Isi konten (Via Docs API)
            print("  ✍️ Step 4: Adding content...")
            self._populate_document(doc_id, content)
            
            # Generate shareable link
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            print(f"✅ Google Doc berhasil dibuat: {doc_title}")
            return doc_url
        
        except HttpError as error:
            print(f"❌ HttpError: {error}")
            # Fallback: Coba metode alternatif
            return self._fallback_create_doc(content, date)
        
        except Exception as error:
            print(f"❌ Error: {error}")
            return self._fallback_create_doc(content, date)
    
    def _create_empty_doc(self, title):
        """Buat Google Doc kosong via Docs API"""
        try:
            doc = self.docs_service.documents().create(
                body={'title': title}
            ).execute()
            
            doc_id = doc.get('documentId')
            print(f"    ✓ Doc created with ID: {doc_id}")
            return doc_id
        
        except HttpError as e:
            print(f"    ✗ Docs API error: {e}")
            # Kalau Docs API gagal, coba buat via Drive API
            return self._create_doc_via_drive(title)
    
    def _create_doc_via_drive(self, title):
        """FALLBACK: Buat Google Doc via Drive API (alternatif method)"""
        try:
            print("    🔄 Fallback: Using Drive API to create doc...")
            
            file_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            file = self.drive_service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            doc_id = file.get('id')
            print(f"    ✓ Doc created via Drive API: {doc_id}")
            return doc_id
        
        except Exception as e:
            print(f"    ✗ Drive API fallback also failed: {e}")
            return None
    
    def _move_doc_to_folder(self, doc_id, folder_id):
        """Pindahkan doc ke folder (Via Drive API - This works!)"""
        try:
            # Get current parents
            file = self.drive_service.files().get(
                fileId=doc_id,
                fields='parents'
            ).execute()
            
            previous_parents = ",".join(file.get('parents', []))
            
            # Move to new folder
            self.drive_service.files().update(
                fileId=doc_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            print(f"    ✓ Doc moved to folder")
        
        except Exception as e:
            print(f"    ✗ Error moving doc: {e}")
            # Not critical, doc still exists, just not in right folder
    
    def _populate_document(self, doc_id, markdown_content):
        """Isi konten ke Google Doc (Via Docs API)"""
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
            
            print(f"    ✓ Content added successfully")
        
        except HttpError as e:
            print(f"    ✗ Error adding content: {e}")
            print(f"    ⚠️ Doc created but empty. You can edit manually.")
            # Not critical, doc exists, just empty
        
        except Exception as e:
            print(f"    ✗ Unexpected error: {e}")
    
    def _fallback_create_doc(self, content, date):
        """
        ULTIMATE FALLBACK: Buat doc langsung di root, skip folder structure
        Kalau semua metode gagal, at least doc tetap terbuat
        """
        try:
            print("  🆘 Fallback: Creating doc in root folder...")
            
            doc_title = f"AI News Digest - {date.strftime('%Y-%m-%d')}"
            
            # Try Docs API first
            doc_id = self._create_empty_doc(doc_title)
            
            if not doc_id:
                # Try Drive API
                doc_id = self._create_doc_via_drive(doc_title)
            
            if doc_id:
                # Try to add content
                self._populate_document(doc_id, content)
                
                doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
                print(f"  ✓ Fallback succeeded: {doc_url}")
                print(f"  ⚠️ Doc created in root folder, not in organized structure")
                return doc_url
            else:
                print("  ✗ All methods failed")
                return None
        
        except Exception as e:
            print(f"  ✗ Fallback also failed: {e}")
            return None
    
    def _get_or_create_folder(self, folder_name, parent_id):
        """Cari atau buat folder (Via Drive API - This works!)"""
        
        query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        try:
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            else:
                # Buat folder baru
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id]
                }
                
                folder = self.drive_service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                
                print(f"    ✓ Folder '{folder_name}' created")
                return folder.get('id')
        
        except Exception as e:
            print(f"    ✗ Error with folder '{folder_name}': {e}")
            # Return parent as fallback
            return parent_id
    
    def _markdown_to_plain_text(self, markdown):
        """Convert markdown ke plain text (simplified)"""
        
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', markdown)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[\-\*]\s+', '• ', text, flags=re.MULTILINE)
        
        return text
