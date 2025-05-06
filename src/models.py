import csv
import io
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_serializer, field_validator


class WorkType(Enum):
    CUSTOMER_ONSITE = "01"
    CUSTOMER_OFFSITE = "02"
    INHOUSE_ONSITE = "10"
    INHOUSE_OFFSITE = "11"
    ABSENCE = "03"
    PAID_HOLIDAY = "04"
    PAID_HOLIDAY_HALF = "05"
    COMPENSATORY_HOLIDAY = "06"
    SUMMER_VACATION = "08"
    SPECIAL_LEAVE = "09"
    BLANK = ""


class WorkPattern(Enum):
    ONSITE = "onsite"
    OFFSITE = "offsite"
    HOLIDAY = "holiday"


class Attendance(BaseModel):
    work_date: date = Field(..., alias="年月日")
    work_type: WorkType | None = Field(alias="勤務区分")
    start_time: str | None = Field(alias="開始")
    memo: str | None = Field(alias="メモ")

    @field_validator("work_date", mode="before")
    @classmethod
    def parse_work_date(cls, value: str) -> date:
        return datetime.strptime(value, "%Y%m%d").date()


class AttendanceRecords(BaseModel):
    attendances: list[Attendance] = []

    @classmethod
    def from_tsv(cls, tsv_content: str) -> "AttendanceRecords":
        content = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
        attendances = [Attendance(**attendance) for attendance in content]
        return cls(attendances=attendances)

    def append(self, attendance: Attendance) -> None:
        """渡されたAttendanceを要素の最後に追加する"""
        self.attendances.append(attendance)

    def group_by_date(self) -> dict[date, "AttendanceRecords"]:
        """日付ごとにAttendanceをグループ化する"""
        grouped: dict[date, AttendanceRecords] = {}
        for attendance in self.attendances:
            work_date = attendance.work_date
            if work_date not in grouped:
                grouped[work_date] = AttendanceRecords()
                print(type(grouped[work_date]))
            grouped[work_date].append(attendance)

        return grouped

    def filter_by_work_type(self, work_types: list[WorkType]) -> "AttendanceRecords":
        """特定の勤務区分のAttendanceを抽出する"""
        filtered = []
        for attendance in self.attendances:
            if attendance.work_type in work_types:
                filtered.append(attendance)
        return AttendanceRecords(attendances=filtered)

    def get_work_pattern(self) -> WorkPattern:
        """勤務区分のリストから優先度の高い勤務形態を判定する"""
        # 勤務区分の値のセットを作成
        work_types = set(attendance.work_type for attendance in self.attendances)

        onsite_types = {
            WorkType.CUSTOMER_ONSITE,
            WorkType.INHOUSE_ONSITE,
        }
        if work_types & onsite_types:
            return WorkPattern.ONSITE

        offsite_types = {
            WorkType.CUSTOMER_OFFSITE,
            WorkType.INHOUSE_OFFSITE,
        }
        if work_types & offsite_types:
            return WorkPattern.OFFSITE

        return WorkPattern.HOLIDAY


class Expense(BaseModel):
    work_date: date = Field(..., alias="日付")
    departure: str = Field(..., alias="出発")
    arrival: str = Field(..., alias="到着")
    round_trip: str = Field("往復", alias="往復")
    amount: int = Field(..., alias="金額/Km")
    customer_billing: str = Field("なし", alias="客先請求")
    reason: str | None = Field(None, alias="申請理由")
    transpotation: str | None = Field("電車", alias="交通機関")
    note: str | None = Field(None, alias="備考")

    @field_serializer("work_date")
    def serialize_date(self, work_date: date) -> str:
        return work_date.strftime("%Y/%m/%d")


class ExpenseRecords(BaseModel):
    expences: list[Expense] = []

    def append(self, expense: Expense) -> None:
        """渡されたExpenseを要素の最後に追加する"""
        self.expences.append(expense)

    def extend(self, other: "ExpenseRecords") -> None:
        """渡されたExpenseRecordsを要素の最後に追加する"""
        self.expences.extend(other.expences)

    def to_csv_text(self) -> str:
        """交通費精算データをCSV形式の文字列に変換する"""
        output = io.StringIO()

        # ヘッダー行を定義
        fieldnames = [field_into.alias for field_into in Expense.model_fields.values()]

        with output:
            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames,
                lineterminator="\n",
            )
            writer.writeheader()

            for expense in self.expences:
                expense_dict = expense.model_dump(by_alias=True)
                # Mappingにキャストして型エラーを解消
                writer.writerow(expense_dict)

            text = output.getvalue()

        return text
