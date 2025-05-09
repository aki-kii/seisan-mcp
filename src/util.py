import json
import os
from collections.abc import Callable, Sequence
from datetime import date
from typing import Any, TypeVar

from jinja2 import Environment, FileSystemLoader, Template

from database import (
    CompanyTransportation,
    CustomerTransportation,
    HomeCharge,
)
from models import (
    AttendanceRecords,
    Expense,
    ExpenseRecords,
    WorkPattern,
    WorkType,
)

T = TypeVar("T", CompanyTransportation, CustomerTransportation)


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


def _find_location(
    memo: str | None,
    get_default: Callable[[], T],
    get_all: Callable[[], Sequence[T]],
) -> T:
    """メモ欄から自社識別子を特定し、対応する交通費情報を返す
    ただし、メモ欄と最長一致した勤務先とする
    """
    if not memo:
        return get_default()

    transportations = get_all()

    if len(transportations) == 1:
        return get_default()

    matched_location = get_default()
    max_length: int = 0

    for transportation in transportations:
        length = len(transportation.location)
        if not (transportation.location in memo and length > max_length):
            continue

        matched_location = transportation
        max_length = length

    return matched_location


def _create_onsite_expenses(
    work_date: date, onsite_rows: AttendanceRecords, config: dict[str, Any]
) -> ExpenseRecords:
    """オンサイト勤務（会社または顧客先）の交通費データを作成"""
    expenses: ExpenseRecords = ExpenseRecords()

    for attendance in onsite_rows.attendances:
        work_type = attendance.work_type

        match work_type:
            case WorkType.CUSTOMER_ONSITE:
                transportation = _find_location(
                    attendance.memo,
                    CustomerTransportation.get_default,
                    CustomerTransportation.get_all,
                )
                reason = "顧客先交通費"
            case WorkType.INHOUSE_ONSITE:
                transportation = _find_location(
                    attendance.memo,
                    CompanyTransportation.get_default,
                    CompanyTransportation.get_all,
                )
                reason = "通勤費(通常勤務地)"

        expense_data = {
            "日付": work_date,
            "出発": transportation.departure,
            "到着": transportation.destination,
            "往復": "往復",
            "金額/Km": transportation.amount,
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
    home_charge = HomeCharge.get_home_charge()
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
