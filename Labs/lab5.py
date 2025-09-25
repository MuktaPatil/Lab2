import streamlit as st
import requests
from openai import OpenAI

def get_current_weather(location: str, API_key: str):
    """
    Retrieve current weather for a given location using OpenWeatherMap API.
    Returns a dictionary with temperature, feels_like, min, max, humidity, and description.
    """
    if "," in location:
        location = location.split(",")[0].strip()

    urlbase = "https://api.openweathermap.org/data/2.5/"
    urlweather = f"weather?q={location}&appid={API_key}&units=metric"
    response = requests.get(urlbase + urlweather)
    data = response.json()

    if response.status_code != 200 or "main" not in data:
        return {"error": f"Could not retrieve weather for {location}"}

    # Extract temperatures & convert Kelvin → Fahrenheit
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    temp_min = data['main']['temp_min']
    temp_max = data['main']['temp_max']
    humidity = data['main']['humidity']
    description = data['weather'][0]['description']

    return {
        "location": location,
        "temperature": round(temp, 2),     
        "feels_like": round(feels_like, 2),
        "temp_min": round(temp_min, 2),
        "temp_max": round(temp_max, 2),
        "humidity": round(humidity, 2),
        "description": description
    }



st.title("🌤 Smart Outfit Picker")

# API keys from secrets
API_key = st.secrets["openweather_api_key"]
client = OpenAI(api_key=st.secrets["openai_api_key"])

# Input city
city = st.text_input("Enter a city:", "Syracuse, NY")

if st.button("Pick me an outfit!"):
    weather = get_current_weather(city, API_key)

    if "error" in weather:
        st.error(weather["error"])
    else:
        # Show weather info
        st.write("### Weather Info (In Celsius)")
        st.json(weather)

        # Build prompt for clothing suggestion
        prompt = f"""
        The current weather in {weather['location']} is:
        - Temperature: {weather['temperature']}°C
        - Feels like: {weather['feels_like']}°C
        - Min: {weather['temp_min']}°C / Max: {weather['temp_max']}°C
        - Humidity: {weather['humidity']}%
        - Condition: {weather['description']}

        Based on this weather:
        1. Suggest appropriate clothes to wear today.
        2. Say whether it’s a good day for a picnic.
        """

        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        suggestion = response.choices[0].message.content

        st.write("## Wardrobe Suggestions")
        st.write(suggestion)