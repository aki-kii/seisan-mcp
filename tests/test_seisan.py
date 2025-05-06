"""
[テスト]
勤怠データから交通費精算データを作成するツールを提供するMCPサーバー
"""

from pathlib import Path

import pytest

from server import seisan


@pytest.fixture
def data_dir() -> Path:
    """テストデータのディレクトリを返す"""
    return Path(__file__).parent / "data"


def read_file(file: Path) -> str:
    """テキスト形式でファイルを読み込む"""
    with open(file, encoding="utf-8") as f:
        text = f.read()

    return text


@pytest.mark.parametrize(
    ["attendance_file", "expected_file"],
    [
        pytest.param(
            "attendance/one_month.txt",
            "expense/one_month.csv",
            id="one_month",
        ),
        pytest.param(
            "attendance/offsite.txt",
            "expense/offsite.csv",
            id="offsite",
        ),
        pytest.param(
            "attendance/onsite.txt",
            "expense/onsite.csv",
            id="onsite",
        ),
        pytest.param(
            "attendance/mixed.txt",
            "expense/mixed.csv",
            id="mixed",
        ),
        pytest.param(
            "attendance/holidays.txt",
            "expense/holidays.csv",
            id="holidays",
        ),
        pytest.param(
            "attendance/multiple_onsite.txt",
            "expense/multiple_onsite.csv",
            id="multiple_onsite",
        ),
        pytest.param(
            "attendance/overnight_offsite.txt",
            "expense/overnight_offsite.csv",
            id="overnight_offsite",
        ),
        pytest.param(
            "attendance/overnight_onsite.txt",
            "expense/overnight_onsite.csv",
            id="overnight_onsite",
        ),
    ],
)
def test_seisan(
    data_dir: Path,
    attendance_file: str,
    expected_file: str,
) -> None:
    """
    期待する交通費精算データが出力されることをテスト
    """
    # ファイルパスを生成
    attendance_path = data_dir / attendance_file
    expected_path = data_dir / expected_file
    config_path = data_dir / "test_config.json"
    prompt_path = data_dir / "prompt/expense.j2"

    # ファイルからテキストを読み込む
    input_text = read_file(attendance_path)

    # テスト対象の呼び出し
    actual: str = seisan(
        input_text=input_text,
        config_path=config_path,
        prompt_path=prompt_path,
    )

    # 期待される出力ファイルを読み込む
    expected = read_file(expected_path)

    assert actual == expected


def test_template(data_dir: Path) -> None:
    """
    テンプレートが利用できていることをテスト
    """
    # ファイルパスを生成
    attendance_path = data_dir / "attendance/template.txt"
    expected_path = data_dir / "expense/template.txt"
    config_path = data_dir / "test_config.json"
    prompt_path = data_dir / "prompt/template.j2"

    # ファイルからテキストを読み込む
    with open(attendance_path, encoding="utf-8") as f:
        input_text = f.read()

    # テスト対象の呼び出し
    actual: str = seisan(
        input_text=input_text,
        config_path=config_path,
        prompt_path=prompt_path,
    )

    # 期待される出力ファイルを読み込む
    expected = read_file(expected_path)

    assert actual == expected
