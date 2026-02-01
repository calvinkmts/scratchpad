# Certificates Data Entry Tools

A Python toolset for managing certificate program data, including programs, schedules, and participants. This toolset helps automate the process of inserting data into a database from CSV files and program lists.

## Features

- **Program Management**: Add new training programs to the database with automatic categorization
- **Schedule Management**: Import program schedules from CSV files with Indonesian date parsing
- **Participant Management**: Import participants and generate certificate records
- **Duplicate Prevention**: Checks for existing records to prevent duplicates
- **Dry Run Mode**: Preview changes before executing SQL statements
- **Automatic SQL Generation**: Creates SQL scripts for database insertion

## Prerequisites

- Python 3.13 or higher
- MySQL database
- Required Python packages (see [Installation](#installation))

## Installation

1. Clone this repository:

   ```bash
   git clone <repository-url>
   cd certificates-data-entry-tools
   ```

2. Install dependencies using uv:

   ```bash
   uv sync
   ```

   Or using pip:

   ```bash
   pip install -r requirements.txt  # If you create a requirements.txt file
   ```

## Configuration

Before using the tools, you need to configure the database connection and other settings in [`config.py`](config.py:1):

### Database Configuration

Update the `DB_CONFIG` dictionary with your database connection details:

```python
DB_CONFIG: Dict[str, Any] = {
    "host": "localhost",
    "port": 33061,
    "user": "user",
    "password": "password",
    "database": "laravel",
}
```

### Program Categories

The tool uses predefined categories for programs. You can modify the `CATEGORY_IDS` dictionary:

```python
CATEGORY_IDS: Dict[str, int] = {
    "Engineering": 1,
    "Accounting": 2,
    "Construction": 3,
    # ... more categories
}
```

### Adding New Programs

To add new programs, update the `NEW_PROGRAM_LIST` in [`config.py`](config.py:38):

```python
NEW_PROGRAM_LIST: List[str] = [
    "Training SAP 2000: Analisa Struktur & Desain",
    "Training CMA",
    # ... more programs
]
```

### Categorization Rules

The tool automatically categorizes programs based on keywords. You can customize these rules in the `RULES` dictionary:

```python
RULES: Dict[str, List[str]] = {
    "Construction": ["sap 2000"],
    "Engineering": ["plc"],
    # ... more rules
}
```

## Usage

### 1. Managing Programs

Use [`insert_programs.py`](insert_programs.py:1) to add new programs to the database:

```bash
# Preview what would be inserted (dry run)
python insert_programs.py --dry-run

# Generate SQL for new programs
python insert_programs.py
```

This will:

- Check which programs from `NEW_PROGRAM_LIST` don't exist in the database
- Predict categories for new programs based on rules
- Generate SQL statements in `out/insert_programs.sql`

### 2. Managing Schedules

Use [`insert_schedules.py`](insert_schedules.py:1) to import program schedules from a CSV file:

```bash
# Preview what would be inserted (dry run)
python insert_schedules.py --dry-run

# Generate SQL for new schedules
python insert_schedules.py
```

This will:

- Read schedule data from the CSV file specified in `SCHEDULES_INPUT_FILE`
- Parse Indonesian date formats (e.g., "31 Desember 2024")
- Match programs with existing database records
- Generate SQL statements in `out/insert_schedules.sql`

#### CSV Format for Schedules

The CSV file should contain the following columns:

- `Program`: Program name
- `Tanggal Mulai`: Start date in Indonesian format (e.g., "31 Desember 2024")
- `Tanggal Sertifikat`: Certificate issue date in Indonesian format

Example:

```csv
Program,Tanggal Mulai,Tanggal Sertifikat
Training SAP 2000,31 Desember 2024,31 Desember 2024
Training CMA,15 Januari 2025,15 Januari 2025
```

### 3. Managing Participants

Use [`insert_participants.py`](insert_participants.py:1) to import participants and generate certificate records:

```bash
# Preview what would be inserted (dry run)
python insert_participants.py --dry-run

# Generate SQL for new participants
python insert_participants.py
```

This will:

- Read participant data from the CSV file specified in `SCHEDULES_INPUT_FILE`
- Match participants with existing programs and schedules
- Generate SQL statements for both participants and certificates in `out/insert_participants.sql`

#### CSV Format for Participants

The CSV file should contain the following columns:

- `Nama`: Participant name
- `Program`: Program name
- `Tanggal Mulai`: Schedule start date in Indonesian format
- `No`: Certificate reference number prefix
- `ket`: Certificate reference number suffix
- `Tanggal Sertifikat`: Certificate issue date in Indonesian format

Example:

```csv
Nama,Program,Tanggal Mulai,ket,Tanggal Sertifikat
John Doe,Training SAP 2000,31 Desember 2024,001,31 Desember 2024
Jane Smith,Training CMA,15 Januari 2025,002,15 Januari 2025
```

## Database Schema

The tools work with the following database tables:

- `programs`: Stores program information (id, id_category, created_at, updated_at)
- `program_translations`: Stores program translations (id_program, language_code, name, slug, description, created_at, updated_at)
- `schedules`: Stores program schedules (id, id_program, id_category, date_start, date_end, time_start, time_end, created_at, updated_at)
- `participants`: Stores participant information (id_schedule, id_program, id_category, name, created_at)
- `certificates`: Stores certificate information (id_participant, reference_number, nama_program, issued_at, created_at)

## Output

All generated SQL files are saved in the `out/` directory:

- `insert_programs.sql`: SQL for inserting new programs
- `insert_schedules.sql`: SQL for inserting new schedules
- `insert_participants.sql`: SQL for inserting participants and certificates

## Error Handling

The tools include error handling for:

- Invalid date formats
- Missing programs or schedules
- Database connection issues
- Duplicate records

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please create an issue in the repository.
