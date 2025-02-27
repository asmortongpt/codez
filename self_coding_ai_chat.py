from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import openai
import os
import subprocess

# Initialize Flask App
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# OpenAI API Key
from dotenv import load_dotenv
load_dotenv()  # Load API key from GitHub Secrets
openai.api_key = os.getenv("OPENAI_API_KEY")

# Track API usage and progress
api_calls = 0
total_cost = 0.0
project_progress = []

# Function to estimate API cost
def estimate_cost():
    global api_calls, total_cost
    return round(api_calls * 0.002, 4)  # Assuming $0.002 per request

# Function to generate AI-written code using the latest OpenAI API
def generate_code(prompt):
    global api_calls, total_cost
    try:
        client = openai.OpenAI()  # Updated to the latest SDK usage
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an AI that writes Python code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        api_calls += 1
        total_cost = estimate_cost()
        
        return response.choices[0].message.content  # Correct way to extract response
    except Exception as e:
        return f"❌ Error generating code: {str(e)}"

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Self-Coding AI</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 0; }
            h1 { background: #222; color: white; padding: 10px; }
            #chatbox { width: 60%; height: 400px; border: 1px solid #ccc; margin: auto; overflow-y: scroll; padding: 10px; text-align: left; }
            input, button { padding: 10px; margin: 10px; width: 60%; }
            #dashboard { width: 60%; margin: auto; padding: 10px; border: 1px solid black; text-align: left; }
            .code-output { white-space: pre-wrap; background: #f4f4f4; padding: 10px; border: 1px solid #ddd; margin-top: 10px; }
        </style>
    </head>
    <body>

        <h1>💬 Self-Coding AI Chat</h1>
        
        <div id="dashboard">
            <h3>📊 Dashboard</h3>
            <p><b>API Calls:</b> <span id="api_calls">0</span></p>
            <p><b>Total Cost:</b> $<span id="total_cost">0.0000</span></p>
            <h4>Progress</h4>
            <ul id="progress_list"></ul>
        </div>

        <div id="chatbox"></div>
        <input id="input" type="text" placeholder="Enter your coding prompt...">
        <button onclick="sendMessage()">Send</button>
        <button onclick="runCode()">Run Code</button>
        <button onclick="updateDesign()">Update Design</button>

        <div id="code_output" class="code-output"></div>

        <script>
            var socket = io.connect(window.location.protocol + "//" + window.location.host);

            function sendMessage() {
                let prompt = document.getElementById("input").value;
                document.getElementById("chatbox").innerHTML += "<p><b>You:</b> " + prompt + "</p>";
                socket.emit('user_prompt', { 'prompt': prompt });
                document.getElementById("input").value = "";
            }

            function runCode() {
                socket.emit("run_code");
            }

            function updateDesign() {
                let instruction = prompt("Enter design update instructions:");
                if (instruction) {
                    socket.emit("update_design", { "message": instruction });
                }
            }

            socket.on('ai_response', function(data) {
                document.getElementById("chatbox").innerHTML += "<p><b>AI:</b> " + data.message + "</p>";
            });

            socket.on('code_output', function(data) {
                document.getElementById("code_output").innerHTML = "<h3>💻 Code Output</h3><p>" + data.output + "</p>";
            });

            socket.on("update_dashboard", function(data) {
                document.getElementById("api_calls").innerText = data.api_calls;
                document.getElementById("total_cost").innerText = data.total_cost.toFixed(4);
                document.getElementById("progress_list").innerHTML = data.progress.map(p => `<li>${p.prompt} - ${p.status}</li>`).join("");
            });
        </script>

    </body>
    </html>
    """

@socketio.on("user_prompt")
def handle_user_prompt(data):
    prompt = data["prompt"]
    socketio.emit("ai_response", {"message": f"⏳ Generating code for: {prompt}"})
    
    code = generate_code(prompt)
    
    # Save to file
    with open("generated_code.py", "w") as f:
        f.write(code)
    
    project_progress.append({"prompt": prompt, "status": "Completed"})
    
    socketio.emit("ai_response", {"message": f"✅ Code Generated!\n\n```python\n{code}\n```"})
    socketio.emit("update_dashboard", {"api_calls": api_calls, "total_cost": total_cost, "progress": project_progress})

@socketio.on("run_code")
def handle_run_code():
    try:
        output = subprocess.check_output(["python3", "generated_code.py"], stderr=subprocess.STDOUT, text=True)
        socketio.emit("code_output", {"output": f"💻 Output:\n\n{output}"})
    except subprocess.CalledProcessError as e:
        socketio.emit("code_output", {"output": f"❌ Error:\n\n{e.output}"})

@socketio.on("update_design")
def handle_design_update(data):
    project_progress.append({"prompt": data["message"], "status": "Design Updated"})
    socketio.emit("ai_response", {"message": f"✅ Design instructions received: {data['message']}"})
    socketio.emit("update_dashboard", {"api_calls": api_calls, "total_cost": total_cost, "progress": project_progress})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)