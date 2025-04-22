from flask import Flask, request, jsonify, send_from_directory
import requests
from flask_cors import CORS
import os
from random import shuffle

# Configure Flask to serve index.html from frontend folder
app = Flask(__name__, static_folder="../frontend")
CORS(app)

# Store the current question and answer for each session
sessions = {}

TRIVIA_API_URL = "https://opentdb.com/api.php?amount=1&type=multiple"

def fetch_question():
    res = requests.get(TRIVIA_API_URL)
    if res.status_code != 200:
        return None, None, None

    data = res.json()['results'][0]
    question = data['question']
    correct = data['correct_answer']
    options = data['incorrect_answers']
    options.append(correct)
    shuffle(options)

    formatted_question = f"{question} " + " ".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    correct_index = options.index(correct) + 1

    return formatted_question, correct, correct_index

# ✅ Serve index.html for frontend display
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.get_json()
    session_id = body['session']
    query = body['queryResult']['queryText'].strip().lower()

    # If user says "start quiz"
    if "start quiz" in query or "begin quiz" in query:
        question, correct_answer, correct_index = fetch_question()
        if not question:
            return jsonify({'fulfillmentText': "Sorry, I couldn't fetch a question right now."})

        sessions[session_id] = {
            "correct_answer": correct_answer,
            "correct_index": correct_index
        }

        return jsonify({'fulfillmentText': question + " Reply with the correct option number."})

    # If it's a number (1 to 4)
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
    app.run(debug=True)
