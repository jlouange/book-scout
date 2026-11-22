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

        data = search_books(search_type=search_type, search_term=search_term)
        display_books(data)

if __name__ == "__main__":
    main()