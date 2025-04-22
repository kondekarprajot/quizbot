import os
from flask import Flask, request, jsonify, send_from_directory
import requests
from flask_cors import CORS
import html  # Added for decoding HTML entities

app = Flask(__name__)
CORS(app)

# Store the current question and answer for each session
sessions = {}

TRIVIA_API_URL = "https://opentdb.com/api.php?amount=1&type=multiple"

def fetch_question():
    res = requests.get(TRIVIA_API_URL)
    if res.status_code != 200:
        return None, None, None

    data = res.json()['results'][0]
    question = html.unescape(data['question'])  # Decode question
    correct = html.unescape(data['correct_answer'])  # Decode correct answer
    options = [html.unescape(opt) for opt in data['incorrect_answers']]  # Decode options
    options.append(correct)

    from random import shuffle
    shuffle(options)
    
    formatted_question = f"{question} " + " ".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    correct_index = options.index(correct) + 1

    return formatted_question, correct, correct_index

# Serve the index.html file from the current directory
@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.get_json()
    session_id = body['session']
    query = body['queryResult']['queryText'].strip().lower()

    if "start quiz" in query or "begin quiz" in query:
        question, correct_answer, correct_index = fetch_question()
        if not question:
            return jsonify({'fulfillmentText': "Sorry, I couldn't fetch a question right now."})
        
        sessions[session_id] = {
            "correct_answer": correct_answer,
            "correct_index": correct_index
        }

        return jsonify({'fulfillmentText': question + " Reply with the correct option number."})

    elif query in ['1', '2', '3', '4']:
        if session_id not in sessions:
            return jsonify({'fulfillmentText': "Please start the quiz first by saying 'start quiz'."})
        
        user_answer = int(query)
        correct = sessions[session_id]["correct_index"]
        correct_text = sessions[session_id]["correct_answer"]

        if user_answer == correct:
            reply = "🎉 Correct! Want another question? Say 'start quiz'."
        else:
            reply = f"❌ Oops! The correct answer was: {correct_text}. Say 'start quiz' to try again."

        del sessions[session_id]
        return jsonify({'fulfillmentText': reply})

    return jsonify({'fulfillmentText': "Please enter a valid option number (1-4) or say 'start quiz' to begin."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
