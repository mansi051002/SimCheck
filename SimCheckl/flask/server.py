import nltk
import time
import requests
import os
import re
import PyPDF2
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
from flask import Flask, render_template, request, session, redirect, url_for
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from datetime import datetime
import pymongo


app = Flask(__name__)
app.secret_key = "ishan"

# Configure MongoDB
mongo_client = pymongo.MongoClient("mongodb+srv://ishanupadhyaya01:cclab@cluster.zszxpto.mongodb.net/?retryWrites=true&w=majority&appName=Cluster")
db = mongo_client.db

oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id="NmprnBmkaX6oHID6F6Zt1AtYYefLmPgm",
    client_secret="JPNv_w_t0wMDmJNlHFRPSxgKJ6G9mBBs2X8JFnpvt7HOjzhbKOlcNZi_Qft52BpJ",
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://zeuidon.us.auth0.com/.well-known/openid-configuration',
)

# Helper function to make the API call
def make_api_call(data):
    url = "http://localhost:8000/in"
    response = requests.post(url, json=data)
    return response.json()

# Helper function to extract text from PDF
def pdf_to_text(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ''
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
    return text

def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9]", " ", text)
    tokens = word_tokenize(text)
    tokens = [w for w in tokens if w not in stopwords.words("english")]
    lemmatizer = WordNetLemmatizer()
    stemmer = PorterStemmer()
    clean_tokens_list = []
    for tok in tokens:
        lemmatizer_tok = lemmatizer.lemmatize(tok).strip()
        clean_tok = stemmer.stem(lemmatizer_tok)
        clean_tokens_list.append(clean_tok)
    return clean_tokens_list

# Controllers
@app.route("/")
def home():
    return render_template('index.html', session=session.get('user'))

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect(url_for('home'))

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + "zeuidon.us.auth0.com"
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": "NmprnBmkaX6oHID6F6Zt1AtYYefLmPgm",
            },
            quote_via=quote_plus,
        )
    )

@app.route('/', methods=['POST'])
def process_pdfs():
    if 'user' not in session:
        return redirect(url_for('login'))

    file_1 = request.files['file_1']
    file_2 = request.files['file_2']

    text1 = pdf_to_text(file_1)
    tokenized_text1 = " ".join(tokenize(text1))

    text2 = pdf_to_text(file_2)
    tokenized_text2 = " ".join(tokenize(text2))

    my_obj = {
        "t1": text1,
        "t2": text2
    }

    res = make_api_call(my_obj)

    # Store the comparison result in MongoDB
    user_id = session['user']['userinfo']['sub']
    result_data = {
        'user_id': user_id,
        'file_1_name': file_1.filename,
        'file_2_name': file_2.filename,
        'result': res,
        'timestamp': datetime.utcnow()
    }
    db.pdf_comparisons.insert_one(result_data)

    # Retrieve the user's comparison history from MongoDB
    comparison_history = list(db.pdf_comparisons.find({'user_id': user_id}))

    return render_template('result.html', result=res, session=session.get('user'), history=comparison_history)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=3000)