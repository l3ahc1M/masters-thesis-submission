# build_db.py
import json
import sqlite3
from pathlib import Path



DB_PATH = "test_cases/dummy.db"
SCHEMA_PATH = "test_cases/db_schema.json"

# --- type mapping for SQLite ---
def sqlite_type(fmt: str) -> str:
    if fmt == "boolean":
        return "INTEGER"
    if fmt in ("uuid", "string"):
        return "TEXT"
    if fmt == "date":
        return "TEXT"  # store ISO-8601
    if fmt == "array":
        return "TEXT"  # store JSON string
    return "TEXT"

def is_boolean(fmt: str) -> bool:
    return fmt == "boolean"

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def choose_primary_key(table: dict) -> str | None:
    # Prefer the first uuid-typed column, else "ID" if present, else None (rowid table)
    for col in table["columns"]:
        if col.get("format") == "uuid":
            return col["name"]
    for col in table["columns"]:
        if col["name"] == "ID":
            return "ID"
    return None

def guess_fk_targets(tables, pk_by_table):
    """
    Build a quick lookup of table names.
    We'll add FKs for columns named SomethingUUID -> Something(UUID-PK table),
    but only when that target table exists and has a uuid primary key.
    """
    table_names = {t["name"] for t in tables}
    def resolve_target(col_name: str):
        if not col_name.endswith("UUID"):
            return None
        base = col_name[:-4]  # strip 'UUID'
        # exact table name match
        if base in table_names:
            return base
        # sometimes you get 'BankAccountContractUUID' that should map to 'BankAccountContract'
        # same rule still works (exact match)
        return None

    return resolve_target

def main():
    schema = load_schema()
    tables = schema["tables"]

    # Determine primary keys
    pk_by_table = {t["name"]: choose_primary_key(t) for t in tables}

    # FK target resolver
    resolve_target = guess_fk_targets(tables, pk_by_table)

    # Create DB
    if Path(DB_PATH).exists():
        Path(DB_PATH).unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Create tables
    for t in tables:
        tname = t["name"]
        pk = pk_by_table[tname]

        col_defs = []
        fk_defs = []

        for col in t["columns"]:
            cname = col["name"]
            cfmt  = col.get("format", "string")
            ctype = sqlite_type(cfmt)

            # column definition
            parts = [f'"{cname}" {ctype}']
            if is_boolean(cfmt):
                parts.append(f'CHECK("{cname}" IN (0,1))')
            if pk and cname == pk:
                parts.append("PRIMARY KEY")

            col_defs.append(" ".join(parts))

            # foreign key guesses for ...UUID that aren't the PK
            if cfmt == "uuid" and cname != pk and cname.endswith("UUID"):
                target_table = resolve_target(cname)
                if target_table:
                    target_pk = pk_by_table.get(target_table)
                    # only add FK if target table has a PK and it's uuid-based or 'ID'
                    if target_pk:
                        fk_defs.append(
                            f'FOREIGN KEY("{cname}") REFERENCES "{target_table}"("{target_pk}")'
                        )

        ddl = f'CREATE TABLE "{tname}" (\n  ' + ",\n  ".join(col_defs + fk_defs) + "\n);"
        conn.execute(ddl)

    for t in tables:
        tname = t["name"]
        pk = pk_by_table[tname]
        for col in t["columns"]:
            cname = col["name"]
            if cname == pk:
                continue
            if cname.endswith(("ID", "Code", "UUID")):
                idx = f'CREATE INDEX "idx_{tname}_{cname}" ON "{tname}"("{cname}");'
                try:
                    conn.execute(idx)
                except sqlite3.OperationalError:
                    pass

    conn.commit()
    conn.close()
    print(f"Created {DB_PATH} with tables and indexes.")

if __name__ == "__main__":
    main()
