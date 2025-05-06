from typing import Any

from jinja2 import Template
from mcp.server.fastmcp import FastMCP

from models import AttendanceRecords, ExpenseRecords
from util import load_config, load_template, process_attendance_data

# Initialize FastMCP server
mcp = FastMCP(
    "seisan",
    instructions="""
    # 交通費精算データ作成くん

    このサーバーは、勤怠データを渡すと交通費精算データを作成するツールを提供します。
    勤怠データはファイルとして提供するので、このサーバーには勤怠データファイルの中身を渡してください。
    """,
)


@mcp.tool()
def seisan(
    input_text: str,
    config_path: str = "tests/data/test_config.json",
    prompt_path: str = "prompts/prompt.j2",
) -> str:
    """メイン処理"""
    # 設定ファイルを読み込む
    config: dict[str, Any] = load_config(config_path)

    # 勤務表TSVファイルを読み込む
    attendance_data: AttendanceRecords = AttendanceRecords.from_tsv(input_text)

    # 勤務表データを処理し、交通費精算データを生成
    expense_records: ExpenseRecords = process_attendance_data(attendance_data, config)
    expense_text: str = expense_records.to_csv_text()

    # 出力用プロンプトを作成
    template: Template = load_template(prompt_path)
    prompt: str = template.render(expense_records=expense_text)

    return prompt


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
