from flask import Flask, request, jsonify, render_template
import os
import requests
import uuid
import subprocess
import tempfile
import pandas as pd

app = Flask(__name__)

key = os.getenv("API_KEY")

context_sheet = None


# Your UI — served at the root
@app.route('/')
def index():
    return render_template('index.html')


@app.route("/runCode", methods=["POST"])
def run_code():
    if not request.json:
        return jsonify({"error": "Invalid JSON format in request"}), 400
    code = request.json.get("code")
    if not code:
        return jsonify({"error": "No code provided"}), 400

    prepend_lines = """
    options(warn=1)
    png("data/output.png")
    .libPaths("r_libs")
    """

    # Combine the lines
    full_code = prepend_lines.strip() + "\n\n" + code

    # Save R code to file
    os.makedirs("data", exist_ok=True)
    r_path = "data/script.R"
    with open(r_path, "w") as f:
        f.write(full_code)

    # Run the R script
    try:
        process = subprocess.Popen(["Rscript", r_path],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)

        stdout, stderr = process.communicate()

        # You may want to filter only relevant lines (optional)
        log_output = stdout + ("\n" + stderr if stderr else "")

        return jsonify({"output": log_output.strip()})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.output.decode()})


# AI function endpoint
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    text = data.get('text', '')
    result = process_text(text)
    key = os.getenv("API_KEY")
    return jsonify({'result': get_best_r_code_from_ai(text)})


@app.route('/upload', methods=['POST'])
def upload_file():
    global context_sheet

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Read the Excel file into a DataFrame
        context_sheet = pd.read_excel(file)
        return jsonify({"result": "File uploaded and stored successfully."})
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 500


# Replace this with your AI logic
def process_text(text):
    return text[::-1]  # Example: reverse the string


def get_best_r_code_from_ai(question):

    if (context_sheet is not None):
        prompt = f"""
        You are an expert in R programming. A user asked for: "{question}".

        Provide the user with functional R code to fufill the request. Include any packages
        that need to be downloaded,
        along with the code.
        Rules:
        1. You must provide your answer with the code to insall the packages, followed
        by the code to run the analysis.
        2. You must include nothing else
        3. All variables must be labled input1, input2, ect
        4. You must not include any wrapper for the code, just the code itself.
        5. you must write the package installation line in the format:
        install.packages("package", repos = "https://cloud.r-project.org")
        6. You must use the data from the following dataframe: {context_sheet} for the
        analysis. The user will specify the data that they want to use from the
        dataframe, you must find the data that the user is asking for, and use it in
        the program.
        """

    else:
        prompt = f"""
        You are an expert in R programming. A user asked for: "{question}".

        Provide the user with functional R code to fufill the request. Include any packages
        that need to be downloaded,
        along with the code.
        Rules:
        1. You must provide your answer with the code to insall the packages, followed
        by the code to run the analysis.
        2. You must include nothing else
        3. All variables must be labled input1, input2, ect
        4. You must not include any wrapper for the code, just the code itself.
        5. you must write the package installation line in the format:
        install.packages("package", repos = "https://cloud.r-project.org")
        """

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    data = {
        "model":
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",  # Free Together.ai model
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "max_tokens": 1024,
        "temperature": 0.7
    }

    response = requests.post("https://api.together.xyz/v1/chat/completions",
                             headers=headers,
                             json=data)
    result = response.json()

    content = result["choices"][0]["message"]["content"]
    print("\n=== AI Response ===\n", content)
    return content


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
