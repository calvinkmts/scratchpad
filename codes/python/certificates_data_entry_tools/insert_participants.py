import argparse
import csv
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional, TypedDict

# Local module imports
from config import DB_CONFIG, OUTPUT_DIR, SCHEDULES_INPUT_FILE
from database import DatabaseManager

# Configuration
INPUT_FILE = SCHEDULES_INPUT_FILE
OUTPUT_FILE = "insert_participants.sql"

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


class ParticipantReportItem(TypedDict):
    """Represents a single item in the participant processing report."""

    participant_name: str
    program_name: str
    schedule_start_date: str
    certificate_ref: str
    certificate_issue_date: str
    status: str
    action: str


# --- Core Logic Functions ---


def parse_indonesian_date(date_str: str) -> Optional[str]:
    """
    Parses an Indonesian date string into 'YYYY-MM-DD' format.

    Args:
        date_str: The date string in Indonesian format (e.g., "31 Desember 2024").

    Returns:
        The parsed date string in 'YYYY-MM-DD' format, or None if parsing fails.
    """
    if not date_str or pd.isna(date_str):
        return None

    date_str = str(date_str).strip().lower()
    parts = date_str.split()

    if len(parts) != 3:
        # Try to handle formats like "18 January 2025" which might already be in English
        try:
            dt_obj = datetime.strptime(date_str, "%d %B %Y")
            return dt_obj.strftime("%Y-%m-%d")
        except ValueError:
            return None

    day, month_ind, year = parts
    month_eng = INDONESIAN_MONTHS.get(month_ind)

    if not month_eng:
        # Month might already be in English
        try:
            dt_obj = datetime.strptime(
                f"{day} {month_ind.capitalize()} {year}", "%d %B %Y"
            )
            return dt_obj.strftime("%Y-%m-%d")
        except ValueError:
            return None

    try:
        dt_obj = datetime.strptime(f"{day} {month_eng} {year}", "%d %B %Y")
        return dt_obj.strftime("%Y-%m-%d")
    except ValueError:
        return None


def load_programs_map(db_manager: DatabaseManager) -> Dict[str, Dict[str, int]]:
    """
    Loads program data from the database into a dictionary for lookup.

    Args:
        db_manager: An instance of DatabaseManager.

    Returns:
        A dictionary mapping program names (lowercase) to their IDs and category IDs.
        Format: {"program_name_lower": {"id": program_id, "cat_id": category_id}}
    """
    programs_map = {}
    programs_data = db_manager.get_programs_data()
    for name_lower, data in programs_data.items():
        programs_map[name_lower] = {
            "id": data["id"],
            "cat_id": data["cat_id"],
        }
    return programs_map


def load_schedules_map(db_manager: DatabaseManager) -> Dict[Tuple[int, str], int]:
    """
    Loads schedule data from the database into a dictionary for lookup.

    Args:
        db_manager: An instance of DatabaseManager.

    Returns:
        A dictionary mapping (program_id, start_date_str) to schedule_id.
        Format: {(program_id, "YYYY-MM-DD"): schedule_id}
    """
    schedules_map = {}
    schedules_data = db_manager.get_schedules_data()
    for (program_id, date_start_str), schedule_id in schedules_data.items():
        schedules_map[(program_id, date_start_str)] = schedule_id
    return schedules_map


def load_existing_participants(db_manager: DatabaseManager) -> Set[Tuple[int, str]]:
    """
    Loads existing participants from the database to prevent duplicate inserts.

    Args:
        db_manager: An instance of DatabaseManager.

    Returns:
        A set of tuples (id_schedule, name_lower) for existing participants.
    """
    existing_participants = set()
    participants_data = db_manager.get_participants_data()
    for participant in participants_data:
        existing_participants.add(
            (participant["id_schedule"], participant["name"].lower())
        )
    return existing_participants


