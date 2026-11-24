import requests
API_URL = "https://www.jlmushumba.tech/api/books"
#API_URL = "http://127.0.0.1:5001/api/books" # this wa my local development api


def search_books(search_type, search_term, limit, page, sort_order="relevance"):
    params = {
        "q": search_term,
        "type": search_type,
        "limit": limit,
        "page": page,
        "sort": sort_order

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