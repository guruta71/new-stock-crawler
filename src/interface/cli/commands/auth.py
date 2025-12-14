import typer
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
import os

from google_auth_oauthlib.flow import InstalledAppFlow
from config import config
from infra.adapters.storage.google_drive_adapter import GoogleDriveAdapter

# 커스텀 테마 정의
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
})

console = Console(theme=custom_theme)


def auth_drive():
    """
    구글 드라이브 인증 (OAuth 2.0)
    
    웹 브라우저를 열어 구글 로그인을 수행하고,
    발급받은 인증 토큰을 로컬 파일(token.json)로 저장합니다.
    """
    console.print(Panel.fit("🔐 Google Drive 인증 도구 (OAuth 2.0)", style="bold blue"))
    
    try:
        # 0. Client Secret 확인
        if not os.path.exists(config.GOOGLE_CLIENT_SECRET_FILE):
             console.print(f"[error]❌ Client Secret 파일을 찾을 수 없습니다.[/error]\n경로: {config.GOOGLE_CLIENT_SECRET_FILE}")
             raise typer.Exit(code=1)

        console.print("[info]브라우저를 실행하여 인증을 진행합니다...[/info]")
        
        # 1. Flow 생성 및 인증 진행
        flow = InstalledAppFlow.from_client_secrets_file(
            config.GOOGLE_CLIENT_SECRET_FILE,
            scopes=GoogleDriveAdapter.SCOPES
        )
        
        creds = flow.run_local_server(port=0)
        
        # 2. 토큰 저장
        console.print(f"[info]토큰을 저장합니다...[/info] ({config.GOOGLE_TOKEN_FILE})")
        
        # secrets 폴더가 없으면 생성
        os.makedirs(os.path.dirname(config.GOOGLE_TOKEN_FILE), exist_ok=True)
        
        with open(config.GOOGLE_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
        console.print(Panel(f"[success]✅ 인증 성공! 토큰이 저장되었습니다.[/success]", title="인증 완료", border_style="green"))
        
        # 3. 연결 테스트
        console.print("\n[info]연결 테스트를 수행합니다...[/info]")
        storage = GoogleDriveAdapter()
        files = storage.list_files(query="trashed = false")
        console.print(f"  • [success]✅ 연결 확인됨[/success] (현재 드라이브 파일 수: {len(files)}개)")
        
    except Exception as e:
        console.print(f"[error]❌ 인증 실패:[/error] {e}")
        raise typer.Exit(code=1)

