from search import *

from flask import Flask, render_template, request


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    q = request.form.get('q')
    results = run_search(q)
    return render_template('search.html', results=results)
