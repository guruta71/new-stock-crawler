"""
Text Parsers 단위 테스트

테스트 대상:
- parse_to_int: 문자열을 정수로 변환
- clean_stock_name: 종목명 정제
- is_spac_stock: 스팩 여부 확인
- format_competition_rate: 경쟁률 포맷팅
- extract_share_count: 주식 수 추출
- clean_tradable_values: 유통가능물량 정제
"""
import pytest
from infra.adapters.parsing.text.parsers import (
    parse_to_int,
    clean_stock_name,
    is_spac_stock,
    format_competition_rate,
    extract_share_count,
    clean_tradable_values,
)


class TestParseToInt:
    """parse_to_int 함수 테스트"""

    @pytest.mark.parametrize("input_str, expected", [
        ("12345", 12345),           # 정상 숫자
        ("100", 100),               # 정상 숫자
        ("1,000,000", 1_000_000),   # 쉼표 포함
        ("500,000", 500_000),       # 쉼표 포함
        ("10,000주", 10_000),       # 단위 '주' 포함
        ("5,000 주", 5_000),        # 단위 ' 주' 포함
        ("1,000,000원", 1_000_000), # 단위 '원' 포함
        ("10,000(예정)", 10_000),   # 괄호 포함
        ("5,000 (확정)", 5_000),    # 괄호 포함
        ("10,000~15,000", 10_000),  # 물결표 범위
        ("5,000 ~ 8,000원", 5_000), # 물결표 범위 + 단위
        ("100:200", 100),           # 콜론 범위
        ("100.5", 100),             # 실수형 문자열
        ("99.9", 99),               # 실수형 문자열
    ])
    def test_parse_to_int_success(self, input_str, expected):
        """
        다양한 형식의 문자열을 정수로 올바르게 변환하는지 테스트합니다.

        Arrange: 테스트할 입력 문자열(input_str)과 기대하는 정수값(expected) 준비
        Act: parse_to_int 호출
        Assert: 반환값이 기대값과 일치하는지 확인
        """
        assert parse_to_int(input_str) == expected

    @pytest.mark.parametrize("input_str", [
        "N/A",          # N/A
        "-",            # 하이픈
        "",             # 빈 문자열
        "   ",          # 공백
        "abc",          # 문자
        "가나다",       # 한글
    ])
    def test_parse_to_int_returns_none(self, input_str):
        """
        변환 불가능하거나 유효하지 않은 문자열에 대해 None을 반환하는지 테스트합니다.

        Arrange: 유효하지 않은 입력 문자열(input_str) 준비
        Act: parse_to_int 호출
        Assert: None 반환 확인
        """
        assert parse_to_int(input_str) is None


class TestCleanStockName:
    """clean_stock_name 함수 테스트"""

    @pytest.mark.parametrize("input_name, expected", [
        ("테스트회사(상장)", "테스트회사"),          # (상장) 제거
        ("샘플 (상장)", "샘플"),                     # (상장) 제거 (공백 포함)
        ("테스트회사(구.옛날이름)", "테스트회사"),   # (구.xxx) 제거
        ("회사(구.ABC)명", "회사명"),                # 중간에 있는 (구.xxx) 제거
        ("테스트(구.옛이름)(상장)", "테스트"),       # 복합 패턴 제거
        ("삼성전자", "삼성전자"),                    # 일반 종목명 유지
        ("SK하이닉스", "SK하이닉스"),                # 일반 종목명 유지
        ("  회사명  ", "회사명"),                    # 앞뒤 공백 제거
    ])
    def test_clean_stock_name(self, input_name, expected):
        """
        종목명에서 불필요한 패턴을 제거하고 정제하는지 테스트합니다.

        Arrange: 원본 종목명(input_name)과 정제된 기대값(expected) 준비
        Act: clean_stock_name 호출
        Assert: 정제된 종목명이 기대값과 일치하는지 확인
        """
        assert clean_stock_name(input_name) == expected


