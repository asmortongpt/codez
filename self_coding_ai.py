import openai
import git
import os

# Load OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to generate code using OpenAI Codex
def generate_code(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "You are an AI that writes Python code."},
                  {"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"]

# Function to write code to a file
def write_code(file_name, code):
    with open(file_name, "w") as f:
        f.write(code)

# GitHub Integration
def commit_and_push(repo_path, commit_message):
    repo = git.Repo(repo_path)
    repo.git.add(update=True)
    repo.index.commit(commit_message)
    origin = repo.remote(name='origin')
    origin.push()

# Example Usage
if __name__ == "__main__":
    prompt = "Write a Python script that prints 'Hello, World!'"
    code = generate_code(prompt)
    write_code("hello_world.py", code)

    # Commit and push to GitHub
    commit_and_push(".", "Generated Hello World script")
    print("🚀 Code pushed to GitHub successfully!")
