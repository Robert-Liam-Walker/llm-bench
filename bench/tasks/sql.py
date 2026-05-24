"""SQL. Model writes a query; runner executes it against SQLite and compares results."""

import re
import sqlite3

from ._util import extract_code
from .base import Prompt, Task

SETUP_SQL = """
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, country TEXT);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL, created_at TEXT);
INSERT INTO customers VALUES (1, 'Alice', 'US'), (2, 'Bob', 'UK'), (3, 'Cara', 'US'), (4, 'Dan', 'CA');
INSERT INTO orders VALUES
    (1, 1, 100.0, '2026-01-15'),
    (2, 1,  50.0, '2026-02-10'),
    (3, 2, 200.0, '2026-01-20'),
    (4, 3,  75.0, '2026-03-05'),
    (5, 3,  25.0, '2026-03-12'),
    (6, 4, 500.0, '2026-02-28');
"""

PROMPTS = [
    Prompt(
        id="count_us_customers",
        length_bucket="short",
        text=(
            "Given:\n"
            "```sql\n"
            "customers(id, name, country)\n"
            "orders(id, customer_id, amount, created_at)\n"
            "```\n"
            "Write a SQL query that returns the number of customers from the US. "
            "Return one column named `count`."
        ),
        reference={"expected": [(2,)]},
    ),
    Prompt(
        id="top_spender",
        length_bucket="medium",
        text=(
            "Given the same schema, write a query that returns the name of the customer "
            "with the highest total order amount. Return one column named `name`."
        ),
        reference={"expected": [("Dan",)]},
    ),
    Prompt(
        id="monthly_revenue_by_country",
        length_bucket="long",
        text=(
            "Given the same schema, write a query that returns, for each (country, month), the "
            "total order amount. Use the YYYY-MM format for month. Columns: `country`, `month`, "
            "`total`. Order by country, then month ascending."
        ),
        reference={
            "expected": [
                ("CA", "2026-02", 500.0),
                ("UK", "2026-01", 200.0),
                ("US", "2026-01", 100.0),
                ("US", "2026-02", 50.0),
                ("US", "2026-03", 100.0),
            ]
        },
    ),
]


def score(prompt: Prompt, response: str) -> float:
    sql = extract_code(response, "sql")
    # SQLite uses different identifier rules; strip semicolons for safety
    sql = re.sub(r";\s*$", "", sql.strip())
    if not sql:
        return 0.0
    try:
        conn = sqlite3.connect(":memory:")
        conn.executescript(SETUP_SQL)
        rows = conn.execute(sql).fetchall()
        conn.close()
    except Exception:
        return 0.0
    expected = prompt.reference["expected"]
    return 1.0 if rows == expected else 0.0


TASK = Task(
    category="sql",
    scorer_kind="deterministic",
    rubric="",
    prompts=PROMPTS,
    score_fn=score,
)
