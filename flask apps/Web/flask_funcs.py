import time, json, os
#from kafka import KafkaProducer
from confluent_kafka import Producer
from chat_downloader import ChatDownloader
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import pandas as pd
from typing import Tuple
from functions import getDriver, goToLink, playButton, getCaptionsContainer, getCaptionsLines



from langchain_google_genai import GoogleGenerativeAI
api_key = "AIzaSyALE6Vt_Vloi_Nld-EfMeoxY56neEc73Is"
llm = GoogleGenerativeAI(model="models/text-bison-001", google_api_key=api_key, temperature=0.5)

def palm_it(text):

    #text = "The Apache Hadoop software library is a framework that allows for the distributed processing of large data sets across clusters of computers using simple programming models. It is designed to scale up from single servers to thousands of machines, each offering local computation and storage. Rather than rely on hardware to deliver high-availability, the library itself is designed to detect and handle failures at the application layer, so delivering a highly-available gourane on top of a cluster of computers, each of which may be prone to failures."
    questions = ["what the text talks about "]
    question = "\n".join([ f"{i+1}- {q}" for i,q in enumerate(questions)])

    promt = f"""given the folowing text :
    {text}
    answer to thoses questions in one word:

    {question}

    """
    poem = llm.predict(promt)

    print(poem)
    return poem

def scrape_captions(link):
    # Getting the chrome driver
    driver = getDriver()

    # Going to the link
    goToLink(link, driver)

    playButton(driver)

    # Finding the captions container
    caption_container = getCaptionsContainer(driver)
    print("Caption container Found!!")

    # Kafka producer setup
    # producer = Producer(bootstrap_servers='localhost:9093')

    last_text = "."
    while True:
        try:
            # Getting the existing lines from the captions
            caption_lines = getCaptionsLines(driver)

            if len(caption_lines):
                for line in caption_lines:
                    # Extract text from each segment within a line
                    text = line.text
                    if text != last_text:
                        # print(text)
                        # producer.send('captions', value=text.encode('utf-8'))
                        last_text = text
                        palm_it('Captions',text)

            time.sleep(1.5)
        except:
            print('No caption found')

producer = Producer({'bootstrap.servers': 'localhost:9093'})
def send_to_kafka(topic, data):
    # Serialize the data to JSON
    print('1')
    serialized_data = json.dumps(data).encode('utf-8')
    # Produce the message
    print('2')
    producer.produce(topic, serialized_data)
    # Flush the producer to ensure all messages are sent
    producer.flush()
    print('Message sent to kafka')

Output_topic="Output"
sentiments=[]
def consume_from_kafka(Output_topic):
    import json
    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
    Output_topic,
    bootstrap_servers='localhost:9093',
    auto_offset_reset='earliest',  # Start consuming from the beginning (optional)
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))  # Deserialize JSON messages
    )
    global sentiments
    try:
        # Continuously consume messages
        for message in consumer:
            message_data = message.value
            print(f"Received message: {message_data}")
            # Access specific fields:
            #date = message_data.get('date')
            #name = message_data.get('name')
            #message = message_data.get('message')
            sentiments.append(message_data.get('emotion_and_sentiment'))
    finally:
    # Close the consumer to avoid resource leaks
        consumer.close()


def scrape_chat(url: str):
    from app import send_sentiment_data

    chat = ChatDownloader().get_chat(url)

    for message in chat:                        # iterate over messages
        chat.print_formatted(message)
        send_to_kafka('Chats', message)
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    total_messages = 0
    
    sentiments=[]
    consume_from_kafka('Output')

    for sentiment in sentiments:
        total_messages += 1
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1

        # Calculate percentages
        sentiment_data = {
            'positive': (sentiment_counts['positive'] / total_messages) * 100,
            'negative': (sentiment_counts['negative'] / total_messages) * 100,
            'neutral': (sentiment_counts['neutral'] / total_messages) * 100
        }
        send_sentiment_data(sentiment_data)
