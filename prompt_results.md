# Prompt Results

## Prompt 1

Prompt:

```text
Who are the top 3 creators in my library by number of distinct items?
```

Result:

SQL:
```sql
SELECT c.creator_id, c.name, COUNT(DISTINCT ic.item_id) AS item_count
FROM CREATOR c
JOIN ITEM_CREATOR ic ON c.creator_id = ic.creator_id
GROUP BY c.creator_id, c.name
ORDER BY item_count DESC, c.name ASC
LIMIT 3
```

Answer:
```text
Top 3 creators by distinct items in your library:
1) J. R. R. Tolkien — 3 items
2) Frank Herbert — 2 items
3) Hayao Miyazaki — 2 items

Note: Frank Herbert and Hayao Miyazaki are tied with 2 items; your query ordered ties alphabetically by name.
```

## Prompt 2

Prompt:

```text
List items releases before 2000 grouped by format. Please provide relevant details about the item
```

Result:

SQL:
```sql
SELECT
  f.name AS format_name,
  GROUP_CONCAT(
    i.item_id || '|' || i.title || ' (' || i.item_type || ', ' || i.release_year || ')' ||
    CASE WHEN l.name IS NOT NULL THEN ' [lang:' || l.name || ']' ELSE '' END ||
    CASE
      WHEN b.isbn IS NOT NULL THEN ' [ISBN:' || b.isbn || '][pages:' || COALESCE(b.page_count, '') || ']'
      WHEN m.runtime_minutes IS NOT NULL THEN ' [runtime:' || m.runtime_minutes || 'min][rating:' || COALESCE(m.rating, '') || ']'
      WHEN g.platform IS NOT NULL THEN ' [platform:' || g.platform || ']'
      ELSE ''
    END ||
    CASE WHEN COALESCE(pub_book.name, pub_movie.name, pub_game.name) IS NOT NULL THEN ' [company:' || COALESCE(pub_book.name, pub_movie.name, pub_game.name) || ']' ELSE '' END
    , ' || '
  ) AS items
FROM FORMAT f
JOIN ITEM_FORMAT ifmt ON ifmt.format_id = f.format_id
JOIN ITEM i ON i.item_id = ifmt.item_id
LEFT JOIN LANGUAGE l ON l.language_id = i.language_id
LEFT JOIN BOOK b ON b.item_id = i.item_id
LEFT JOIN MOVIE m ON m.item_id = i.item_id
LEFT JOIN GAME g ON g.item_id = i.item_id
LEFT JOIN COMPANY pub_book ON pub_book.company_id = b.publisher_id
LEFT JOIN COMPANY pub_movie ON pub_movie.company_id = m.studio_id
LEFT JOIN COMPANY pub_game ON pub_game.company_id = g.publisher_id
WHERE i.release_year < 2000
GROUP BY f.format_id, f.name
ORDER BY f.name
```

Answer:
```text
Found items released before 2000, grouped by format:

- Hardcover
  - Item 5: The Hobbit (BOOK, 1937). Language: English. ISBN: 9780547928227. Pages: 310. Publisher: Penguin Random House.

- Paperback
  - Item 1: Dune (BOOK, 1965). Language: English. ISBN: 9780441013593. Pages: 688. Publisher: HarperCollins.
  - Item 8: One Hundred Years of Solitude (BOOK, 1967). Language: Spanish. ISBN: 9780060883287. Pages: 417. Publisher: Penguin Random House.
```

## Prompt 3

Prompt:

```text
Which companies have published at least one book and produced at least one movie? Give details about the company
```

Result:

SQL:
```sql
SELECT c.company_id, c.name, COUNT(DISTINCT b.item_id) AS books_published, COUNT(DISTINCT m.item_id) AS movies_produced
FROM COMPANY c
JOIN BOOK b ON b.publisher_id = c.company_id
JOIN MOVIE m ON m.studio_id = c.company_id
GROUP BY c.company_id, c.name
```

