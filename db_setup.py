import sqlite3


DB_PATH = "media_library.db"


SCHEMA_CONTEXT = """
Tables:
- LANGUAGE(language_id, code, name)
- COMPANY(company_id, name)
- ITEM(item_id, item_type, title, release_year, description, language_id, notes, created_at)
- BOOK(item_id, isbn, page_count, publisher_id)
- MOVIE(item_id, runtime_minutes, rating, studio_id)
- GAME(item_id, platform, publisher_id)
- CREATOR(creator_id, name)
- ROLE(role_id, name)
- ITEM_CREATOR(item_id, creator_id, role_id)
- GENRE(genre_id, name)
- ITEM_GENRE(item_id, genre_id)
- FORMAT(format_id, name)
- ITEM_FORMAT(item_id, format_id, details, acquired_date)

Relationships:
- ITEM.language_id -> LANGUAGE.language_id
- BOOK.item_id, MOVIE.item_id, GAME.item_id -> ITEM.item_id
- BOOK.publisher_id, GAME.publisher_id, MOVIE.studio_id -> COMPANY.company_id
- ITEM_CREATOR links ITEM, CREATOR, ROLE
- ITEM_GENRE links ITEM and GENRE
- ITEM_FORMAT links ITEM and FORMAT
""".strip()


