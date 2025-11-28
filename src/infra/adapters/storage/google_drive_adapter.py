"""
Google Drive 저장소 어댑터 구현
"""
import os
from pathlib import Path
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from core.ports.storage_ports import StoragePort
from config import config


class GoogleDriveAdapter(StoragePort):
    """
    Google Drive API를 사용한 파일 업로드 어댑터
    """
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, service_account_file: str = None, folder_id: str = None):
        self.service_account_file = service_account_file or config.GOOGLE_SERVICE_ACCOUNT_FILE
        self.folder_id = folder_id or config.GOOGLE_DRIVE_FOLDER_ID
        self._service = None
        
    def _authenticate(self):
        """Google Drive API 인증 및 서비스 생성 (Lazy Loading)"""
        if self._service:
            return

        if not os.path.exists(self.service_account_file):
            raise FileNotFoundError(f"Service Account 키 파일을 찾을 수 없습니다: {self.service_account_file}")

        creds = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes=self.SCOPES
        )
        self._service = build('drive', 'v3', credentials=creds)

    def upload_file(self, local_path: Path, remote_filename: str = None) -> str:
        """
        파일을 Google Drive 폴더로 업로드
        
        Args:
            local_path: 로컬 파일 경로
            remote_filename: 저장할 파일명 (기본값: 로컬 파일명)
            
        Returns:
            str: 업로드된 파일 ID
        """
        self._authenticate()
        
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"업로드할 파일을 찾을 수 없습니다: {local_path}")
            
        file_name = remote_filename or local_path.name
        
        file_metadata = {
            'name': file_name,
            'parents': [self.folder_id] if self.folder_id else []
        }
        
        media = MediaFileUpload(
            str(local_path),
            resumable=True
        )
        
        # 파일 생성 (업로드)
        file = self._service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"      [Google Drive] 업로드 완료: {file_name} (ID: {file.get('id')})")
        return file.get('id')
