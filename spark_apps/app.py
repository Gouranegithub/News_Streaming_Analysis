
import logging
import time
from pyspark.sql import SparkSession
from pyspark.sql.streaming import StreamingQuery
from pyspark.sql.functions import col, from_json, from_unixtime, udf
from pyspark.sql.types import StructType, StructField, StringType, LongType, IntegerType
import pandas as pd
from langchain_google_genai import GoogleGenerativeAI






logging.basicConfig(level=logging.INFO)


SPARK_MASTER_IP = "local"
KAFKA_BROKER_IP = "INSIDE://kafka:9092"
KAFKA_TOPIC = "Chats"

json_schema = StructType([
        StructField("action_type", StringType(), True),
        StructField("message", StringType(), True),
        StructField("message_id", StringType(), True),
        StructField("timestamp", LongType(), True),
        StructField("author", StructType([
            StructField("name", StringType(), True),
            StructField("images", StructType([
                StructField("url", StringType(), True),
                StructField("id", StringType(), True),
                StructField("width", LongType(), True),
                StructField("height", LongType(), True)
            ]), True),
            StructField("id", StringType(), True)
        ]), True),
        StructField("message_type", StringType(), True)
    ])

spark = SparkSession \
    .builder \
    .appName("kafka handler") \
    .config("spark.streaming.stopGracefullyOnShutdown", True) \
    .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0') \
    .config("spark.sql.shuffle.partitions", 4) \
    .master(SPARK_MASTER_IP) \
    .getOrCreate()



#-----------------------------------------------------------------------------------------------
import nltk
nltk.download('punkt')
nltk.download('stopwords')

import pandas as pd
from chat_downloader import ChatDownloader
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
from typing import Tuple
import json
from confluent_kafka import Producer


def palm_it(text):
    api_key = "Google_Palm_Token" #u need to add the personal token 
    llm = GoogleGenerativeAI(model="models/text-bison-001", google_api_key=api_key, temperature=0.5)
   
    #text = "The Apache Hadoop software library is a framework that allows for the distributed processing of large data sets across clusters of computers using simple programming models. It is designed to scale up from single servers to thousands of machines, each offering local computation and storage. Rather than rely on hardware to deliver high-availability, the library itself is designed to detect and handle failures at the application layer, so delivering a highly-available gourane on top of a cluster of computers, each of which may be prone to failures."
    questions = ["what the text talks about in one word"]
    question = "\n".join([ f"{i+1}- {q}" for i,q in enumerate(questions)])

    promt = f"""given the folowing text :
    {text}
    answer to thoses questions:

    {question}

    """
    poem = llm.predict(promt)
    
    print(poem)
    return poem


#print(palm_it('this is talking about the importance of the socity'))
palm_it_udf = udf(palm_it, StringType())
spark.udf.register("palm_it_udf", palm_it_udf)


 
# Define the schema for the NRC Emotion Lexicon
nrc_schema = StructType([
    StructField("word", StringType(), True),
    StructField("emotion", StringType(), True),
    StructField("association", IntegerType(), True)
])

# Define the file path
file_path = "/opt/spark/data/NRC_emotion_lexicon_wordlevel_alphabetized_v0.92.txt"
text_file = spark.read.text(file_path)

# Load NRC Emotion Lexicon
nrc = pd.read_csv(file_path, names=['word', 'emotion', 'association'], sep='\t')

nrc_broadcast = spark.sparkContext.broadcast(nrc)

def detect_emotion_and_sentiment(text: str)->str:
    """
    It returns the emotion of the text and the global sentiment.
    """
    if text== None or text== '' or text== 'null':
        return 'None'
    else:
        words = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        words = [word for word in words if word.isalpha() and word not in stop_words]

        emotion_counter = Counter()
        sentiment_counter = Counter()
        for word in words:
            emotions = nrc[(nrc['word'] == word) & (nrc['association'] == 1) & (~nrc['emotion'].isin(['positive', 'negative']))]['emotion']
            sentiment = nrc[(nrc['word'] == word) & (nrc['association'] == 1) & (nrc['emotion'].isin(['positive', 'negative']))]['emotion']
            
            emotion_counter.update(emotions)
            sentiment_counter.update(sentiment)

        most_common_emotion = emotion_counter.most_common(1)[0][0] if emotion_counter else 'neutral'
        positive_sentiment_count = sentiment_counter.get('positive', 0)
        negative_sentiment_count = sentiment_counter.get('negative', 0)
        
        overall_sentiment = ('positive' if positive_sentiment_count > negative_sentiment_count else 'negative' 
                            if negative_sentiment_count > positive_sentiment_count else 'neutral')

        return most_common_emotion




print(detect_emotion_and_sentiment('good day'))
# Register the UDF with Spark
detect_emotion_and_sentiment_udf = udf(lambda txt:detect_emotion_and_sentiment(txt), StringType())
spark.udf.register("detect_emotion_and_sentiment_udf",detect_emotion_and_sentiment_udf)



#-----------------------------------------------------------------------------------------------


print("reading kafka")

streaming_df = spark.readStream\
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER_IP) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()




print("read kafka")


json_df = streaming_df.selectExpr("cast(value as string) as value")

json_expanded_df = json_df.withColumn("value", from_json(json_df["value"], json_schema)).select("value.*") 
json_expanded_df = json_expanded_df.withColumn("date", from_unixtime(col("timestamp") / 1000000).cast("timestamp"))
#json_expanded_df = json_expanded_df.withColumn("palmed message", palm_it_udf(col("message")))


json_expanded_df = json_expanded_df.withColumn("emotion_and_sentiment", detect_emotion_and_sentiment_udf(col("message")))



df_selected = json_expanded_df.select(col("date"), col("author.name").alias("name"), col("message"), col("emotion_and_sentiment"))

    

# # Define the file path
# file_path = "/opt/spark/data/NRC_emotion_lexicon_wordlevel_alphabetized_v0.92.txt"

# # Read the text file
# text_file_df = spark.read.text(file_path).toDF("line")


# # Show the content of the file
# text_file_df.show()



#-----------------------------------------------test------------------------------------------



# def scrape_chat(url: str):
#     chat = ChatDownloader().get_chat(url)

#     for index, msg in enumerate(chat):
#         print(msg['message'])
#         print(detect_emotion_and_sentiment(msg['message']))
#         print(f"{index+1} chat messages read!!!!")
#         send_to_kafka('Chats', msg)                                       # 7YD HADI wrunni lcode
#         if index > 30: break


    





# url = 'https://www.youtube.com/watch?v=gCNeDWCI0vo&ab_channel=AlJazeeraEnglish'
# scrape_chat(url)

#-----------------------------------------------------end test ----------------------------------------------------





query1 = df_selected.writeStream\
    .trigger(processingTime="2 seconds") \
    .format("console") \
    .outputMode("update") \
    .start()


CHECKPOINT_LOCATION = "/opt/spark/data"

query = df_selected.selectExpr("to_json(struct(*)) AS value") \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER_IP) \
    .option("topic", 'Output') \
    .option("checkpointLocation", CHECKPOINT_LOCATION) \
    .trigger(processingTime="2 seconds") \
    .outputMode("update") \
    .start()

query.awaitTermination()
print("finished writing")

query1.awaitTermination()
