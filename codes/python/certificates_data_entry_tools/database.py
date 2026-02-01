import sqlalchemy
from sqlalchemy import create_engine, text
from typing import Set, Dict, Any, Tuple, List


class DatabaseManager:
    """Manages database connections and queries for the program data entry tool."""

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initializes the DatabaseManager with database configuration.

        Args:
            db_config: A dictionary containing database connection details
                       (host, port, user, password, database).
        """
        self.engine = create_engine(
            f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

    def get_existing_program_names(self) -> Set[str]:
        """
        Fetches all existing program names from the database.

        Returns:
            A set of existing program names in lowercase for case-insensitive comparison.
        """
        with self.engine.connect() as connection:
            query = text("SELECT name FROM program_translations")
            result = connection.execute(query)
            # Store names in lowercase for consistent comparison
            return {row.name.lower() for row in result}

    def get_programs_data(self) -> Dict[str, Dict[str, int]]:
        """
        Fetches program data from the database.

        Returns:
            A dictionary mapping program names (lowercase) to their IDs and category IDs.
        """
        programs_data = {}

        with self.engine.connect() as connection:
            query = text("""
                SELECT p.id, pt.name, p.id_category
                FROM programs p
                JOIN program_translations pt ON p.id = pt.id_program
            """)
            result = connection.execute(query)

            for row in result:
                programs_data[row.name.lower()] = {
                    "id": row.id,
                    "cat_id": row.id_category,
                }

        return programs_data

    def get_existing_schedules(self) -> Set[Tuple[int, str]]:
        """
        Fetches existing schedules from the database.

        Returns:
            A set of tuples containing (program_id, date_start) for existing schedules.
        """
        existing_schedules = set()

        with self.engine.connect() as connection:
            query = text("SELECT id_program, date_start FROM schedules")
            result = connection.execute(query)

            for row in result:
                existing_schedules.add((row.id_program, str(row.date_start)))

        return existing_schedules

    def get_schedules_data(self) -> Dict[Tuple[int, str], int]:
        """
        Fetches schedule data from the database.

        Returns:
            A dictionary mapping (program_id, date_start_str) to schedule_id.
        """
        schedules_data = {}

        with self.engine.connect() as connection:
            query = text("SELECT id, id_program, date_start FROM schedules")
            result = connection.execute(query)

            for row in result:
                schedules_data[(row.id_program, str(row.date_start))] = row.id

        return schedules_data

    def get_participants_data(self) -> List[Dict[str, Any]]:
        """
        Fetches participant data from the database.

        Returns:
            A list of dictionaries, where each dictionary represents a participant
            with 'id_schedule' and 'name'.
        """
        participants_data = []

        with self.engine.connect() as connection:
            query = text("SELECT id_schedule, name FROM participants")
            result = connection.execute(query)

            for row in result:
                participants_data.append(
                    {
                        "id_schedule": row.id_schedule,
                        "name": row.name,
                    }
                )

        return participants_data
