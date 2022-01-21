# coding=utf-8
import os
import mysql.connector
import requests
import smtplib, ssl
from flask import Flask, request, jsonify
from flask_cors import CORS
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()  # Tuo muuttujat .env tiedostosta.

app = Flask(__name__)

CORS(app, origins=["https://villeehrukainen.fi","http://villeehrukainen.fi","localhost:8080"])

# Funktio joka ottaa vastaan tokenin ja tarkistaa recaptchan.
def reCaptcha(token):
    # Luo linkki jolla GET kutsu tehdään googlen recaptcha palveluun. os.environin avulla voidaan käyttää ympäristömuuttujia jotka
    # dotenv on tuonut .env tiedostosta.
    recaptchaUrl = "https://www.google.com/recaptcha/api/siteverify?secret="+os.environ['RECAPTCHA_SECRET']+"&response="+token+"";
    try:
        # Säilytä GET kutsun vastaus response muuttujassa, .json() pitää huolen, että muoto on oikea.
        response = requests.get(recaptchaUrl).json()
        # Jos recaptcha palautti onnistumisen palauta True muutoin False.
        if response['success'] == True and float(response['score']) >= 0.5:
            return {"status":"success"}
        else:
            return {"status":"error","reason":"Recaptcha tarkistus epäonnistui!"}
    except requests.exceptions.RequestException as e:  # Kaikki virheet jotka liittyvät pyyntöön palauttavat seuraavaa.
        return {"status":"error","reason":"Recaptcha palvelu ei vastannut!"}
    except: # Kaikki virheet jotka eivät ole ylemmän expectin mukaisia palauttavat seuraavaa.
        return {"status":"error","reason":"Tuntematon virhe! RE01"}

# GET pyyntö polkuun / vastaa html tiedolla.
@app.route('/', methods=['GET'])
def index():
    return "<h1>PythonAPI ansioluettelosivulleni</h1><br/><p>Ville Ehrukainen 2022</p>"

# GET pyyntö polkuun /apod vastaa nasan päivän astronomiakuvan linkillä, päivämäärällä ja tekijäoikeustiedoilla. Muutoin lähettää virheen.
@app.route('/apod', methods=['GET'])
def apod():
    try:
        # Säilytä GET kutsun vastaus response muuttujassa, .json() pitää huolen, että muoto on oikea.
        response = requests.get('https://api.nasa.gov/planetary/apod?api_key='+os.environ['APOD_APIKEY']).json()
        if not "copyright" in response:
            copyright = ""
        else:
            copyright = response['copyright']
        
        hdurl = response['hdurl']
        date = response['date']
        return jsonify({'status':'success','hdurl':hdurl,'copyright':copyright,'date':date})
    except requests.exceptions.RequestException as e:  # Kaikki virheet jotka liittyvät pyyntöön palauttavat seuraavaa.
        return jsonify({'status':'error','reason':'NASA APOD palvelu ei vastannut!'})
    except: # Kaikki virheet jotka eivät ole ylemmän expectin mukaisia palauttavat seuraavaa.
        return jsonify({'status':'error','reason':'Tuntematon virhe! AP01'})

