def display_books(data):
    if "error" in data:
        print(f"\nError: {data['error']}")
        return

    books = data.get("books", [])
    total = data.get("total", 0)



    print(f"\nFound {total} matching.")
    print("-" * 40)

    if not books:
        print("No books found. Try another title or author.")
        return
    # print(f"Showing {len(books)} of {total} matching books.\n")

    page = data.get("page", 1)
    limit = data.get("limit", 3)

    start = (page - 1) * limit + 1
    end = start + len(books) - 1

    print(f"Showing books {start}-{end} of {total} matching books.\n")


    for index,book in enumerate(books,  start=start):
        authors = book.get("book_authors") or ["Unknown"]

        print(f" {index}. Title: {book.get('book_title', 'Unknown')}")
        print(f"\tAuthor(s): {', '.join(authors)}")
        print(f"\tPublication year: {book.get('book_pub_year') or 'Unknown'}")
        print("-" * 40)
