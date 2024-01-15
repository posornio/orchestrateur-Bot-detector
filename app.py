import os
import requests
from datetime import datetime , timedelta

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)

app = Flask(__name__)

format_str = "%Y-%m-%d"

def get_data(username):
    #Appeler la database et récupérer les données
    predict = None
    now = datetime.now()
    data = requests.get(f'https://bot-detector-dbmanager.azurewebsites.net/account?username={username}')

    if data.status_code == 200:
        data = data.json()
        
        if (now - datetime.strptime(data.get('last_predict'), format_str)) < timedelta(days=30):
            predict = data.get('predict')
            requests.patch(f'https://bot-detector-dbmanager.azurewebsites.net/accountCall?username={username}')
        else : 
            predict = -1

    return predict

def get_prediction(username):
    #Appeler le modèle
    predict = requests.get(f'https://insa-bot-detector.azurewebsites.net/?name={username}')
    return predict.json().get('Bot')[0]

def post_database(username, predict) :
    #Mettre à jour la base de données
    data = {
        'username': username,
        'predict': predict,
        'call': 1,
        'last_predict': str(datetime.now().date())
    }
    requests.post('https://bot-detector-dbmanager.azurewebsites.net/account', json=data)

@app.route('/', methods=['GET'])
def orchestrator():
    username = request.args.get('username')
    predict = get_data(username)

    if predict == None:    
        predict= get_prediction(username)
        post_database(username, predict)
    elif predict == -1:
        predict= get_prediction(username)
        requests.patch(f'https://bot-detector-dbmanager.azurewebsites.net/accountPredict?username={username}&predict={predict}')
    return str(predict)

if __name__ == '__main__':
   app.run()
