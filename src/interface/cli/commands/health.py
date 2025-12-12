import os
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.table import Table

from infra.adapters.storage.google_drive_adapter import GoogleDriveAdapter
from config import config

# 커스텀 테마
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "header": "bold blue",
})

console = Console(theme=custom_theme)

def check_file(path: Path, description: str) -> bool:
    """파일 존재 여부 확인 및 출력"""
    exists = path.exists()
    status = "[success]✅ 존재함[/success]" if exists else "[error]❌ 없음[/error]"
    console.print(f"  • {description}: {status} [dim]({path})[/dim]")
    return exists

def health_check():
    """
    시스템 헬스 체크
    
    필수 파일 존재 여부 및 구글 드라이브 연결 상태를 점검합니다.
    """
    console.print(Panel.fit("🏥 시스템 헬스 체크", style="header"))
    
    all_passed = True
    
    # 1. 필수 파일 점검
    console.print("\n[bold]1. 필수 파일 점검[/bold]")
    
    root_dir = Path(os.getcwd())
    
    # .env
    if not check_file(root_dir / ".env", "환경 변수 파일 (.env)"):
        all_passed = False
        
    # secrets/service_account.json
    service_account_file = Path(config.GOOGLE_SERVICE_ACCOUNT_FILE)
    if not check_file(service_account_file, "Service Account Key"):
        all_passed = False
        console.print(f"    [warning]➜ {config.GOOGLE_SERVICE_ACCOUNT_FILE} 위치에 파일을 넣어주세요.[/warning]")
    
    # 2. 구글 드라이브 연결 점검
    console.print("\n[bold]2. Google Drive 연결 테스트[/bold]")
    
    if service_account_file.exists():
        try:
            storage = GoogleDriveAdapter()
            # 1개만 조회해서 연결 확인
            files = storage.list_files(query="trashed = false")
            console.print(f"  • [success]✅ 연결 성공[/success] (조회된 파일 수: {len(files)}개)")
        except Exception as e:
            console.print(f"  • [error]❌ 연결 실패[/error]: {e}")
            all_passed = False
    else:
        console.print("  • [warning]⚠️ 키 파일이 없어 연결 테스트를 건너뜁니다.[/warning]")
        all_passed = False

    console.print("\n" + "="*30)
    if all_passed:
        console.print("[success]✨ 모든 시스템이 정상입니다![/success]")
    else:
        console.print("[error]🔥 일부 항목에 문제가 있습니다. 위 내용을 확인해주세요.[/error]")
        raise typer.Exit(code=1)
