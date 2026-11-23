import requests
API_URL = "https://www.jlmushumba.tech/api/books"


def search_books(search_type, search_term):
    params = {
        "q": search_term,
        "type": search_type
    }

    try:

        response = requests.get(API_URL, params=params, timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        return {"error": f"Request failed: {error}"}

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        return {"error": "The server returned  invalid JSON"}