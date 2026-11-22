from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/api/books')
def get_books():
    search_term = request.args.get("q", "").strip()
    search_type = request.args.get("type", "title").strip()
    allowed_types = ["title", "author"]
    if search_type not in allowed_types:
        return {"ERROR": "Type not FOUND"}, 400
    if not search_term or not search_type:
        return {
            "Error": "400 BAD REQUEST"
            }, 400
    params = {
        search_type : search_term,
        "limit": 3
    }
    try:

        url = "https://openlibrary.org/search.json"
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            return {"ERROR": "RETURNED INVALID JSON"}, 502
    except requests.exceptions.Timeout:
        return {"error":"The request timed out!"}, 504
    except requests.exceptions.ConnectionError:
        return {"error":"Could not connect to the server!"}, 502
    except requests.exceptions.HTTPError:
        return {"error":"The response is invalid!"}, 502
    except requests.exceptions.JSONDecodeError:
        return {"error":"The external API returned invalid JSON"}, 502

    if not isinstance(data.get("docs"), list):
        return {"ERROR": "Malformed JSON Response"}, 502
    books = data.get("docs", [])

    formatted_books = []
    for book in books:
        the_book = {"book_id" : book.get("key"),
        "book_title" : book.get("title"),
        "book_authors" : book.get("author_name", []),
        "book_pub_year" : book.get("first_publish_year", "")}
        formatted_books.append(the_book)

    the_final_response = {"total": data.get("numFound", 0), "books": formatted_books}
    return the_final_response

if __name__ == "__main__":
    app.run(debug=True, port=5001)