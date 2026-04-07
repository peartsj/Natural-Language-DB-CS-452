# Natural Language Media Organization

This project uses a chatgpt 5 mini to take natural language requests and translate them to and from sql. My database is meant to organize media, looking at common characteristics like genre, creator, etc.

## Files

- `db_setup.py`: database schema + seed data
- `app.py`: CLI app and OpenAI flow
- `config.json`: API key / org / model / db path
- `README.md`: project notes

## Database Design

This project uses a small, student-friendly relational schema to represent a media library. The
goal is clarity for learning SQL rather than exhaustive normalization. At a high level:

- Items: a central `ITEM` table holds shared fields (type, title, year, description, language).
- Media-specific tables: `BOOK`, `MOVIE`, and `GAME` store attributes unique to each format
	(ISBN, runtime, platform, publisher/studio links).
- Creators & roles: `CREATOR` and `ROLE` capture people and their jobs; `ITEM_CREATOR` links
	creators to items so one person can be author, director, actor, or developer.
- Classification: `GENRE` and `FORMAT` plus linking tables (`ITEM_GENRE`, `ITEM_FORMAT`) allow
	many-to-many tags and formats per item.
- Lookups: small tables like `LANGUAGE` and `COMPANY` keep codes and publishers/studios tidy.

The design is organized to make joins, grouping, and common queries straightforward for class
assignments and experiments with natural-language-to-SQL generation.


## A prompt I thought worked well

Prompt:

```text
give me a list of items in the library grouped by creator but only include items with creators that have more than 1 item
```

SQL:

```sql
SELECT c.creator_id,
			 c.name AS creator_name,
			 group_concat(ci.title, '; ') AS items
FROM CREATOR c
JOIN (
	SELECT DISTINCT ic.creator_id, i.item_id, i.title
	FROM ITEM_CREATOR ic
	JOIN ITEM i ON i.item_id = ic.item_id
) ci ON ci.creator_id = c.creator_id
GROUP BY c.creator_id, c.name
HAVING COUNT(ci.item_id) > 1
```

Answer:

```text
I found 3 creators who have more than one item:

- Frank Herbert (creator_id 1) — items: Dune; Dune (appears twice)
- Hayao Miyazaki (creator_id 5) — items: Spirited Away; Starting Point: 1979-1996
- J. R. R. Tolkien (creator_id 6) — items: The Hobbit; The Lord of the Rings: The Fellowship of the Ring; Middle-earth: Shadow of Mordor

Note: Frank Herbert shows "Dune" twice — that likely means the same title is associated more than once. If you want each title listed only once, use GROUP_CONCAT(DISTINCT ...) and/or change the HAVING to COUNT(DISTINCT ci.item_id) > 1 to count unique items.
```

## A prompt that did poorly

Prompt:

```text
List creators and their items, but only include creators that have more than 1 item; list each title only once and show the titles separated by ;
```

SQL:

```sql
SELECT c.creator_id, c.name,
	(
		SELECT group_concat(t.title, ';')
		FROM (
			SELECT DISTINCT i.title
			FROM ITEM i
			JOIN ITEM_CREATOR ic2 ON i.item_id = ic2.item_id
			WHERE ic2.creator_id = c.creator_id
		) t
	) AS titles
FROM CREATOR c
JOIN ITEM_CREATOR ic ON c.creator_id = ic.creator_id
GROUP BY c.creator_id, c.name
HAVING COUNT(DISTINCT ic.item_id) > 1
```

Answer:

```text
Three creators matched your criteria (more than one item). Their names and titles (each title shown once, separated by ;) are:

- Frank Herbert: Dune
- Hayao Miyazaki: Spirited Away; Starting Point: 1979-1996
- J. R. R. Tolkien: The Hobbit; The Lord of the Rings: The Fellowship of the Ring; Middle-earth: Shadow of Mordor
```

Why this confused the app:

- The prompt explicitly asked to "list each title only once", so the SQL deduplicates by `title`. That collapses different items that share a title (for example, a movie and a book both named "Dune") into a single entry.
- The provided SQL uses `DISTINCT i.title` in a subquery, which matches the literal prompt but not the user's expectation of counting distinct items separately.
 
### Why this didn't work well

I tried to see if I could reword the prompt in such a way that it would confuse the model, and it worked. Telling it to list each title only once, it removed the duplicate titles even though they are really separate items. The provided SQL only returns distinct titles, which removes mention of items when their names are the same, as was the case with Dune. Honestly its a mistake even a human could make and it took some tricky wording to get it to mess up.

