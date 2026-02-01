import argparse
import csv
import os
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional, TypedDict

# Local module imports
from config import DB_CONFIG, OUTPUT_DIR, SCHEDULES_INPUT_FILE
from database import DatabaseManager

# Configuration
INPUT_FILE = SCHEDULES_INPUT_FILE
OUTPUT_FILE = "insert_schedules.sql"

# Indonesian month mapping
INDONESIAN_MONTHS: Dict[str, str] = {
    "januari": "January",
    "februari": "February",
    "maret": "March",
    "april": "April",
    "mei": "May",
    "juni": "June",
    "juli": "July",
    "agustus": "August",
    "september": "September",
    "oktober": "October",
    "november": "November",
    "desember": "December",
}


# --- TypedDict for Structured Data ---


class ScheduleReportItem(TypedDict):
    """Represents a single item in the schedule processing report."""

    program_name: str
    start_date: str
    end_date: str
    program_id: Optional[int]
    category_id: Optional[int]
    status: str
    action: str


# --- Core Logic Functions ---


def parse_indonesian_date(date_str: str) -> Optional[str]:
    """
    Parses a date string in Indonesian format to YYYY-MM-DD format.

    Args:
        date_str: Date string in Indonesian format (e.g., "31 Desember 2024")

    Returns:
        Date string in YYYY-MM-DD format or None if parsing fails
    """
    if not date_str:
        return None

    # Convert to lowercase and replace Indonesian month names
    date_str_lower: str = date_str.lower()

    for ind_month, eng_month in INDONESIAN_MONTHS.items():
        if ind_month in date_str_lower:
            date_str_lower = date_str_lower.replace(ind_month, eng_month)
            break

    try:
        # Parse the date and format it as YYYY-MM-DD
        date_obj: datetime = datetime.strptime(date_str_lower, "%d %B %Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        # Try parsing with English month names directly
        try:
            date_obj: datetime = datetime.strptime(date_str, "%d %B %Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            print(f"Warning: Could not parse date: {date_str}")
            return None


def normalize_program_name(program_name: str) -> str:
    """
    Normalizes program names using the PROGRAM_NAME_MAP.

    Args:
        program_name: Original program name

    Returns:
        Normalized program name
    """
    if not program_name:
        return ""

    return program_name


def process_csv_data(file_path: str) -> List[Dict[str, str]]:
    """
    Processes the CSV file and extracts relevant data.

    Args:
        file_path: Path to the CSV file

    Returns:
        List of dictionaries containing processed data
    """
    data: List[Dict[str, str]] = []

    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Extract relevant columns
            program_name: str = row.get("Program", "").strip()
            start_date: str = row.get("Tanggal Mulai", "").strip()
            end_date: str = row.get("Tanggal Sertifikat", "").strip()

            if program_name and start_date and end_date:
                data.append(
                    {
                        "program": program_name,
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                )

    return data


def group_csv_data(data: List[Dict[str, str]]) -> Dict[Tuple[str, str], Dict[str, str]]:
    """
    Groups CSV data by program name and start date.

    Args:
        data: List of dictionaries containing processed data

    Returns:
        Dictionary with (program_name, start_date) as keys and data as values
    """
    grouped_data: Dict[Tuple[str, str], Dict[str, str]] = {}

    for item in data:
        key: Tuple[str, str] = (item["program"], item["start_date"])
        if key not in grouped_data:
            grouped_data[key] = item

    return grouped_data


def process_schedules(
    grouped_data: Dict[Tuple[str, str], Dict[str, str]],
    programs_data: Dict[str, Dict[str, int]],
    existing_schedules: Set[Tuple[int, str]],
) -> List[ScheduleReportItem]:
    """
    Processes grouped schedule data against existing programs and schedules.

    Args:
        grouped_data: Grouped CSV data
        programs_data: Program data from database
        existing_schedules: Set of existing schedules

    Returns:
        A list of ScheduleReportItem dictionaries with processing details
    """
    report_data: List[ScheduleReportItem] = []

    for (program_name, start_date_str), item in grouped_data.items():
        # Normalize program name
        normalized_name: str = normalize_program_name(program_name)
        program_key: str = normalized_name.lower()

        # Initialize with default values
        status: str = "Error"
        action: str = "Skip"
        program_id: Optional[int] = None
        category_id: Optional[int] = None

        # Parse dates
        start_date: Optional[str] = parse_indonesian_date(start_date_str)
        end_date: Optional[str] = parse_indonesian_date(item["end_date"])

        if not start_date or not end_date:
            status = "Invalid Date"
            action = "Skip"
        elif program_key not in programs_data:
            status = "Program Not Found"
            action = "Skip"
        else:
            program_info: Dict[str, int] = programs_data[program_key]
            program_id = program_info["id"]
            category_id = program_info["cat_id"]

            # Check if schedule already exists
            if (program_id, start_date) in existing_schedules:
                status = "Exists"
                action = "Skip"
            else:
                status = "New"
                action = "Insert"

        report_data.append(
            ScheduleReportItem(
                program_name=normalized_name,
                start_date=start_date or "",
                end_date=end_date or "",
                program_id=program_id,
                category_id=category_id,
                status=status,
                action=action,
            )
        )

    return report_data


# --- Output Generation Functions ---


def generate_dry_run_report(report_data: List[ScheduleReportItem]) -> str:
    """
    Generates a markdown-formatted string for the dry-run report.

    Args:
        report_data: A list of ScheduleReportItem dictionaries.

    Returns:
        A markdown string representing the report.
    """
    # Convert to list of dictionaries for markdown generation
    display_data: List[Dict[str, str]] = []
    for item in report_data:
        display_item: Dict[str, str] = {
            "Program Name": item["program_name"],
            "Start Date": item["start_date"],
            "End Date": item["end_date"],
            "Program ID": str(item["program_id"])
            if item["program_id"] is not None
            else "N/A",
            "Category ID": str(item["category_id"])
            if item["category_id"] is not None
            else "N/A",
            "Status": item["status"],
            "Action": item["action"],
        }
        display_data.append(display_item)

    # Import here to avoid dependency if not using pandas
    try:
        import pandas as pd

        report_df = pd.DataFrame(display_data)
        # Sort so Insert items are at the top (easier to check)
        report_df.sort_values(by=["Action"], ascending=True, inplace=True)
        return report_df.to_markdown(index=False)
    except ImportError:
        # Fallback if pandas is not available
        header: str = "| Program Name | Start Date | End Date | Program ID | Category ID | Status | Action |"
        separator: str = (
            "|"
            + "|".join(["-" * (len(col) - 2) for col in header.split("|")[1:-1]])
            + "|"
        )

        lines: List[str] = [header, separator]
        for item in display_data:
            row: str = "| {} | {} | {} | {} | {} | {} | {} |".format(
                item["Program Name"],
                item["Start Date"],
                item["End Date"],
                item["Program ID"],
                item["Category ID"],
                item["Status"],
                item["Action"],
            )
            lines.append(row)

        return "\n".join(lines)


def generate_sql_script(
    schedules_to_insert: List[ScheduleReportItem], output_path_hint: str
) -> str:
    """
    Generates the SQL insert script for new schedules.

    Args:
        schedules_to_insert: A list of ScheduleReportItem dictionaries for schedules to insert.
        output_path_hint: The intended output path (used for comment, not file writing here).

    Returns:
        A string containing the full SQL script.
    """
    sql_lines: List[str] = [
        "-- Generated by certificates-data-entry-tools",
        f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Output target: {output_path_hint}",
        "START TRANSACTION;",
        "",
    ]

    for s in schedules_to_insert:
        if s["action"] != "Insert":
            continue

        sql_lines.append(
            f"-- New Schedule: {s['program_name']} ({s['start_date']} to {s['end_date']})"
        )

        sql_lines.append(
            f"INSERT INTO schedules (id_program, id_category, date_start, date_end, time_start, time_end, created_at, updated_at) "
            f"VALUES ({s['program_id']}, {s['category_id']}, '{s['start_date']}', '{s['end_date']}', NULL, NULL, NOW(), NOW());"
        )
        sql_lines.append("")

    sql_lines.append("COMMIT;")
    return "\n".join(sql_lines)


# --- Main Execution Block ---

if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generate SQL for missing schedules."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be created, do not generate SQL.",
    )
    args: argparse.Namespace = parser.parse_args()

    db_manager: DatabaseManager = DatabaseManager(DB_CONFIG)

    print("Fetching programs data from database...")
    programs_data: Dict[str, Dict[str, int]] = db_manager.get_programs_data()
    print(f"Found {len(programs_data)} programs in database")

    print("Fetching existing schedules from database...")
    existing_schedules: Set[Tuple[int, str]] = db_manager.get_existing_schedules()
    print(f"Found {len(existing_schedules)} existing schedules")

    print(f"Processing CSV file: {INPUT_FILE}")
    csv_data: List[Dict[str, str]] = process_csv_data(INPUT_FILE)
    print(f"Processed {len(csv_data)} rows from CSV")

    # Group CSV data
    grouped_data: Dict[Tuple[str, str], Dict[str, str]] = group_csv_data(csv_data)
    print(f"Grouped into {len(grouped_data)} unique schedules")

    print("Processing schedules...")
    all_report_data: List[ScheduleReportItem] = process_schedules(
        grouped_data, programs_data, existing_schedules
    )

    if args.dry_run:
        print("\n--- DRY RUN REPORT ---")
        report_markdown: str = generate_dry_run_report(all_report_data)
        print(report_markdown)
    else:
        print("Generating SQL insert statements for new schedules...")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_file_path: str = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

        # Filter for schedules that actually need to be inserted
        schedules_to_insert: List[ScheduleReportItem] = [
            s for s in all_report_data if s["action"] == "Insert"
        ]

        if not schedules_to_insert:
            print("[INFO] No new schedules to insert.")
        else:
            sql_content: str = generate_sql_script(
                schedules_to_insert, output_file_path
            )
            with open(output_file_path, "w") as f:
                f.write(sql_content)

            print(
                f"\n[SUCCESS] SQL generated for {len(schedules_to_insert)} new schedules."
            )
            print(f"File saved to: {output_file_path}")
