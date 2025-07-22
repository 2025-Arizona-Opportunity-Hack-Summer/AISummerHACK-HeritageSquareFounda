"""
Code that is located in virtual environment flask server currently interacting with frontend
"""

import time
from flask import Flask, request

app = Flask(__name__)

@app.route('/api/query')
def search():
    query = request.args.get('q')
    time.sleep(3)
    if query:
        return {'response': f"Received query: {query}"}
    else:
        return {'response': "No search query provided."}