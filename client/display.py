def display_books(data):
    if "error" in data:
        print(f"\nError: {data['error']}")
        return

    print(f"\nFound {data.get('total', 0)} matching.")
    print("-" * 40)

    for book in data.get("books", []):
        authors = book.get("book_authors") or ["Unknown"]

        print(f"Title: {book.get('book_title', 'Unknown')}")
        print(f"Author(s): {','.join(authors)}")
        print(f"Publication year: {book.get('book_pub_year') or 'Unknown'}")
        print("-" * 40)