def generate_sql(
    df: pd.DataFrame,
    programs_map: Dict[str, Dict[str, int]],
    schedules_map: Dict[Tuple[int, str], int],
    existing_participants: Set[Tuple[int, str]],
) -> Tuple[str, List[ParticipantReportItem]]:
    """
    Generates SQL INSERT statements for participants and certificates.

    Args:
        df: The DataFrame containing participant data from the CSV.
        programs_map: A dictionary for program lookups.
        schedules_map: A dictionary for schedule lookups.
        existing_participants: A set of existing participants to check for duplicates.

    Returns:
        A tuple containing the generated SQL string and a list of report items.
    """
    sql_statements = ["START TRANSACTION;"]
    report: List[ParticipantReportItem] = []
    processed_count = 0
    inserted_count = 0
    skipped_count = 0
    not_found_count = 0

    for _, row in df.iterrows():
        processed_count += 1
        participant_name = str(row["Nama"]).strip()
        program_name = str(row["Program"]).strip()
        schedule_start_date_str = parse_indonesian_date(row["Tanggal Mulai"])
        no_value = str(row["No"]).strip()
        ket_value = str(row["ket"]).strip()
        # Combine No and ket to form the complete certificate reference number
        certificate_ref = (
            f"{no_value}{ket_value}" if no_value and ket_value else ket_value
        )
        certificate_issue_date_str = parse_indonesian_date(row["Tanggal Sertifikat"])

        report_item: ParticipantReportItem = {
            "participant_name": participant_name,
            "program_name": program_name,
            "schedule_start_date": schedule_start_date_str or "N/A",
            "certificate_ref": certificate_ref,
            "certificate_issue_date": certificate_issue_date_str or "N/A",
            "status": "Pending",
            "action": "N/A",
        }

        if not schedule_start_date_str:
            report_item["status"] = "Skipped"
            report_item["action"] = "Invalid schedule start date"
            report.append(report_item)
            skipped_count += 1
            continue

        program_name_lower = program_name.lower()
        program_data = programs_map.get(program_name_lower)

        if not program_data:
            report_item["status"] = "Not Found"
            report_item["action"] = "Program not found in master data"
            report.append(report_item)
            not_found_count += 1
            continue

        program_id = program_data["id"]
        category_id = program_data["cat_id"]

        schedule_key = (program_id, schedule_start_date_str)
        schedule_id = schedules_map.get(schedule_key)

        if not schedule_id:
            report_item["status"] = "Not Found"
            report_item["action"] = "Schedule not found for this program and date"
            report.append(report_item)
            not_found_count += 1
            continue

        # Check for existing participant
        if (schedule_id, participant_name.lower()) in existing_participants:
            report_item["status"] = "Skipped"
            report_item["action"] = "Participant already exists for this schedule"
            report.append(report_item)
            skipped_count += 1
            continue

        # Generate SQL for participant
        escaped_name = participant_name.replace("'", "''")
        sql_statements.append(
            f"INSERT INTO participants (id_schedule, id_program, id_category, name, created_at) "
            f"VALUES ({schedule_id}, {program_id}, {category_id}, '{escaped_name}', NOW());"
        )
        sql_statements.append("SET @last_part_id = LAST_INSERT_ID();")

        # Generate SQL for certificate
        escaped_cert_ref = certificate_ref.replace("'", "''")
        escaped_program_name = program_name.replace("'", "''")
        issued_at_sql = (
            "NULL"
            if not certificate_issue_date_str
            else f"'{certificate_issue_date_str}'"
        )

        sql_statements.append(
            f"INSERT INTO certificates (id_participant, reference_number, nama_program, issued_at, created_at) "
            f"VALUES (@last_part_id, '{escaped_cert_ref}', '{escaped_program_name}', {issued_at_sql}, NOW());"
        )

        report_item["status"] = "To Be Inserted"
        report_item["action"] = "Participant and Certificate records generated"
        report.append(report_item)
        inserted_count += 1

    sql_statements.append("COMMIT;")
    final_sql = "\n".join(sql_statements)

    # Add summary to the report
    summary_item: ParticipantReportItem = {
        "participant_name": "--- SUMMARY ---",
        "program_name": f"Processed: {processed_count}",
        "schedule_start_date": f"Inserted: {inserted_count}",
        "certificate_ref": f"Skipped: {skipped_count}",
        "certificate_issue_date": f"Not Found: {not_found_count}",
        "status": "Complete",
        "action": "SQL Generation Finished",
    }
    report.append(summary_item)

    return final_sql, report


