import tweepy 
import time

f = open("twitter.txt")

# sensitive area
consumer_key = f.readline().strip()
consumer_secret = f.readline().strip()
access_token = f.readline().strip()
access_token_secret = f.readline().strip()

client = tweepy.Client(consumer_key=consumer_key,consumer_secret=consumer_secret,access_token=access_token,access_token_secret=access_token_secret)

def split_text_into_chunks(input_text, max_length=280):
    sentences = input_text.split(" ")
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_length-1:  # Add 1 for the period
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def post_text(text=''):
    n = 280
    blocks = split_text_into_chunks(text, n)
    for block in blocks:
        print("TWITTER>>", len(block), block)

    tweet_id = ""
    for i, block in enumerate(blocks):
        if i == 0:
            resp = client.create_tweet(text=block)
            tweet_id = resp.data['id']
        else:
            client.create_tweet(text=block, in_reply_to_tweet_id=tweet_id)
        time.sleep(1)