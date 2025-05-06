import json
import os
from datetime import date
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

from database import get_home_charge
from models import (
    AttendanceRecords,
    Expense,
    ExpenseRecords,
    WorkPattern,
    WorkType,
)


def load_config(config_path: str) -> dict[str, Any]:
    """設定ファイルを読み込む"""
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def load_template(template_path: str) -> Template:
    """テンプレートファイルを読み込む"""
    dirname, filename = os.path.split(template_path)
    env = Environment(
        loader=FileSystemLoader(dirname),
    )
    template = env.get_template(filename)

    return template


def process_attendance_data(
    attendance_data: AttendanceRecords, config: dict[str, Any]
) -> ExpenseRecords:
    """勤務表データを処理し、交通費精算データを生成する"""
    grouped = attendance_data.group_by_date()

    expenses: ExpenseRecords = ExpenseRecords()

    for work_date, group in grouped.items():
        # 勤務形態に応じた処理をmatch文で分岐
        match group.get_work_pattern():
            case WorkPattern.ONSITE:
                # 各オンサイト勤務に対して交通費を生成
                onsite_rows: AttendanceRecords = group.filter_by_work_type(
                    [
                        WorkType.CUSTOMER_ONSITE,
                        WorkType.INHOUSE_ONSITE,
                    ]
                )
                onsite_expenses: ExpenseRecords = _create_onsite_expenses(
                    work_date,
                    onsite_rows,
                    config,
                )
                expenses.extend(onsite_expenses)

            case WorkPattern.OFFSITE:
                # オフサイト勤務（在宅）
                offsite_expense: ExpenseRecords = _create_home_charge_expense(
                    work_date,
                    config,
                )
                expenses.extend(offsite_expense)

            case WorkPattern.HOLIDAY:
                # 休日等、出力対象外
                pass

    return expenses


def _find_location(memo: str | None, config: dict[str, Any]) -> dict[str, Any]:
    """メモ欄から顧客識別子を特定し、対応する交通費情報を返す"""
    if not memo:
        return config["transportation"]["customer"]["default"]

    # 最長一致ルールを適用
    matched_location: dict[str, Any] | None = None
    max_length: int = 0

    for location_id, location_data in config["transportation"]["customer"]["locations"].items():
        if location_id in memo and len(location_id) > max_length:
            matched_location = location_data
            max_length = len(location_id)

    return matched_location if matched_location else config["transportation"]["customer"]["default"]


def _create_onsite_expenses(
    work_date: date, onsite_rows: AttendanceRecords, config: dict[str, Any]
) -> ExpenseRecords:
    """オンサイト勤務（会社または顧客先）の交通費データを作成"""
    expenses: ExpenseRecords = ExpenseRecords()

    for attendance in onsite_rows.attendances:
        work_type = attendance.work_type

        match work_type:
            case WorkType.CUSTOMER_ONSITE:
                location_config = _find_location(attendance.memo, config)
                reason = "顧客先交通費"
            case WorkType.INHOUSE_ONSITE:
                location_config = config["transportation"]["company"]
                reason = "通勤費(通常勤務地)"

        expense_data = {
            "日付": work_date,
            "出発": location_config["departure"],
            "到着": location_config["destination"],
            "往復": "往復",
            "金額/Km": location_config["amount"],
            "客先請求": "なし",
            "申請理由": reason,
            "交通機関": "電車",
            "備考": "",
        }
        expenses.append(Expense(**expense_data))

    return expenses


def _create_home_charge_expense(work_date: date, config: dict[str, Any]) -> ExpenseRecords:
    """在宅チャージのデータを作成"""
    expenses: ExpenseRecords = ExpenseRecords()
    home_charge = get_home_charge()
    expense_data = {
        "日付": work_date,
        "出発": "",
        "到着": "",
        "往復": "--",
        "金額/Km": home_charge.amount,
        "客先請求": "なし",
        "申請理由": "在宅チャージ",
        "交通機関": "",
        "備考": "",
    }
    expenses.append(Expense(**expense_data))

    return expenses
