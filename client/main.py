from client.menu import display_main_menu
from client.api_client import search_books
from client.display import display_books



def main():

    while True:
        search_type = display_main_menu()
        if search_type is None:
            print("Thank you for using BookScout. Goodbye!")
            break

        search_term = input(f"Enter the {search_type} you want to search for: ").strip()
        if not search_term:
            print("Search term cannot be empty!")
            continue

        while True:

            try:

                limit = int(input("Results per page (1-20): "))

                if 1 <= limit <= 20:
                    break

                print("Please enter a number between 1 and 20.")

            except ValueError:
                print("Please enter a valid number.")


        while True:


            print("\nSort results by:")
            print("1. Relevance (default)")
            print("2. Newest first")
            print("3. oldest first")

            sort_choice = input(">> ").strip()

            sort_options = {
                "1": "relevance",
                "2": "new",
                "3": "old"
            }

            if sort_choice in sort_options:
                sort_order = sort_options[sort_choice]
                break

            print("Invalid choice! Enter 1, 2, or 3")


        page = 1

        # the paginantion part

        page_cache = {}

        while True:

            if page in page_cache:
                data = page_cache[page]

            else:

                data = search_books(
                    search_type=search_type,
                    search_term=search_term,
                    limit=limit,
                    page=page,
                    sort_order=sort_order
                )

                if not isinstance(data, dict):
                    data = {"error": "Invalid response from the server"}


                if "error" in data:

                    display_books(data)

                    while True:

                        print("\nR. Retry request")
                        print("B. Back to main menu")

                        choice = input(">> ").strip().lower()


                        if choice in ("r", "b"):
                            break

                        print("Invalid choice! Enter R or B")

                    if choice == "b":
                        break

                    continue

                page_cache[page] = data

            display_books(data)

            if not data.get("books"):
                break

            print(
                f"\nPage {data.get('page', page)} "
                f"of {data.get('total_pages', 1)}"
            )


            while True:

                print("\nN. Next pages")
                print("P. previous page")
                print("B. Back to main menu")

                choice = input(">> ").strip().lower()

                if choice == "n":
                    if data.get("has_next"):
                        page += 1
                        break

                    else:
                        print("You are on the last page")

                elif choice == "p":
                    if data.get("has_previous"):
                        page -= 1
                        break
                    else:
                        print("you are on the first page")

                elif choice == "b":
                    break

                else:
                    print("Invalid choice! Enter N, P, or B.")

            # data = search_books(search_type=search_type, search_term=search_term)

            if choice == "b":
                break       # display_books(data)

if __name__ == "__main__":
    main()