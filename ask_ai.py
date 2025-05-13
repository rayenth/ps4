from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import base64
import io
import PyPDF2

app = Flask(__name__)
# Fix: Properly initialize CORS with the app instance
CORS(app)  # This enables CORS for all routes

def extract_text_from_pdf(base64_pdf):
    try:
        pdf_data = base64.b64decode(base64_pdf)
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        print("PDF extraction failed:", e)
        return ""

def ask_ollama(prompt):
    try:
        process = subprocess.Popen(
            ['ollama', 'run', 'llama3'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=prompt)
        if stderr:
            print("Ollama error:", stderr)
        return stdout.strip()
    except Exception as e:
        print("Subprocess error:", e)
        return "Error running Ollama."

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        pdf = data.get('pdf', '').strip()
        if not prompt or not pdf:
            return jsonify({'error': 'Prompt and PDF are required'}), 400
        extracted_text = extract_text_from_pdf(pdf)
        full_prompt = f"Here is the PDF content:\n\n{extracted_text}\n\nAnswer this question based on the document:\n{prompt}"
        response = ask_ollama(full_prompt)
        return jsonify({'response': response})
    except Exception as e:
        print("Server error:", e)
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(port=3000, debug=True)