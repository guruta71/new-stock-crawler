from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    OUTPUT_DIR: Path = BASE_DIR / "output"

    # Web Scraping
    BASE_URL: str = "http://www.38.co.kr"
    HEADLESS: bool = True
    DEFAULT_TIMEOUT: int = 30000  # ms

    # Data Export
    EXCEL_FILENAME: str = "stock_data.xlsx"
    
    # Google Drive Integration
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "service_account.json"
    GOOGLE_DRIVE_FOLDER_ID: str = ""  # .env에서 설정 필요
    
    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_output_path(self, filename: str = None) -> Path:
        """출력 파일의 전체 경로를 반환합니다."""
        if not self.OUTPUT_DIR.exists():
            self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        target_filename = filename or self.EXCEL_FILENAME
        return self.OUTPUT_DIR / target_filename

# 전역 설정 객체
config = Settings()
