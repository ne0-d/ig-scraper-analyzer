import json
import google.generativeai as gemini
from collections import Counter
import emoji
from datetime import datetime
from dotenv import load_dotenv
import os
from math import ceil

# Load environment variables from .env file
load_dotenv()

# Set your Gemini API key from the environment variable
gemini.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Load posts from the scrapedPostsWithCommentsAndDates.json file
with open('scrapedPostsWithCommentsAndDates.json', 'r', encoding='utf-8') as file:
    posts = json.load(file)

# Function to filter posts by date range and remove unwanted fields
def filter_posts_by_date(posts, start_date, end_date):
    filtered_posts = []
    for post in posts:
        # Parse the 'postDate' using the full ISO 8601 format
        post_date = datetime.strptime(post['postDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Check if the post date is within the provided date range
        if start_date <= post_date <= end_date:
            # Remove 'postUrl' and 'imageUrl' as they are not needed
            post.pop('imageUrl', None)
            
            # Limit the comments to 200 if there are more than 200 comments
            post['comments'] = post['comments'][:200]
            
            filtered_posts.append(post)
    
    return filtered_posts

# Function to split posts into batches based on token count
def split_into_batches(posts, max_tokens=9000):
    current_batch = []
    total_tokens = 0
    batches = []
    model = gemini.GenerativeModel("gemini-1.5-pro-latest")

    for post in posts:
        # Estimate token count for the current post (can also use a more sophisticated method)
        post_token_count = model.count_tokens(json.dumps(post, ensure_ascii=False)).total_tokens
        print(post_token_count)
        
        if total_tokens + post_token_count > max_tokens:
            # If adding this post exceeds token limit, store the current batch and start a new one
            batches.append(current_batch)
            current_batch = []
            total_tokens = 0

        current_batch.append(post)
        total_tokens += post_token_count

    # Append the last batch if it has any posts
    if current_batch:
        batches.append(current_batch)

    return batches

# Function to analyze sentiment using Gemini for each batch
def analyze_sentiment_with_gemini(posts_batch, batch_index):
    prompt = f"""
    Please analyze the following Instagram posts and their comments. 
    The comments are a mix of English, Hindi, and Romanized Hindi. Consider 'Jai Shree Ram' as a positive sentiment.

    Posts:
    {json.dumps(posts_batch, ensure_ascii=False)}

    You are expected to extract and return the analysis in a structured JSON response with **exactly** the following fields and key names:
    1. "totalPositiveComments": The exact number of positive comments across all posts.
    2. "totalNegativeComments": The exact number of negative comments across all posts.
    3. "frequentPositiveWords": A list of the top 10 most frequent positive words and bigrams, based on the analysis of all comments.
    4. "frequentNegativeWords": A list of the top 10 most frequent negative words and bigrams, based on the analysis of all comments.
    5. "collectiveSentiment": The overall sentiment over the month, which can be "positive", "negative", or "neutral".
    6. "mostCommentedPosts": A list of posts with the most comments, each object in this list should have the following fields:
        - "postUrl": The URL of the post.
        - "commentCount": The total number of comments for that post.
    7. "mostPositiveCommentsPosts": A list of the posts with the most positive comments, each object should have:
        - "postUrl": The URL of the post.
        - "positiveCommentCount": The number of positive comments for that post.
    8. "mostNegativeCommentsPosts": A list of the posts with the most negative comments, each object should have:
        - "postUrl": The URL of the post.
        - "negativeCommentCount": The number of negative comments for that post.
    9. "mostUsedEmojis": A list of the top 5 most frequently used emojis across all comments.

    Ensure that the JSON response follows this structure exactly and only return the JSON response without any extra text, comments, or explanations.
    !Important reutnr the response in JSON format only with no extra text 
    !Important the key should be same as mentioned in the prompt 
    """

    # Initialize the model (use the version you are working with)
    model = gemini.GenerativeModel("gemini-1.5-flash-latest")

    # Process the batch
    response = model.generate_content(prompt)
    cleaned_response = response.text.replace("```json\n", "").replace("\n```", "")
    response_data = json.loads(cleaned_response)
    
    # Save response to file for this batch
    batch_output_file = f'sentiment_results_batch_{batch_index}.json'
    with open(batch_output_file, 'w', encoding='utf-8') as f:
        json.dump(response_data, f, ensure_ascii=False, indent=2)

    print(f"Batch {batch_index} sentiment analysis results saved to {batch_output_file}")
    return response_data

# Function to combine batch results
def combine_batch_results(batch_results):
    final_result = {
        "totalPositiveComments": 0,
        "totalNegativeComments": 0,
        "frequentPositiveWords": Counter(),
        "frequentNegativeWords": Counter(),
        "mostUsedEmojis": Counter(),
        "mostCommentedPosts": [],
        "mostPositiveCommentsPosts": [],
        "mostNegativeCommentsPosts": [],
    }

    for result in batch_results:
        # Use .get() with default values to handle missing keys
        final_result["totalPositiveComments"] += result.get("totalPositiveComments", 0)
        final_result["totalNegativeComments"] += result.get("totalNegativeComments", 0)
        final_result["frequentPositiveWords"].update(result.get("frequentPositiveWords", []))
        final_result["frequentNegativeWords"].update(result.get("frequentNegativeWords", []))
        final_result["mostUsedEmojis"].update(result.get("mostUsedEmojis", []))

        # Append post data, avoiding duplicates by checking postUrl, use .get() to avoid missing data
        final_result["mostCommentedPosts"].extend(result.get("mostCommentedPosts", []))
        final_result["mostPositiveCommentsPosts"].extend(result.get("mostPositiveCommentsPosts", []))
        final_result["mostNegativeCommentsPosts"].extend(result.get("mostNegativeCommentsPosts", []))

    # Convert Counters back to lists of most common items
    final_result["frequentPositiveWords"] = final_result["frequentPositiveWords"].most_common(10)
    final_result["frequentNegativeWords"] = final_result["frequentNegativeWords"].most_common(10)
    final_result["mostUsedEmojis"] = final_result["mostUsedEmojis"].most_common(5)

    # Sort posts after combining batches, ensure appropriate sorting by comment count and positive/negative counts
    final_result["mostCommentedPosts"] = sorted(final_result["mostCommentedPosts"], key=lambda p: p.get('commentCount', 0), reverse=True)[:5]
    final_result["mostPositiveCommentsPosts"] = sorted(final_result["mostPositiveCommentsPosts"], key=lambda p: p.get('positiveCommentCount', 0), reverse=True)[:5]
    final_result["mostNegativeCommentsPosts"] = sorted(final_result["mostNegativeCommentsPosts"], key=lambda p: p.get('negativeCommentCount', 0), reverse=True)[:5]

    return final_result


# Example usage: Filter posts from a specific date range (YYYY-MM-DD format)
start_date = datetime(2024, 9, 1)
end_date = datetime(2024, 9, 30)
filtered_posts = filter_posts_by_date(posts, start_date, end_date)

# Batch process the filtered posts and analyze sentiment
if filtered_posts:
    batches = split_into_batches(filtered_posts)
    batch_results = []
    for i, batch in enumerate(batches):
        batch_result = analyze_sentiment_with_gemini(batch, i)
        # with open(f'sentiment_results_batch_{i}.json', 'r', encoding='utf-8') as file:
        #     batch_result = json.load(file)
        batch_results.append(batch_result)

    # Combine the results from all batches
    final_results = combine_batch_results(batch_results)

    # Save final results to file
    final_output_file = 'final_sentiment_results.json'
    with open(final_output_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)

    print(f"Final combined sentiment analysis results saved to {final_output_file}")
else:
    print("No posts found within the given date range.")
