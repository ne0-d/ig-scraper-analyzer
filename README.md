# Instagram Comments Scraper and Sentiment Analysis

This project allows you to scrape comments from Instagram posts and perform sentiment analysis on the comments using the Gemini API. It provides insights into the sentiment surrounding your posts and identifies trends in user comments.

## Features

- Scrape comments from Instagram posts.
- Analyze sentiment of comments in multiple languages (English, Hindi, and Romanized Hindi).
- Generate reports on positive and negative comments.
- Extract frequent words, emojis, and most commented posts.
- Visualize sentiment analysis results.

## Requirements

To run this project, you'll need the following libraries:

- `google-generativeai` for sentiment analysis.
- `pandas` for data manipulation.
- `numpy` for numerical operations.
- `matplotlib` for visualizing data.
- `streamlit` for creating a web interface.

You can install these libraries using:

```bash
pip install google-generativeai pandas numpy matplotlib streamlit
```
## Getting Started
Prerequisites
Python 3.x installed on your machine.
Access to the Gemini API. Make sure to set up your credentials.
Setup
Clone the repository:

```bash
Copy code
git clone https://github.com/ne0-d/ig-scraper-analyzer.git
cd instagram-comments-scraper
```

### Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### Install the required packages:

```bash
pip install -r requirements.txt
Environment Variables for Google Gemini Setup
```
To use the Gemini API, you'll need to set up your environment variables for authentication. Create a .env file in the root of your project and add the following:

```plaintext
GEMINI_API_KEY=your_api_key_here
```
Replace your_api_key_here with your actual API key. You can use the python-dotenv library to load these variables if needed.

## Usage
Update the configuration in your script to include your Instagram account and any specific post URLs you want to scrape.

Run the Streamlit application:

```bash
streamlit run app.py
Open your web browser and go to http://localhost:8501 to view the application.
```

## Note on API Usage
Make sure to respect Instagram's terms of service while scraping data. Additionally, ensure that your usage of the Gemini API complies with its usage policies.


## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements
Thanks to Google's Gemini API for providing powerful sentiment analysis capabilities.
Thanks to the open-source community for their contributions and support.