def main():
    """
    Main function to orchestrate the participant and certificate data insertion process.
    """
    parser = argparse.ArgumentParser(
        description="Generate SQL for inserting participants and certificates."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print a summary table of actions to be taken without generating the SQL file.",
    )
    args = parser.parse_args()

    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Initialize database manager
    db_manager = DatabaseManager(DB_CONFIG)

    # Load data from CSV
    print(f"Reading data from {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
        # Ensure required columns are present
        required_cols = [
            "Nama",
            "Program",
            "Tanggal Mulai",
            "ket",
            "Tanggal Sertifikat",
        ]
        if not all(col in df.columns for col in required_cols):
            print(
                f"Error: CSV file is missing one or more required columns: {', '.join(required_cols)}"
            )
            return
    except FileNotFoundError:
        print(f"Error: Input file not found at {INPUT_FILE}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Load lookup maps
    print("Loading programs map...")
    programs_map = load_programs_map(db_manager)
    if not programs_map:
        print(
            "Warning: No programs found in the database. Participants cannot be linked."
        )
        # Decide if to proceed or exit. For now, we proceed, which will lead to "Not Found" statuses.

    print("Loading schedules map...")
    schedules_map = load_schedules_map(db_manager)
    if not schedules_map:
        print(
            "Warning: No schedules found in the database. Participants cannot be linked."
        )

    print("Loading existing participants...")
    existing_participants = load_existing_participants(db_manager)

    # Generate SQL
    print("Generating SQL statements...")
    sql_output, report = generate_sql(
        df, programs_map, schedules_map, existing_participants
    )

    if args.dry_run:
        print("\n--- Dry Run Summary ---")
        # Create a DataFrame for a nicer table display
        report_df = pd.DataFrame(report[:-1])  # Exclude the summary item for the table
        if not report_df.empty:
            # Reorder columns for better readability
            report_df = report_df[
                [
                    "participant_name",
                    "program_name",
                    "schedule_start_date",
                    "status",
                    "action",
                    "certificate_ref",
                    "certificate_issue_date",
                ]
            ]
            # Rename columns for display
            report_df.columns = [
                "Participant Name",
                "Program",
                "Schedule Start",
                "Status",
                "Action",
                "Cert. Ref.",
                "Cert. Issue Date",
            ]
            print(report_df.to_string(index=False))

        # Print the summary line
        summary_line = report[-1]
        print(
            f"\nSummary: Processed: {summary_line['program_name'].split(': ')[1]}, "
            f"Inserted: {summary_line['schedule_start_date'].split(': ')[1]}, "
            f"Skipped: {summary_line['certificate_ref'].split(': ')[1]}, "
            f"Not Found: {summary_line['certificate_issue_date'].split(': ')[1]}"
        )
    else:
        # Write SQL to file
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        print(f"Writing SQL to {output_path}...")
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(sql_output)
            print(f"Successfully generated SQL file: {output_path}")
        except IOError as e:
            print(f"Error writing SQL file: {e}")

        # Print a brief summary
        summary_line = report[-1]
        print(
            f"Generation complete. Processed: {summary_line['program_name'].split(': ')[1]}, "
            f"To Insert: {summary_line['schedule_start_date'].split(': ')[1]}, "
            f"Skipped: {summary_line['certificate_ref'].split(': ')[1]}, "
            f"Not Found: {summary_line['certificate_issue_date'].split(': ')[1]}"
        )


if __name__ == "__main__":
    main()
