# Import necessary libraries
from flask import Flask, render_template, request, redirect, url_for, jsonify
import openai
import os
from dotenv import load_dotenv
import time
from flask_mail import Mail, Message
import speech_recognition as sr

load_dotenv()
# Set the OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Define the name of the bot
name = 'Cloud'

# Define the role of the bot
role = 'mental health counselor'

# Define the impersonated role with instructions
impersonated_role = f"""
    From now on, you are going to act as {name}. Your role is {role}.
    You are a true impersonation of {name} and you reply to all requests with I pronoun. You never give unknown information.
    Forward them to the website for more information.
    Keep the responses very short and concise.
    Do not give repetitive responses.
    Do not answer anything that is not related to mental health.
    YOU ARE NOT AN AI MODEL!
"""

# Initialize variables for chat history
explicit_input = ""
chatgpt_output = 'Chat log: /n'
cwd = os.getcwd()
i = 1

# Find an available chat history file
while os.path.exists(os.path.join(cwd, f'chat_history{i}.txt')):
    i += 1

history_file = os.path.join(cwd, f'chat_history{i}.txt')

# Create a new chat history file
with open(history_file, 'w') as f:
    f.write('\n')

# Initialize chat history
chat_history = ''

# Create a Flask web application
app = Flask(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Your email server
app.config['MAIL_PORT'] = 587  # Port for SMTP
app.config['MAIL_USERNAME'] = 'abc@gmail.com'  # Your email address
app.config['MAIL_PASSWORD'] = 'password'  # Your email password
app.config['MAIL_DEFAULT_SENDER'] = 'abc@gmail.com'  # Default sender email
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_TLS_VERSION'] = 'TLSv1_2'

mail = Mail(app)

# Function to complete chat input using OpenAI's GPT-3.5 Turbo
def chatcompletion(user_input, impersonated_role, explicit_input, chat_history):
    output = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0301",
        temperature=1,
        presence_penalty=0,
        frequency_penalty=0,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": f"{impersonated_role}. Conversation history: {chat_history}"},
            {"role": "user", "content": f"{user_input}. {explicit_input}"},
        ]
    )
    for item in output['choices']:
        chatgpt_output = item['message']['content']

    return chatgpt_output

# Function to handle user chat input
def chat(user_input):
    global chat_history, name, chatgpt_output
    current_day = time.strftime("%d/%m", time.localtime())
    current_time = time.strftime("%H:%M:%S", time.localtime())
    chat_history += f'\nUser: {user_input}\n'
    chatgpt_raw_output = chatcompletion(user_input, impersonated_role, explicit_input, chat_history).replace(f'{name}:', '')
    chatgpt_output = f'{name}: {chatgpt_raw_output}'
    chat_history += chatgpt_output + '\n'
    with open(history_file, 'a') as f:
        f.write('\n'+ current_day+ ' '+ current_time+ ' User: ' +user_input +' \n' + current_day+ ' ' + current_time+  ' ' +  chatgpt_output + '\n')
        f.close()
    return chatgpt_raw_output

# Function to get a response from the chatbot
def get_response(userText):
    return chat(userText)

# Define app routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file:
            # Save the file temporarily
            filename = uploaded_file.filename
            uploaded_file.save(filename)
            
            # Send email with attachment
            msg = Message('File Attachment', recipients=['xyz@gmail.com'])
            msg.body = 'Please find the attached file.'
            with app.open_resource(filename) as fp:
                msg.attach(filename, 'application/octet-stream', fp.read())
            mail.send(msg)
            
            return redirect(url_for('index'))
    return 'No file uploaded'

@app.route("/get")
# Function for the bot response
def get_bot_response():
    userText = request.args.get('msg')
    return str(get_response(userText))

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    r = sr.Recognizer()
    with sr.AudioFile(request.files['audio']) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)
    return jsonify({'text': text})


# Run the Flask app
if __name__ == "__main__":
    app.run()