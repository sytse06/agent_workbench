#!/usr/bin/env python3
"""
Simple DB Scanner - Table Visibility and Management Operations
Focused tool for database table management and operations.
"""
import os
import sys
import sqlite3
from pathlib import Path


class SimpleDBScanner:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or self._get_default_db_path()

    def _get_default_db_path(self) -> str:
        """Get database path from environment or default."""
        env = os.getenv('APP_ENV', 'development')
        return f"./data/agent_workbench_{env}.db"

    def connect(self):
        """Connect to the database."""
        if not Path(self.db_path).exists():
            print(f"❌ Database not found: {self.db_path}")
            return None

        try:
            return sqlite3.connect(self.db_path)
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return None

    def show_tables(self):
        """Show all tables with row counts."""
        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            print("🗄️  Database Tables")
            print("=" * 50)
            print(f"Database: {self.db_path}")
            print()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()

            if not tables:
                print("📭 No tables found")
                return

            print("📊 Table Summary:")
            total_rows = 0

            for (table_name,) in tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                total_rows += row_count

                print(f"  📋 {table_name}: {row_count:,} rows")

            print(f"\n📈 Total rows: {total_rows:,}")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            conn.close()

    def show_table_structure(self, table_name: str):
        """Show detailed structure of a specific table."""
        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f"❌ Table '{table_name}' not found")
                return

            print(f"📋 Table Structure: {table_name}")
            print("=" * 50)

            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            print("🏗️  Columns:")
            for cid, name, type_, notnull, default_value, pk in columns:
                pk_indicator = " 🔑" if pk else ""
                null_info = "NOT NULL" if notnull else "NULL"
                default_info = f" DEFAULT {default_value}" if default_value else ""
                print(f"  {name}: {type_} {null_info}{default_info}{pk_indicator}")

            # Get row count and sample data
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"\n📊 Row count: {row_count:,}")

            if row_count > 0:
                # Show sample data (first 3 rows)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                column_names = [description[0] for description in cursor.description]

                print("\n💾 Sample data:")
                for i, row in enumerate(rows, 1):
                    print(f"  Row {i}:")
                    for col_name, value in zip(column_names, row):
                        display_value = str(value)[:50] + "..." if len(str(value)) > 50 else value
                        print(f"    {col_name}: {display_value}")
                    print()

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            conn.close()

    def query_table(self, table_name: str, limit: int = 10):
        """Query table data with limit."""
        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f"❌ Table '{table_name}' not found")
                return

            print(f"📋 Table Data: {table_name} (limit {limit})")
            print("=" * 50)

            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]

            if not rows:
                print("📭 No data found")
                return

            # Print header
            header = " | ".join(col[:15] for col in column_names)
            print(header)
            print("-" * len(header))

            # Print data
            for row in rows:
                row_str = " | ".join(str(val)[:15] if val is not None else "NULL" for val in row)
                print(row_str)

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            conn.close()

    def search_data(self, table_name: str, search_term: str, limit: int = 5):
        """Search for data in table columns."""
        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            text_columns = [col[1] for col in columns if col[2].upper() in ['TEXT', 'VARCHAR']]

            if not text_columns:
                print(f"❌ No searchable text columns in {table_name}")
                return

            print(f"🔎 Searching '{search_term}' in {table_name}")
            print("=" * 50)

            # Build search query
            where_clauses = [f"{col} LIKE ?" for col in text_columns]
            where_clause = " OR ".join(where_clauses)
            search_params = [f"%{search_term}%" for _ in text_columns]

            query = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT {limit}"
            cursor.execute(query, search_params)

            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]

            if not rows:
                print("📭 No matches found")
                return

            print(f"Found {len(rows)} matches:")
            for i, row in enumerate(rows, 1):
                print(f"\nResult {i}:")
                for col_name, value in zip(column_names, row):
                    if value and search_term.lower() in str(value).lower():
                        print(f"  {col_name}: {value} ⭐")
                    else:
                        display_value = str(value)[:50] + "..." if len(str(value)) > 50 else value
                        print(f"  {col_name}: {display_value}")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            conn.close()

    def show_recent_activity(self, table_name: str = None, limit: int = 5):
        """Show recent activity (assumes created_at or similar timestamp column)."""
        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            if table_name:
                tables = [(table_name,)]
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if not cursor.fetchone():
                    print(f"❌ Table '{table_name}' not found")
                    return
            else:
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                tables = cursor.fetchall()

            print("⏰ Recent Activity")
            print("=" * 50)

            for (table_name,) in tables:
                # Look for timestamp columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                timestamp_cols = [col[1] for col in columns
                                if any(time_word in col[1].lower()
                                      for time_word in ['created_at', 'updated_at', 'timestamp', 'date'])]

                if timestamp_cols:
                    timestamp_col = timestamp_cols[0]  # Use first timestamp column
                    cursor.execute(f"SELECT * FROM {table_name} ORDER BY {timestamp_col} DESC LIMIT {limit}")
                    rows = cursor.fetchall()
                    column_names = [description[0] for description in cursor.description]

                    if rows:
                        print(f"\n📋 {table_name} (recent {len(rows)}):")
                        for row in rows:
                            timestamp_value = row[column_names.index(timestamp_col)]
                            print(f"  {timestamp_value} - ID: {row[0] if row else 'N/A'}")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            conn.close()

    def run_sql(self, sql_query: str):
        """Execute custom SQL query."""
        conn = self.connect()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            print(f"🔍 SQL Query: {sql_query}")
            print("=" * 50)

            cursor.execute(sql_query)

            # Handle SELECT queries
            if sql_query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                column_names = [description[0] for description in cursor.description]

                if not rows:
                    print("📭 No results found")
                    return

                # Print header
                header = " | ".join(col[:15] for col in column_names)
                print(header)
                print("-" * len(header))

                # Print data
                for row in rows:
                    row_str = " | ".join(str(val)[:15] if val is not None else "NULL" for val in row)
                    print(row_str)

                print(f"\n📊 {len(rows)} row(s) returned")
            else:
                # Handle non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                conn.commit()
                print(f"✅ Query executed successfully")
                if cursor.rowcount > 0:
                    print(f"📊 {cursor.rowcount} row(s) affected")

        except Exception as e:
            print(f"❌ SQL Error: {e}")
        finally:
            conn.close()