def initialize_database(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    create_schema(conn)
    seed_data(conn)
    conn.commit()
    conn.close()


def create_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS LANGUAGE (
            language_id INTEGER PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS COMPANY (
            company_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS ITEM (
            item_id INTEGER PRIMARY KEY,
            item_type TEXT NOT NULL CHECK(item_type IN ('BOOK', 'MOVIE', 'GAME')),
            title TEXT NOT NULL,
            release_year INTEGER,
            description TEXT,
            language_id INTEGER NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(language_id) REFERENCES LANGUAGE(language_id)
        );

        CREATE TABLE IF NOT EXISTS BOOK (
            item_id INTEGER PRIMARY KEY,
            isbn TEXT,
            page_count INTEGER,
            publisher_id INTEGER,
            FOREIGN KEY(item_id) REFERENCES ITEM(item_id) ON DELETE CASCADE,
            FOREIGN KEY(publisher_id) REFERENCES COMPANY(company_id)
        );

        CREATE TABLE IF NOT EXISTS MOVIE (
            item_id INTEGER PRIMARY KEY,
            runtime_minutes INTEGER,
            rating TEXT,
            studio_id INTEGER,
            FOREIGN KEY(item_id) REFERENCES ITEM(item_id) ON DELETE CASCADE,
            FOREIGN KEY(studio_id) REFERENCES COMPANY(company_id)
        );

        CREATE TABLE IF NOT EXISTS GAME (
            item_id INTEGER PRIMARY KEY,
            platform TEXT,
            publisher_id INTEGER,
            FOREIGN KEY(item_id) REFERENCES ITEM(item_id) ON DELETE CASCADE,
            FOREIGN KEY(publisher_id) REFERENCES COMPANY(company_id)
        );

        CREATE TABLE IF NOT EXISTS CREATOR (
            creator_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS ROLE (
            role_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS ITEM_CREATOR (
            item_id INTEGER NOT NULL,
            creator_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY(item_id, creator_id, role_id),
            FOREIGN KEY(item_id) REFERENCES ITEM(item_id) ON DELETE CASCADE,
            FOREIGN KEY(creator_id) REFERENCES CREATOR(creator_id),
            FOREIGN KEY(role_id) REFERENCES ROLE(role_id)
        );

        CREATE TABLE IF NOT EXISTS GENRE (
            genre_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS ITEM_GENRE (
            item_id INTEGER NOT NULL,
            genre_id INTEGER NOT NULL,
            PRIMARY KEY(item_id, genre_id),
            FOREIGN KEY(item_id) REFERENCES ITEM(item_id) ON DELETE CASCADE,
            FOREIGN KEY(genre_id) REFERENCES GENRE(genre_id)
        );

        CREATE TABLE IF NOT EXISTS FORMAT (
            format_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS ITEM_FORMAT (
            item_id INTEGER NOT NULL,
            format_id INTEGER NOT NULL,
            details TEXT,
            acquired_date TEXT,
            PRIMARY KEY(item_id, format_id),
            FOREIGN KEY(item_id) REFERENCES ITEM(item_id) ON DELETE CASCADE,
            FOREIGN KEY(format_id) REFERENCES FORMAT(format_id)
        );
        """
    )


def seed_data(conn):
    conn.executemany(
        "INSERT OR IGNORE INTO LANGUAGE(language_id, code, name) VALUES (?, ?, ?)",
        [
            (1, "en", "English"),
            (2, "ja", "Japanese"),
            (3, "es", "Spanish"),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO COMPANY(company_id, name) VALUES (?, ?)",
        [
            (1, "Penguin Random House"),
            (2, "Warner Bros"),
            (3, "Nintendo"),
            (4, "FromSoftware"),
            (5, "A24"),
            (6, "HarperCollins"),
            (7, "Bandai Namco"),
            (8, "Studio Ghibli"),
            (9, "Supergiant Games"),
            (10, "New Line Cinema"),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO ROLE(role_id, name) VALUES (?, ?)",
        [
            (1, "Author"),
            (2, "Director"),
            (3, "Actor"),
            (4, "Developer"),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO GENRE(genre_id, name) VALUES (?, ?)",
        [
            (1, "Fantasy"),
            (2, "Sci-Fi"),
            (3, "Action"),
            (4, "Drama"),
            (5, "Adventure"),
            (6, "RPG"),
            (7, "Animation"),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO FORMAT(format_id, name) VALUES (?, ?)",
        [
            (1, "Physical"),
            (2, "Digital"),
            (3, "Streaming"),
            (4, "Hardcover"),
            (5, "Paperback"),
            (6, "Blu-ray"),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO CREATOR(creator_id, name) VALUES (?, ?)",
        [
            (1, "Frank Herbert"),
            (2, "Christopher Nolan"),
            (3, "Leonardo DiCaprio"),
            (4, "Eiji Aonuma"),
            (5, "Hayao Miyazaki"),
            (6, "J. R. R. Tolkien"),
            (7, "Hidetaka Miyazaki"),
            (8, "Daniel Kwan"),
            (9, "Daniel Scheinert"),
            (10, "Gabriel Garcia Marquez"),
            (11, "Supergiant Dev Team"),
            (12, "Peter Jackson"),
            (13, "Denis Villeneuve"),
            (14, "Monolith Productions"),
        ],
    )

    conn.executemany(
        """
        INSERT OR IGNORE INTO ITEM(item_id, item_type, title, release_year, description, language_id, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "BOOK", "Dune", 1965, "A science fiction novel set on Arrakis.", 1, "Classic novel"),
            (2, "MOVIE", "Inception", 2010, "A thief enters dreams to steal information.", 1, "Mind-bending sci-fi"),
            (3, "GAME", "The Legend of Zelda: Breath of the Wild", 2017, "Open-world action adventure game.", 1, "Switch launch era"),
            (4, "MOVIE", "Spirited Away", 2001, "Animated fantasy film about a girl in a spirit world.", 2, "Oscar winner"),
            (5, "BOOK", "The Hobbit", 1937, "Bilbo Baggins goes on an unexpected journey.", 1, "Prequel to LOTR"),
            (6, "GAME", "Elden Ring", 2022, "Action RPG in a dark fantasy world.", 1, "Huge open world"),
            (7, "MOVIE", "Everything Everywhere All at Once", 2022, "A multiverse family drama/action film.", 1, "A24 film"),
            (8, "BOOK", "One Hundred Years of Solitude", 1967, "A multi-generational story of the Buendia family.", 3, "Magical realism"),
            (9, "GAME", "Hades", 2020, "Roguelike dungeon crawler inspired by Greek mythology.", 1, "Indie hit"),
            (10, "MOVIE", "The Lord of the Rings: The Fellowship of the Ring", 2001, "Epic fantasy movie based on Tolkien's work.", 1, "LOTR movie"),
            (11, "MOVIE", "Dune", 2021, "Modern film adaptation of the Dune novel.", 1, "Book adaptation"),
            (12, "BOOK", "Starting Point: 1979-1996", 2009, "Essays and notes by Hayao Miyazaki.", 1, "Creator across media"),
            (13, "GAME", "Middle-earth: Shadow of Mordor", 2014, "Action game set in Tolkien's Middle-earth.", 1, "Cross-media Tolkien example"),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO BOOK(item_id, isbn, page_count, publisher_id) VALUES (?, ?, ?, ?)",
        [
            (1, "9780441013593", 688, 6),
            (5, "9780547928227", 310, 1),
            (8, "9780060883287", 417, 1),
            (12, "9781421505947", 448, 6),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO MOVIE(item_id, runtime_minutes, rating, studio_id) VALUES (?, ?, ?, ?)",
        [
            (2, 148, "PG-13", 2),
            (4, 125, "PG", 8),
            (7, 139, "R", 5),
            (10, 178, "PG-13", 10),
            (11, 155, "PG-13", 2),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO GAME(item_id, platform, publisher_id) VALUES (?, ?, ?)",
        [
            (3, "Nintendo Switch", 3),
            (6, "PC, PS5, Xbox", 7),
            (9, "PC, Switch, PS, Xbox", 9),
            (13, "PC, PS4, Xbox One", 2),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO ITEM_CREATOR(item_id, creator_id, role_id) VALUES (?, ?, ?)",
        [
            (1, 1, 1),
            (2, 2, 2),
            (2, 3, 3),
            (3, 4, 4),
            (4, 5, 2),
            (5, 6, 1),
            (6, 7, 4),
            (7, 8, 2),
            (7, 9, 2),
            (8, 10, 1),
            (9, 11, 4),
            (10, 6, 1),
            (10, 12, 2),
            (11, 1, 1),
            (11, 13, 2),
            (12, 5, 1),
            (13, 6, 1),
            (13, 14, 4),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO ITEM_GENRE(item_id, genre_id) VALUES (?, ?)",
        [
            (1, 2),
            (2, 2),
            (2, 3),
            (3, 5),
            (3, 6),
            (4, 1),
            (4, 7),
            (5, 1),
            (5, 5),
            (6, 1),
            (6, 6),
            (7, 3),
            (7, 4),
            (8, 4),
            (9, 3),
            (9, 6),
            (10, 1),
            (10, 5),
            (11, 2),
            (11, 4),
            (12, 4),
            (13, 1),
            (13, 3),
            (13, 5),
        ],
    )

    conn.executemany(
        "INSERT OR IGNORE INTO ITEM_FORMAT(item_id, format_id, details, acquired_date) VALUES (?, ?, ?, ?)",
        [
            (1, 5, "Mass market paperback", "2023-09-02"),
            (2, 6, "4K UHD copy", "2022-03-10"),
            (2, 3, "Available on streaming service", "2024-01-15"),
            (3, 1, "Physical cartridge", "2019-11-20"),
            (4, 3, "Streaming subscription", "2024-05-07"),
            (5, 4, "Hardcover edition", "2021-02-14"),
            (6, 2, "Digital Steam copy", "2022-04-01"),
            (7, 3, "Streaming rental", "2024-06-10"),
            (8, 5, "Paperback", "2020-08-19"),
            (9, 2, "Digital copy", "2021-12-05"),
            (10, 6, "Blu-ray extended edition", "2023-01-20"),
            (10, 3, "Streaming purchase", "2024-03-05"),
            (11, 6, "4K steelbook", "2022-01-12"),
            (12, 4, "Hardcover art book", "2022-07-08"),
            (13, 2, "Digital copy", "2020-10-12"),
        ],
    )
