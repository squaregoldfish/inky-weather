import toml
import os
from requests_oauthlib import OAuth2Session
import time
import json
import requests

with open('config.toml') as c:
    config = toml.load(c)

TOKEN_FILE = "netatmo_token.json"

def token_updater(token):
    # Save the new token to a file or any storage solution
    print("Updating token:", token)
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token, f)

def save_token_data(token_data):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)

def load_token_data():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None

def get_oauth_session():
    token_data = load_token_data()

    if token_data and time.time() < token_data['expires_at'] - 60:
        oauth = OAuth2Session(config['netatmo']['client_id'], token=token_data)
        return oauth

    oauth = OAuth2Session(config['netatmo']['client_id'], redirect_uri='http://localhost', token_updater=token_updater)
    token = oauth.refresh_token(
        'https://api.netatmo.com/oauth2/token',
        client_id=config['netatmo']['client_id'],
        client_secret=config['netatmo']['client_secret'],
        refresh_token=config['netatmo']['init_refresh_token']
    )

    token_data = {
        'access_token': token['access_token'],
        'refresh_token': token['refresh_token'],
        'expires_at': time.time() + token['expires_in']
    }
    save_token_data(token_data)

    oauth.token = token_data
    return oauth

oauth = get_oauth_session()


headers = {
    'Authorization': f'Bearer {oauth.access_token}'
}

response = requests.get('https://api.netatmo.com/api/getstationsdata', headers=headers)

if response.status_code == 200:
    data = response.json()
    
    with open("netatmo_weather.json", "w") as out:
        json.dump(data['body'], out)
else:
    print(f"Error: {response.status_code} - {response.text}")
