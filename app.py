from flask import Flask, render_template, request
from src.negative_sentiment_analyzer import NegativeSentimentAnalyzer

from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)


analyzer = NegativeSentimentAnalyzer(os.getenv("OPENAI_API_KEY"))


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None

    if request.method == 'POST':
        text = request.form['text']
        is_negative = analyzer.is_negative(text)
        result = "Negative" if is_negative else "Not Negative"

    return render_template('index.html', result=result)


if __name__ == '__main__':
    app.run(debug=True)
