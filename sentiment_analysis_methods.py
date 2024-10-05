import json
import google.generativeai as gemini
from collections import Counter
from datetime import datetime

# Function to filter posts by date range
def filter_posts_by_date(posts, start_date, end_date):
    filtered_posts = []
    for post in posts:
        post_date = datetime.strptime(post['postDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
        
        if start_date <= post_date <= end_date:
            post.pop('imageUrl', None)
            post['comments'] = post['comments'][:200]
            filtered_posts.append(post)
    
    return filtered_posts

# Function to split posts into batches based on token count
def split_into_batches(posts, max_tokens=9000):
    current_batch = []
    total_tokens = 0
    batches = []
    model = gemini.GenerativeModel("gemini-1.5-flash-latest")

    for post in posts:
        post_token_count = model.count_tokens(json.dumps(post, ensure_ascii=False)).total_tokens
        
        if total_tokens + post_token_count > max_tokens:
            batches.append(current_batch)
            current_batch = []
            total_tokens = 0

        current_batch.append(post)
        total_tokens += post_token_count

    if current_batch:
        batches.append(current_batch)

    return batches

# Function to analyze sentiment using Gemini for each batch
def analyze_sentiment_with_gemini(posts_batch, batch_index):
    prompt = prompt = f"""
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

    !Important return the response in JSON format only with no extra text 
    !Important the key should be same as mentioned in the prompt 
    """
    model = gemini.GenerativeModel("gemini-1.5-flash-latest")
    response = model.generate_content(prompt)
    print(response)
    # Assuming the response contains the text directly or as an attribute
    try:
        cleaned_response = response.text  # Adjust based on actual structure
        cleaned_response = cleaned_response.replace("```json\n", "").replace("\n```", "")
        return json.loads(cleaned_response)
    except AttributeError:
        print("Response does not have the expected attributes. Please check the structure of the response.")
        return {}

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
        final_result["totalPositiveComments"] += result.get("totalPositiveComments", 0)
        final_result["totalNegativeComments"] += result.get("totalNegativeComments", 0)
        final_result["frequentPositiveWords"].update(result.get("frequentPositiveWords", []))
        final_result["frequentNegativeWords"].update(result.get("frequentNegativeWords", []))
        final_result["mostUsedEmojis"].update(result.get("mostUsedEmojis", []))
        final_result["mostCommentedPosts"].extend(result.get("mostCommentedPosts", []))
        final_result["mostPositiveCommentsPosts"].extend(result.get("mostPositiveCommentsPosts", []))
        final_result["mostNegativeCommentsPosts"].extend(result.get("mostNegativeCommentsPosts", []))

    final_result["frequentPositiveWords"] = final_result["frequentPositiveWords"].most_common(10)
    final_result["frequentNegativeWords"] = final_result["frequentNegativeWords"].most_common(10)
    final_result["mostUsedEmojis"] = final_result["mostUsedEmojis"].most_common(5)

    final_result["mostCommentedPosts"] = sorted(final_result["mostCommentedPosts"], key=lambda p: p.get('commentCount', 0), reverse=True)[:5]
    final_result["mostPositiveCommentsPosts"] = sorted(final_result["mostPositiveCommentsPosts"], key=lambda p: p.get('positiveCommentCount', 0), reverse=True)[:5]
    final_result["mostNegativeCommentsPosts"] = sorted(final_result["mostNegativeCommentsPosts"], key=lambda p: p.get('negativeCommentCount', 0), reverse=True)[:5]

    return final_result
