import typer
from interface.cli.dependencies import build_dependencies
from infra.adapters.utils.console_logger import ConsoleLogger

def auth_drive():
    """
    구글 드라이브 인증 (토큰 생성용)
    
    크롤링 없이 오직 구글 드라이브 인증만 수행하여 token.json을 생성합니다.
    """
    logger = ConsoleLogger()
    logger.info("=" * 60)
    logger.info("🔐 Google Drive 인증 시작")
    logger.info("=" * 60)
    
    try:
        # 의존성 빌드 (여기서 GoogleDriveAdapter가 초기화됨)
        deps = build_dependencies(headless=True)
        storage = deps['storage']
        
        # 인증 트리거 (파일 목록 조회 시도)
        logger.info("구글 로그인 창이 열리면 인증을 진행해주세요...")
        files = storage.list_files(query="trashed = false")
        
        logger.info("✅ 인증 성공! (token.json 생성됨)")
        logger.info(f"현재 드라이브 파일 수: {len(files)}개")
        
    except Exception as e:
        logger.error(f"❌ 인증 실패: {e}")
        raise typer.Exit(code=1)
