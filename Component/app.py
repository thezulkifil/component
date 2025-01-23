from flask import Flask, request, jsonify, render_template_string
from spacy import load

# Load the transformer-based NLP model
nlp = load("en_core_web_lg")

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Component</title>
    <link rel="icon" href="{{ url_for('static', filename='favicon.ico') }}" type="image/x-icon">
    <style>
        body {
            background-color: black;
            color: white;
            font-family: Consolas, monospace;
            text-align: center;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            width: 90%;
            max-width: 1000px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        input {
            width: 100%;
            font-size: min(5vw, 24px);
            background-color: black;
            color: white;
            border: none;
            padding: 2vh;
            margin-top: 2vh;
            outline: none;
            text-align: center;
            opacity: 0.3;
        }
        .pos-overlay {
            position: relative;
            font-size: min(4vw, 20px);
            color: #a9a9a9;
            margin-bottom: 2vh;
            white-space: normal;
            overflow: visible;
            text-align: center;
            width: 100%;
        }
        .word-pos-container {
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            margin: 0 10px;
            cursor: pointer;
        }
        .word {
            font-size: min(5vw, 24px);
            color: white;
        }
        .pos {
            font-size: min(3vw, 16px);
            color: #a9a9a9;
            margin-top: 5px;
        }
    </style>
    <script>
        async function updateOutput() {
            const sentence = document.getElementById('sentence-input').value;
            if (!sentence.trim()) {
                document.getElementById('pos-overlay').innerHTML = '';
                return;
            }

            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sentence })
            });

            if (!response.ok) {
                console.error('Error:', await response.text());
                return;
            }

            const data = await response.json();
            const posContainer = document.getElementById('pos-overlay');
            posContainer.innerHTML = data.tokens.map((word, i) => 
                i % 2 === 0 ? `<div class="word-pos-container">
                                <span class="word">${word}</span>
                                <span class="pos">${data.tokens[i + 1]}</span>
                              </div>` : ''
            ).join('');
        }
    </script>
</head>
<body>
    <div class="container">
        <div id="pos-overlay" class="pos-overlay"></div>
        <input id="sentence-input" type="text" name="sentence" placeholder="Type a sentence here..." oninput="updateOutput()">
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    sentence = data.get('sentence', '').strip()

    if not sentence:
        return jsonify({"error": "No sentence provided"}), 400

    try:
        doc = nlp(sentence)
        tokens = []
        i = 0

        while i < len(doc):
            token = doc[i]
            # Check if the current token and the next token form a contraction
            if i + 1 < len(doc) and doc[i + 1].text.startswith("'") and token.text + doc[i + 1].text in sentence:
                # Combine the contraction into a single token
                combined_text = token.text + doc[i + 1].text
                tokens.extend([combined_text, token.pos_])  # Add the combined word and its POS tag
                i += 2  # Skip the next token since we've combined it
            else:
                # Add the token as-is
                tokens.extend([token.text, token.pos_])
                i += 1

        # Convert POS tags to human-readable format
        tokens = [tokens[i] if i % 2 == 0 else nlp.vocab[tokens[i]].text for i in range(len(tokens))]

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"tokens": tokens})

if __name__ == '__main__':
    app.run(debug=True)