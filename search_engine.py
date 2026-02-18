import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
CX = os.getenv("GOOGLE_CX")


async def search_google(query: str):
    url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "key": API_KEY,
        "cx": CX,
        "q": query,
        "num": 5
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []

    if "items" in data:
        for item in data["items"]:
            results.append({
                "title": item["title"],
                "link": item["link"],
                "snippet": item["snippet"]
            })

    return results