class TestIsSpacStock:
    """is_spac_stock 함수 테스트"""

    @pytest.mark.parametrize("stock_name, expected", [
        ("테스트스팩", True),      # 스팩 포함
        ("ABC스팩1호", True),      # 스팩 포함
        ("삼성전자", False),       # 일반 종목
        ("SK하이닉스", False),     # 일반 종목
        ("SPAC", False),           # 영어 SPAC (현재 로직상 False)
    ])
    def test_is_spac_stock(self, stock_name, expected):
        """
        종목명에 '스팩'이 포함되어 있는지 여부를 테스트합니다.

        Arrange: 종목명(stock_name)과 기대하는 결과(expected) 준비
        Act: is_spac_stock 호출
        Assert: 반환값이 기대값과 일치하는지 확인
        """
        assert is_spac_stock(stock_name) is expected


class TestFormatCompetitionRate:
    """format_competition_rate 함수 테스트"""

    @pytest.mark.parametrize("rate_str, expected", [
        ("1234.56:1", "1235:1"),   # 소수점 반올림
        ("100.2:1", "100:1"),      # 소수점 버림
        ("1,234:1", "1234:1"),     # 쉼표 제거
        ("500:1", "500:1"),        # 정상 포맷
        ("99.5:1", "100:1"),       # 반올림
        ("99.4:1", "99:1"),        # 반올림
        ("N/A", "N/A"),            # 변환 불가 (유지)
        ("미정", "미정"),          # 변환 불가 (유지)
    ])
    def test_format_competition_rate(self, rate_str, expected):
        """
        경쟁률 문자열을 표준 형식(xxx:1)으로 포맷팅하는지 테스트합니다.

        Arrange: 원본 경쟁률 문자열(rate_str)과 기대값(expected) 준비
        Act: format_competition_rate 호출
        Assert: 포맷팅된 결과가 기대값과 일치하는지 확인
        """
        assert format_competition_rate(rate_str) == expected


class TestExtractShareCount:
    """extract_share_count 함수 테스트"""

    @pytest.mark.parametrize("raw_value, expected", [
        ("10,000주", "10000"),     # 단위 '주' 포함
        ("5,000 주", "5000"),      # 단위 ' 주' 포함
        ("1,000,000주", "1000000"),# 쉼표 포함
        ("10,000", "10000"),       # 단위 없음
        ("", "0"),                 # 빈 문자열 (기본값)
        ("주", "0"),               # 숫자 없음 (기본값)
    ])
    def test_extract_share_count(self, raw_value, expected):
        """
        문자열에서 주식 수(숫자)만 추출하는지 테스트합니다.

        Arrange: 원본 문자열(raw_value)과 기대값(expected) 준비
        Act: extract_share_count 호출
        Assert: 추출된 숫자가 기대값과 일치하는지 확인
        """
        assert extract_share_count(raw_value) == expected

    def test_extract_share_count_custom_default(self):
        """
        빈 문자열 입력 시 커스텀 기본값을 반환하는지 테스트합니다.

        Arrange: 빈 문자열과 커스텀 기본값 준비
        Act: extract_share_count 호출
        Assert: 커스텀 기본값 반환 확인
        """
        assert extract_share_count("", default="N/A") == "N/A"


class TestCleanTradableValues:
    """clean_tradable_values 함수 테스트"""

    @pytest.mark.parametrize("count_in, percent_in, expected_count, expected_percent", [
        ("10000", "50%", "10000", "50%"),      # 정상 케이스
        ("-", "", "N/A", "N/A"),               # 빈 값/하이픈 -> N/A
        ("　", "S", "N/A", "N/A"),             # 특수문자 -> N/A
        ("50%", "10000", "10000", "50%"),      # 순서 바뀜 -> 교정
        ("10000", "50%", "10000", "50%"),      # 순서 정상 -> 유지
    ])
    def test_clean_tradable_values(self, count_in, percent_in, expected_count, expected_percent):
        """
        유통가능물량(주식수, 지분율)을 정제하고 검증하는지 테스트합니다.

        Arrange: 입력 주식수/지분율과 기대되는 주식수/지분율 준비
        Act: clean_tradable_values 호출
        Assert: 정제된 결과가 기대값과 일치하는지 확인
        """
        count_out, percent_out = clean_tradable_values(count_in, percent_in)
        assert count_out == expected_count
        assert percent_out == expected_percent