Answer:
```text
No companies meet that condition — your query returned zero rows.

That means: in this database there isn’t any company that is recorded both as a book publisher (publisher_id on BOOK) and as a movie studio (studio_id on MOVIE) at the same time. It could be genuinely true, or it could be caused by data/keys not matching or missing values.

If you want to investigate, try these checks:
- See how many companies publish books and how many produce movies separately:
  SELECT c.company_id, c.name, COUNT(b.item_id) AS books
  FROM COMPANY c JOIN BOOK b ON b.publisher_id = c.company_id
  GROUP BY c.company_id, c.name;
  SELECT c.company_id, c.name, COUNT(m.item_id) AS movies
  FROM COMPANY c JOIN MOVIE m ON m.studio_id = c.company_id
  GROUP BY c.company_id, c.name;
- Or use EXISTS to test intersection (equivalent logic but clearer for debugging):
  SELECT c.company_id, c.name
  FROM COMPANY c
  WHERE EXISTS (SELECT 1 FROM BOOK b WHERE b.publisher_id = c.company_id)
    AND EXISTS (SELECT 1 FROM MOVIE m WHERE m.studio_id = c.company_id);
- If you want companies that did either books or movies (not necessarily both), ask for an OR/UNION instead.

If you’d like, tell me whether you want to (a) confirm the underlying data counts, (b) find companies that did either books or movies, or (c) debug potential missing/mismatched keys — and I’ll give the exact query to run.
```

## Prompt 4

Prompt:

```text
Show all games tagged as RPG. For each game list title, platform, publisher name, and developer(s)
```

Result:

SQL:
```sql
SELECT i.title, g.platform, c.name AS publisher, GROUP_CONCAT(DISTINCT cr.name) AS developers
FROM ITEM i
JOIN GAME g ON g.item_id = i.item_id
LEFT JOIN COMPANY c ON g.publisher_id = c.company_id
JOIN ITEM_GENRE ig ON i.item_id = ig.item_id
JOIN GENRE gen ON ig.genre_id = gen.genre_id AND gen.name = 'RPG'
LEFT JOIN ITEM_CREATOR ic ON i.item_id = ic.item_id
LEFT JOIN ROLE r ON ic.role_id = r.role_id AND r.name = 'Developer'
LEFT JOIN CREATOR cr ON ic.creator_id = cr.creator_id
GROUP BY i.item_id, i.title, g.platform, c.name
ORDER BY i.title
```

Answer:
```text
The query found 3 games tagged as RPG:

- Elden Ring — Platform: PC, PS5, Xbox — Publisher: Bandai Namco — Developer(s): Hidetaka Miyazaki  
- Hades — Platform: PC, Switch, PS, Xbox — Publisher: Supergiant Games — Developer(s): Supergiant Dev Team  
- The Legend of Zelda: Breath of the Wild — Platform: Nintendo Switch — Publisher: Nintendo — Developer(s): Eiji Aonuma

Note: the "developers" field was built by concatenating creators with the "Developer" role, so multiple developers (if any) would appear comma-separated.
```

## Prompt 5

Prompt:

```text
Which creators appear across multiple media types?
```

Result:

SQL:
```sql
SELECT c.creator_id, c.name,
  (SELECT GROUP_CONCAT(t.item_type, ', ')
   FROM (
     SELECT DISTINCT i.item_type
     FROM ITEM i
     JOIN ITEM_CREATOR ic2 ON ic2.item_id = i.item_id
     WHERE ic2.creator_id = c.creator_id
     ORDER BY i.item_type
   ) t
  ) AS media_types
FROM CREATOR c
WHERE (
  SELECT COUNT(*) FROM (
    SELECT DISTINCT i.item_type
    FROM ITEM i
    JOIN ITEM_CREATOR ic3 ON ic3.item_id = i.item_id
    WHERE ic3.creator_id = c.creator_id
  )
) > 1
```

Answer:
```text
The query found 3 creators who appear across multiple media types:
- Frank Herbert — BOOK and MOVIE
- Hayao Miyazaki — BOOK and MOVIE
- J. R. R. Tolkien — BOOK, GAME, and MOVIE
```
