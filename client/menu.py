# this is the interactive menu made for the user

# the header part
def display_header():
    width = 30
    title = "BOOK SCOUT"

    head = f"""
    {"=" * width}
    {title.center(width)}
    {"=" * width}
    """.strip()
    print(head)


    print("1. Search books by title")
    print("2. Search books by author")
    print("3. Exit")
def display_main_menu():
    while True:
        display_header()
        try:
            main_menu_choice = int(input(">> "))
        except ValueError:
            print("Please enter a valid value!")
            continue

        if main_menu_choice == 1:
            return "title"
        elif main_menu_choice == 2:
            return "author"
        elif main_menu_choice == 3:
            return None
        else:
            print("please enter a valid value!(1-3)")
            continue

# if __name__ == "__main__":
#     display_main_menu()
