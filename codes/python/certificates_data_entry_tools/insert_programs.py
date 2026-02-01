import argparse
import os
import pandas as pd
import re
from slugify import slugify
from typing import List, Dict, Set, Tuple, Optional, TypedDict

# Local module imports
from config import (
    DB_CONFIG,
    NEW_PROGRAM_LIST,
    RULES,
    CATEGORY_IDS,
    OUTPUT_DIR,
    OUTPUT_FILE,
)
from database import DatabaseManager

# --- TypedDict for Structured Data ---


class ProgramReportItem(TypedDict):
    """Represents a single item in the program processing report."""

    program_name: str
    status: str
    predicted_category: str
    predicted_category_id: Optional[int]  # Can be None if uncategorized
    action: str
    slug: str


# --- Core Logic Functions ---


def predict_category(
    program_name_normalized: str, rules: Dict[str, List[str]]
) -> Tuple[str, Optional[int]]:
    """
    Predicts the category for a given program name based on keyword rules.

    Args:
        program_name_normalized: The lowercase, stripped program name.
        rules: A dictionary mapping category names to lists of keywords.

    Returns:
        A tuple containing the predicted category name and its ID (or None if uncategorized).
    """
    for category, keywords in rules.items():
        if any(
            re.search(rf"\b{re.escape(keyword)}\b", program_name_normalized)
            for keyword in keywords
        ):
            return category, CATEGORY_IDS.get(category)
    return "Uncategorized", None


def process_programs(
    new_programs: List[str],
    existing_programs: Set[str],
    rules: Dict[str, List[str]],
    category_ids: Dict[str, int],
) -> List[ProgramReportItem]:
    """
    Processes a list of new programs against existing ones and categorizes them.

    Args:
        new_programs: A list of new program names to process.
        existing_programs: A set of existing program names (lowercase).
        rules: Categorization rules.
        category_ids: Mapping of category names to IDs.

    Returns:
        A list of ProgramReportItem dictionaries with processing details.
    """
    report_data: List[ProgramReportItem] = []
    for program_name in new_programs:
        normalized_name = program_name.strip().lower()
        status = "Exists"
        predicted_category_name = "N/A"
        predicted_category_id_val: Optional[int] = None  # Use None for type consistency
        action = "Skip"

        if normalized_name not in existing_programs:
            status = "New"
            action = "Insert"
            predicted_category_name, predicted_category_id_val = predict_category(
                normalized_name, rules
            )
            # If still uncategorized after prediction, ensure ID is None
            if predicted_category_name == "Uncategorized":
                predicted_category_id_val = None

        # For display purposes, if it's "Exists", use "N/A" for category fields
        if status == "Exists":
            final_pred_cat_id: Optional[int] = (
                None  # To satisfy TypedDict, will be displayed as "N/A"
            )
        else:
            final_pred_cat_id = predicted_category_id_val

        report_data.append(
            ProgramReportItem(
                program_name=program_name,
                status=status,
                predicted_category=predicted_category_name,
                predicted_category_id=final_pred_cat_id,
                action=action,
                slug=slugify(program_name.strip()),
            )
        )
    return report_data


# --- Output Generation Functions ---


def generate_dry_run_report(report_data: List[ProgramReportItem]) -> str:
    """
    Generates a markdown-formatted string for the dry-run report.

    Args:
        report_data: A list of ProgramReportItem dictionaries.

    Returns:
        A markdown string representing the report.
    """
    # Convert to DataFrame for easy markdown generation
    # Need to handle Optional[int] for display, converting "N/A" or None to string
    display_data = []
    for item in report_data:
        display_item = {
            "Program Name": item["program_name"],
            "Predicted Category": item["predicted_category"],
            "Predicted Category ID": str(item["predicted_category_id"])
            if item["predicted_category_id"] is not None
            else "N/A",
            "Action": item["action"],
        }
        display_data.append(display_item)

    report_df = pd.DataFrame(display_data)
    # No need to select columns if we build display_item with the correct keys
    display_df = report_df
    # Sort so NEW items are at the top (easier to check)
    display_df.sort_values(by=["Action"], ascending=True, inplace=True)
    return display_df.to_markdown(index=False)


def generate_sql_script(
    programs_to_insert: List[ProgramReportItem], output_path_hint: str
) -> str:
    """
    Generates the SQL insert script for new programs.

    Args:
        programs_to_insert: A list of ProgramReportItem dictionaries for programs to insert.
        output_path_hint: The intended output path (used for comment, not file writing here).

    Returns:
        A string containing the full SQL script.
    """
    sql_lines = [
        "-- Generated by certificates-data-entry-tools",
        f"-- Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Output target: {output_path_hint}",
        "START TRANSACTION;",
        "",
    ]

    for p in programs_to_insert:
        if p["action"] != "Insert" or p["predicted_category_id"] is None:
            # Skip if not for insertion or if category ID is missing (e.g., uncategorized and not handled)
            # This check should ideally be done before calling this function
            continue

        sql_lines.append(
            f"-- New Program: {p['program_name']} ({p['predicted_category']})"
        )
        # Insert Program (Parent)
        sql_lines.append(
            f"INSERT INTO programs (id_category, created_at, updated_at) VALUES ({p['predicted_category_id']}, NOW(), NOW());"
        )
        # Store ID in variable for safety in bulk script
        sql_lines.append("SET @last_prog_id = LAST_INSERT_ID();")
        # Insert Translation (Child)
        clean_name = p["program_name"].replace("'", "''")  # Escape single quotes
        sql_lines.append(
            f"INSERT INTO program_translations (id_program, language_code, name, slug, description, created_at, updated_at) "
            f"VALUES (@last_prog_id, 'id', '{clean_name}', '{p['slug']}', '-', NOW(), NOW());"
        )
        sql_lines.append("")

    sql_lines.append("COMMIT;")
    return "\n".join(sql_lines)


# --- Main Execution Block ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SQL for missing programs.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be created, do not generate SQL.",
    )
    args = parser.parse_args()

    db_manager = DatabaseManager(DB_CONFIG)

    print("Fetching existing programs from the database...")
    existing_programs_set = db_manager.get_existing_program_names()

    print("Processing new program list...")
    all_report_data = process_programs(
        NEW_PROGRAM_LIST, existing_programs_set, RULES, CATEGORY_IDS
    )

    if args.dry_run:
        print("\n--- DRY RUN REPORT ---")
        report_markdown = generate_dry_run_report(all_report_data)
        print(report_markdown)
    else:
        print("Generating SQL insert statements for new programs...")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_file_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

        # Filter for programs that actually need to be inserted
        # and have a valid category ID.
        programs_to_insert = [
            p
            for p in all_report_data
            if p["action"] == "Insert" and p["predicted_category_id"] is not None
        ]

        if not programs_to_insert:
            print(
                "[INFO] No new programs to insert or all new programs are uncategorized."
            )
        else:
            sql_content = generate_sql_script(programs_to_insert, output_file_path)
            with open(output_file_path, "w") as f:
                f.write(sql_content)

            print(
                f"\n[SUCCESS] SQL generated for {len(programs_to_insert)} new programs."
            )
            print(f"File saved to: {output_file_path}")
