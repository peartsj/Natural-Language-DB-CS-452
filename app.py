import json
import re
import sqlite3
from pathlib import Path

from openai import OpenAI

from db_setup import DB_PATH, SCHEMA_CONTEXT, initialize_database


CONFIG_PATH = Path("config.json")


def load_config(path=CONFIG_PATH):
    if not path.exists():
        raise FileNotFoundError("config.json was not found.")
    with path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    openai_config = config.get("openai", {})
    api_key = openai_config.get("api_key", "").strip()
    if not api_key or api_key == "PASTE_API_KEY_HERE":
        raise ValueError("Put your real API key in config.json first.")

    return config


def build_client(config):
    openai_config = config["openai"]
    kwargs = {"api_key": openai_config["api_key"].strip()}
    org_id = openai_config.get("organization", "").strip()
    if org_id and org_id != "PASTE_ORG_ID_HERE":
        kwargs["organization"] = org_id
    return OpenAI(**kwargs)


def split_sql_statements(text):
    statements = []
    current = []
    in_single = False
    in_double = False
    i = 0

    while i < len(text):
        ch = text[i]

        if ch == "'" and not in_double:
            if in_single and i + 1 < len(text) and text[i + 1] == "'":
                current.append(ch)
                current.append(text[i + 1])
                i += 2
                continue
            in_single = not in_single
            current.append(ch)
            i += 1
            continue

        if ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
            i += 1
            continue

        if ch == ";" and not in_single and not in_double:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)

    return statements


def clean_sql(raw_sql):
    text = raw_sql.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:sql)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()

    match = re.search(r"\b(select|with)\b", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError("Only SELECT queries are allowed.")
    text = text[match.start():].strip()

    statements = split_sql_statements(text)
    if not statements:
        raise ValueError("Only SELECT queries are allowed.")

    text = statements[0].strip()

    lowered = text.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("Only SELECT queries are allowed.")

    blocked_words = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "replace",
        "pragma",
        "attach",
        "detach",
    ]
    for word in blocked_words:
        if re.search(rf"\b{word}\b", lowered):
            raise ValueError("Unsafe SQL generated. Try rephrasing your question.")

    return text


def question_to_sql(client, model, question):
    instructions = (
        "You write SQLite SELECT queries. Return exactly one SQL statement and nothing else. "
        "Do not include a second statement. "
        "SQLite note: GROUP_CONCAT(DISTINCT value, 'sep') is invalid; DISTINCT aggregates take one argument, so use a subquery if needed. "
        "Use only the provided schema. Never use INSERT, UPDATE, DELETE, DROP, ALTER, PRAGMA, ATTACH, DETACH, or CREATE. "
        "Prefer explicit joins."
    )
    prompt = (
        f"Schema:\n{SCHEMA_CONTEXT}\n\n"
        f"Question: {question}\n\n"
        "Return exactly one SQL query."
    )

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt},
        ],
    )

    sql = response.output_text.strip()
    return clean_sql(sql)


def run_query(db_path, sql):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def results_to_answer(client, model, question, sql, rows):
    sample_rows = rows[:50]
    prompt = (
        "Turn the SQL result into a short, clear answer in plain language. "
        "If no rows were returned, say that clearly and suggest how the user might ask differently.\n\n"
        f"Original question: {question}\n"
        f"SQL used: {sql}\n"
        f"Result row count: {len(rows)}\n"
        f"Result rows (up to 50): {json.dumps(sample_rows, ensure_ascii=True)}"
    )

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": "You explain database query results to a student in plain English.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    return response.output_text.strip()


def main():
    config = load_config()
    db_path = config.get("database", {}).get("path", DB_PATH)
    model = config.get("openai", {}).get("model", "gpt-5-mini")

    initialize_database(db_path)
    client = build_client(config)

    print("Database is ready.")
    print("Ask a question about your media library. Type 'exit' to quit.")

    while True:
        question = input("\n> ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break

        generated_sql = None
        try:
            generated_sql = question_to_sql(client, model, question)
            print("\nSQL:")
            print(generated_sql)

            rows = run_query(db_path, generated_sql)
            answer = results_to_answer(client, model, question, generated_sql, rows)

            print("\nAnswer:")
            print(answer)
        except Exception as e:
            if generated_sql:
                print("\nSQL:")
                print(generated_sql)
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