def main():
    """Command line interface."""
    if len(sys.argv) < 2:
        print("Simple DB Scanner - Table Visibility and Management")
        print("Usage:")
        print("  python simple_db_scanner.py tables                    # Show all tables")
        print("  python simple_db_scanner.py structure <table>         # Show table structure")
        print("  python simple_db_scanner.py query <table> [limit]     # Query table data")
        print("  python simple_db_scanner.py search <table> <term>     # Search in table")
        print("  python simple_db_scanner.py recent [table]            # Show recent activity")
        print("  python simple_db_scanner.py sql \"<query>\"             # Execute custom SQL")
        return

    scanner = SimpleDBScanner()
    command = sys.argv[1]

    if command == "tables":
        scanner.show_tables()

    elif command == "structure" and len(sys.argv) > 2:
        scanner.show_table_structure(sys.argv[2])

    elif command == "query" and len(sys.argv) > 2:
        table = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        scanner.query_table(table, limit)

    elif command == "search" and len(sys.argv) > 3:
        table = sys.argv[2]
        term = sys.argv[3]
        scanner.search_data(table, term)

    elif command == "recent":
        table = sys.argv[2] if len(sys.argv) > 2 else None
        scanner.show_recent_activity(table)

    elif command == "sql" and len(sys.argv) > 2:
        sql_query = sys.argv[2]
        scanner.run_sql(sql_query)

    else:
        print("❌ Invalid command or missing arguments")


if __name__ == "__main__":
    main()