@app.route('/mail', methods=['POST'])
def mail():
    requestdata = request.get_json()
    if not "email" in requestdata:
        return jsonify({'status':'error','reason':'Tietoja puuttuu!'})
    if not "msg" in requestdata:
        return jsonify({'status':'error','reason':'Tietoja puuttuu!'})
    if not "token" in requestdata:
        return jsonify({"status":"error","reason":"Recaptcha tokenia ei vastaanotettu!"})
    # Recapcha tarkistus.
    recaptcha = reCaptcha(requestdata['token'])
    if recaptcha['status'] == "success":
        try:
            sender_email = os.environ['MAIL_USER']
            receiver_email = requestdata['email']
            password = os.environ['MAIL_PASS']

            message = MIMEMultipart("alternative")
            message["Subject"] = "Villeehrukainen.fi | Yhteyslomake"
            message["From"] = sender_email
            message["To"] = receiver_email

            sender_emailad = os.environ['MAIL_USER']
            receiver_emailad = "ville.ehrukainen2@gmail.com"

            messagead = MIMEMultipart("alternative")
            messagead["Subject"] = "Villeehrukainen.fi | Yhteyslomake"
            messagead["From"] = sender_email
            messagead["To"] = "ville.ehrukainen2@gmail.com"

            # Create the plain-text and HTML version of your message
            text = """\
            Hei!
            Viestisi on onnistuneesti vastaanotettu!
            www.villeehrukainen.fi"""
            html = """\
            <html>
            <body>
                <h2>Hei,<h2/>
                <p>Viestisi on onnistuneesti vastaanotettu!</p><br/>
                <a href="https://www.villeehrukainen.fi">Villeehrukainen.fi</a> 
            </body>
            </html>
            """

            textad = """\
            Hei!
            Viestisi on onnistuneesti vastaanotettu!
            www.villeehrukainen.fi"""
            htmlad = """\
            <html>
            <body>
                <h2>Lähettäjä: """+requestdata['email']+"""<h2/>
                <p>"""+requestdata['msg']+"""<br/>
                <a href="https://www.villeehrukainen.fi">Villeehrukainen.fi</a> 
            </body>
            </html>
            """

            # Turn these into plain/html MIMEText objects
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            part1ad = MIMEText(textad, "plain")
            part2ad = MIMEText(htmlad, "html")

            # Add HTML/plain-text parts to MIMEMultipart message
            # The email client will try to render the last part first
            message.attach(part1)
            message.attach(part2)
            messagead.attach(part1ad)
            messagead.attach(part2ad)

            messagead.attach(part1ad)
            messagead.attach(part2ad)

            # Create secure connection with server and send email
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(os.environ['MAIL_HOST'], 465, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
                server.sendmail(sender_emailad, receiver_emailad, messagead.as_string())
        except:
            return jsonify({'status':'error','reason':'Sähköpostin lähettäminen epäonnistui!'})
        
        return jsonify({'status':'success','reason':'Sähköpostin lähettäminen onnistui!'})
    else:
        return jsonify({'status':'error','reason':recaptcha['reason']})

@app.route('/feedback', methods=['POST'])
def feed():
    requestdata = request.get_json()
    if not "responsiivisuus" in requestdata:
        return jsonify({'status':'error','reason':'Tietoja puuttuu!'})
    if not "kaytettavyys" in requestdata:
        return jsonify({'status':'error','reason':'Tietoja puuttuu!'})
    if not "ulkoasu" in requestdata:
        return jsonify({'status':'error','reason':'Tietoja puuttuu!'})
    if not "email" in requestdata:
        return jsonify({'status':'error','reason':'Tietoja puuttuu!'})
    if not "token" in requestdata:
        return jsonify({"status":"error","reason":"Recaptcha tokenia ei vastaanotettu!"})
     # Recapcha tarkistus.
    recaptcha = reCaptcha(requestdata['token'])
    if recaptcha['status'] == "success":
        # Connect to DB
        try:
            mydb = mysql.connector.connect(
                host=os.environ['DB_HOST'],
                user=os.environ['DB_USER'],
                password=os.environ['DB_PASS'],
                database=os.environ['DB_FEEDBACK']
            )
            mycursor = mydb.cursor()

            if not "message" in requestdata:
                sql = "INSERT INTO palaute (responsiivisuus, kaytettavuus, ulkoasu, sahkoposti) VALUES (%s, %s, %s, %s)"
                val = (requestdata['responsiivisuus'],requestdata['kaytettavyys'],requestdata['ulkoasu'],requestdata['email'])
                mycursor.execute(sql, val)
            else:
                sql = "INSERT INTO palaute (responsiivisuus, kaytettavuus, ulkoasu, sahkoposti, viesti) VALUES (%s, %s, %s, %s, %s)"
                val = (requestdata['responsiivisuus'],requestdata['kaytettavyys'],requestdata['ulkoasu'],requestdata['email'],requestdata['message'])
                mycursor.execute(sql, val)
            mydb.commit()
        except:
            return jsonify({'status':'error','reason':'Yhteys tietokantaan epäonnistui!'})
    else:
        return jsonify({'status':'error','reason':recaptcha['reason']})
    return jsonify({'status':'success','reason':'Palaute lähetettiin onnistuneesti!'})
from waitress import serve
serve(app, host='127.0.0.1', port=8080)