import os
import mysql.connector
import ftplib
import schedule
import time
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
from config import FTP_HOST, FTP_USER, FTP_PASSWORD, WP_CONTENT_FOLDER, QUESTIONS_FOLDER, ANSWERS_FOLDER, WP_DB_HOST, WP_DB_USER, WP_DB_PASSWORD, WP_DB_NAME, LLAMA_MODEL

# Connect to FTP server
ftp = ftplib.FTP(FTP_HOST)
ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)

# Connect to WordPress database
cnx = mysql.connector.connect(
    user=WP_DB_USER,
    password=WP_DB_PASSWORD,
    host=WP_DB_HOST,
    database=WP_DB_NAME
)

def answer_question(question):
    try:
        url = 'http://localhost:3000/predict'
        data = {'question': question}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            answer = response.text
            return answer
        else:
            logging.error(f"Error generating answer: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error generating answer: {e}")
        return None

def get_questions():
    try:
        # Get list of questions from WordPress database
        cursor = cnx.cursor()
        query = "SELECT * FROM wp_posts WHERE post_type = 'question'"
        cursor.execute(query)
        questions = cursor.fetchall()
        return questions
    except Exception as e:
        logging.error(f"Error in get_questions(): {e}")
        return []

def answer_question_db(question):
    try:
        logging.info("Q & A bot running!")
        # Answer question using Llama model
        question_id = question[0]
        question_text = question[4]
        answer = answer_question(question_text)
        if answer is not None:
            # Update question with answer in WordPress database
            cursor = cnx.cursor()
            query = "UPDATE wp_posts SET post_content = %s WHERE ID = %s"
            cursor.execute(query, (answer, question_id))
            cnx.commit()

            # Upload answer to FTP server
            answer_file = f"{question_id}.txt"
            with open(answer_file, 'w') as file:
                file.write(answer)
            ftp.storbinary(f"STOR {WP_CONTENT_FOLDER}{ANSWERS_FOLDER}{answer_file}", open(answer_file, 'rb'))
    except Exception as e:
        logging.error(f"Error in answer_question_db(): {e}")

def monitor_questions():
    questions = get_questions()
    for question in questions:
        logging.info(f"Processing question {question[0]}")
        answer_question_db(question)

# Execute monitor_questions immediately
monitor_questions()

# Schedule monitor_questions to run every 1 minute
schedule.every(1).minutes.do(monitor_questions)  # Monitor every 1 minute

try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    logging.info("Monitoring stopped by user")
finally:
    if ftp is not None:
        ftp.quit()
    if cnx is not None:
        cnx.close()