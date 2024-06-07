from flask import Flask, request, jsonify, render_template
from threading import Thread
from flask_socketio import SocketIO, emit
from flask_funcs import scrape_chat
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable CORS for SocketIO
# socketio = SocketIO(app)

@app.route('/', methods = ['GET'])
def index():
    return render_template('index.html', topic=Topic)

@app.route('/start_scraper', methods=['POST'])
def start_scraper():
    data = request.json
    # print(data)
    link = data.get('link')
    if not link:
        return jsonify({"error": "No link provided"}), 400
    
    # # Start chat scraping in a background thread
    # chat_thread = Thread(target=scrape_chat, args=(link,))
    # chat_thread.start()

    # # Start caption scraping in a background thread
    # caption_thread = Thread(target=scrape_captions, args=(link,))
    # caption_thread.start()

    # Start chat scraping in a background task
    socketio.start_background_task(scrape_chat, link)

    # Start caption scraping in a background task
    socketio.start_background_task(scrape_captions, link)


    return jsonify({"message": "Scraper started"}), 200

def send_sentiment_data(sentiment_data):
    socketio.emit('update_sentiment', sentiment_data)
    # print("Data SENT INTO EVENT SOCKETTTTTTT")

####################################################
import time
from functions import *
from langchain_google_genai import GoogleGenerativeAI
api_key = "AIzaSyALE6Vt_Vloi_Nld-EfMeoxY56neEc73Is"
llm = GoogleGenerativeAI(model="models/text-bison-001", google_api_key=api_key, temperature=0.4)

def palm_it(text):

    # text = "The Apache Hadoop software library is a framework that allows for the distributed processing of large data sets across clusters of computers using simple programming models. It is designed to scale up from single servers to thousands of machines, each offering local computation and storage. Rather than rely on hardware to deliver high-availability, the library itself is designed to detect and handle failures at the application layer, so delivering a highly-available gourane on top of a cluster of computers, each of which may be prone to failures."
    questions = ["what this news talks about "]
    question = "\n".join([ f"{i+1}- {q}" for i,q in enumerate(questions)])

    promt = f"""given the folowing text :
    {text}
    answer to thoses questions in short:

    {question}

    """
    poem = llm.predict(promt)

    print(poem)
    return poem







# link = "https://www.youtube.com/watch?v=gCNeDWCI0vo&ab_channel=AlJazeeraEnglish"

Topic= ' '
def scrape_captions(link):

    driver = getDriver()

    goToLink(link, driver)

    playButton(driver)

    # Finding the captions container
    caption_container = getCaptionsContainer(driver)
    print("Caption container Found!!")

    last_text="."
    full_text=" "
    i=0
    j=0
    global  Topic
    while True:

        try:
            # Getting the existing lines from the captions
            caption_lines = getCaptionsLines(driver)

            if len(caption_lines):
                for line in caption_lines:
                    # Extract text from each segment within a line
                    text = line.text
                    if text != last_text:
                        # producer.send('captions',value=text.encode('utf-8'))
                        last_text=text
                        # print(text)
                        full_text= full_text+text
                        i=i+1
                        if i%9==0:
                            # print(full_text)
                            Topic = palm_it(last_text)
                        
            time.sleep(1.5)
        except:
            print('No caption found')

###########################################################"


############################################

if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, debug=True)
