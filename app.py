import json
import google.generativeai as gemini
from collections import Counter
from datetime import datetime
from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sentiment_analysis_methods import (
    filter_posts_by_date,
    split_into_batches,
    analyze_sentiment_with_gemini,
    combine_batch_results
)

# Load environment variables from .env file
load_dotenv()

# Set your Gemini API key from the environment variable
gemini.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Load posts from the scrapedPostsWithCommentsAndDates.json file
with open('./ig_scraper/scrapedPostsWithCommentsAndDates.json', 'r', encoding='utf-8') as file:
    posts = json.load(file)

# Streamlit UI for date range input
st.title("Instagram Sentiment Analysis Report")
st.header("Note - Data available only for posts after 2024-04-17")
st.write("Select a date range to filter posts for sentiment analysis (Not more than a month due to request limit).")

start_date = st.date_input("Start Date", value=datetime(2024, 9, 1))
end_date = st.date_input("End Date", value=datetime(2024, 9, 7))

# Convert Streamlit date inputs to datetime
start_date = datetime.combine(start_date, datetime.min.time())
end_date = datetime.combine(end_date, datetime.max.time())

# Run sentiment analysis when the user clicks the button
if st.button("Analyze Sentiment"):
    filtered_posts = filter_posts_by_date(posts, start_date, end_date)
    
    if filtered_posts:
        batches = split_into_batches(filtered_posts)
        batch_results = []
        for i, batch in enumerate(batches):
            batch_result = analyze_sentiment_with_gemini(batch, i)
            batch_results.append(batch_result)
        
        data = combine_batch_results(batch_results)
       
        # Total positive and negative comments
        if data:
            st.header("Total Comments")
            # Display the metrics
            st.metric(label="Total Positive Comments", value=data["totalPositiveComments"])
            st.metric(label="Total Negative Comments", value=data["totalNegativeComments"])

            # Create and display the pie chart
            pie_chart_data = {
                "Sentiment": ["Positive Comments", "Negative Comments"],
                "Count": [data["totalPositiveComments"], data["totalNegativeComments"]]
            }
            
            fig = px.pie(pie_chart_data, values='Count', names='Sentiment', title='Positive vs Negative Comments')
            st.plotly_chart(fig)  # Display the pie chart in Streamlit

            # Frequent positive words
            st.header("Frequent Positive Words")
            positive_words = dict(data["frequentPositiveWords"])
            st.bar_chart(pd.Series(positive_words))  # Bar chart for frequent positive words

            # Frequent negative words
            st.header("Frequent Negative Words")
            negative_words = dict(data["frequentNegativeWords"])
            st.bar_chart(pd.Series(negative_words))  # Bar chart for frequent negative words

            # Most used emojis
            st.header("Most Used Emojis")
            for emoji, count in data["mostUsedEmojis"]:
                st.write(f"{emoji}: {count} times")

            # Most commented posts
            st.header("Most Commented Posts")
            for post in data["mostCommentedPosts"]:
                st.write(f"[View Post]({post['postUrl']}): {post['commentCount']} comments")

            # Most positive comments posts
            st.header("Posts with Most Positive Comments")
            for post in data["mostPositiveCommentsPosts"]:
                st.write(f"[View Post]({post['postUrl']}): {post['positiveCommentCount']} positive comments")

            # Most negative comments posts
            st.header("Posts with Most Negative Comments")
            for post in data["mostNegativeCommentsPosts"]:
                st.write(f"[View Post]({post['postUrl']}): {post['negativeCommentCount']} negative comments")
        else:
            st.write("Error in generating response")
    else:
        st.write("No posts found within the given date range.")
