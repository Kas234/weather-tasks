# pobieranie danych pogodowychim

import requests

def get_weather():
    API_KEY = "e84a6c3860ab207983fc8b8746a515ee"
    CITY = "Tenerife"
    URL = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}"
    response = requests.get(URL)
    return response.json()
