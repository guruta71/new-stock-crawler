"""
콘솔 로거 어댑터
"""
from core.ports.utility_ports import LoggerPort


class ConsoleLogger(LoggerPort):
    """
    콘솔 출력 로거 구현
    
    단순히 print로 출력하는 구현
    향후 logging 모듈이나 다른 로거로 교체 가능
    """
    
    def _safe_print(self, message: str) -> None:
        """
        Windows 환경 등에서 Unicode 출력 시 에러가 발생하면
        인코딩 가능한 문자로 대체하여 출력
        """
        try:
            print(message)
        except UnicodeEncodeError:
            # sys.stdout.encoding이 None일 수도 있으므로 기본값 설정
            import sys
            encoding = sys.stdout.encoding or 'utf-8'
            # 인코딩 불가능한 문자는 ? 등으로 대체
            safe_message = message.encode(encoding, errors='replace').decode(encoding)
            print(safe_message)

    def info(self, message: str) -> None:
        """정보 로그"""
        self._safe_print(f"[INFO] {message}")
    
    def warning(self, message: str) -> None:
        """경고 로그"""
        self._safe_print(f"[WARNING] {message}")
    
    def error(self, message: str) -> None:
        """에러 로그"""
        self._safe_print(f"[ERROR] {message}")
