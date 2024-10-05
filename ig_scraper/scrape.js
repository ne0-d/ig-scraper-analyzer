const puppeteer = require('puppeteer');
const fs = require('fs');

// Function to login to Instagram
async function loginToInstagram(page, username, password) {
    await page.goto('https://www.instagram.com/accounts/login/', { waitUntil: 'networkidle2' });

    await page.type('input[name="username"]', username);
    await page.type('input[name="password"]', password);

    await page.click('button[type="submit"]');
    await page.waitForNavigation({ waitUntil: 'networkidle2' });

    console.log("Logged in successfully!");
}

// Function to extract posts from a profile
async function extractPosts(page, maxPosts = 3) {
    let posts = [];
    let previousHeight = 0;

    while (posts.length < maxPosts) {
        const newPosts = await page.$$eval('div._ac7v.xras4av.xgc1b0m.xat24cr.xzboxd6', postElements => {
            return postElements.map(post => {
                const postUrl = post.querySelector('a._a6hd')?.href || 'No post URL';
                const imageUrl = post.querySelector('img')?.src || 'No image URL';
                const caption = post.querySelector('img')?.alt || 'No caption';
                return { postUrl, imageUrl, caption };
            });
        });

        // Avoid duplicates
        posts = [...new Set([...posts, ...newPosts])];

        previousHeight = await page.evaluate('document.body.scrollHeight');
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');

        await new Promise(resolve => setTimeout(resolve, 3000));

        const newHeight = await page.evaluate('document.body.scrollHeight');
        if (newHeight === previousHeight) {
            console.log('No more content to load');
            break;
        }

        console.log(`Loaded ${posts.length} posts so far...`);
    }

    console.log('Scraped Posts:', posts.length);
    return posts;
}

// Function to scroll and load all comments for a post
async function loadAllComments(page, commentsContainerSelector, maxComments = 500) {
    let lastHeight = await page.evaluate((commentsContainerSelector) => {
        const commentsContainer = document.querySelector(commentsContainerSelector);
        return commentsContainer.scrollHeight;
    }, commentsContainerSelector);

    let totalCommentsLoaded = 0;

    while (true) {
        await page.evaluate((commentsContainerSelector) => {
            const commentsContainer = document.querySelector(commentsContainerSelector);
            commentsContainer.scrollTo(0, commentsContainer.scrollHeight);
        }, commentsContainerSelector);

        await new Promise(resolve => setTimeout(resolve, 2000));

        const newHeight = await page.evaluate((commentsContainerSelector) => {
            const commentsContainer = document.querySelector(commentsContainerSelector);
            return commentsContainer.scrollHeight;
        }, commentsContainerSelector);

        const currentCommentsCount = await page.$$eval(
            'div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1cy8zhl.x1oa3qoh.x1nhvcw1',
            commentElements => commentElements.length
        );

        if (currentCommentsCount >= maxComments || newHeight === lastHeight) {
            break;
        }

        lastHeight = newHeight;
    }
}

// Function to extract comments for a post
async function extractComments(page, postUrl, maxComments = 500) {
    await page.goto(postUrl, { waitUntil: 'networkidle2' });

    const commentsContainerSelector = 'div.x5yr21d.xw2csxc.x1odjw0f.x1n2onr6';
    await page.waitForSelector(commentsContainerSelector);

    await loadAllComments(page, commentsContainerSelector, maxComments);
    const postDate = await page.$eval('time[class="x1p4m5qa"]', timeElement => timeElement.getAttribute('datetime'));

    const comments = await page.$$eval(
        'div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1cy8zhl.x1oa3qoh.x1nhvcw1',
        (commentElements, maxComments) => {
            return commentElements.slice(0, maxComments).map(comment => {
                const commentText = comment.querySelector('span[class^="x1lliihq"]')?.textContent || '';
                return commentText;
            });
        },
        maxComments
    );

    console.log(`Extracted ${comments.length} comments and date for post ${postUrl}`);

    // Return post data including comments and date
    return { comments, postDate };
}

// Append post data to JSON file after scraping each post
function appendDataToFile(postData) {
    const filePath = 'scrapedPostsWithCommentsAndDates.json';

    // Check if file exists, and if not, create an empty array
    if (!fs.existsSync(filePath)) {
        fs.writeFileSync(filePath, '[]', 'utf8');
    }

    // Read existing data
    const existingData = JSON.parse(fs.readFileSync(filePath, 'utf8'));

    // Append new post data
    existingData.push(postData);

    // Write updated data back to the file
    fs.writeFileSync(filePath, JSON.stringify(existingData, null, 2), 'utf8');
}

// Main function to scrape Instagram profile
async function scrapeInstagramClone(profileUrl, username, password) {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    try {
        // Step 1: Login to Instagram
        await loginToInstagram(page, username, password);

        // Step 2: Navigate to the profile page
        await page.goto(profileUrl, { waitUntil: 'networkidle2' });

        // Step 3: Extract posts
        const posts = await extractPosts(page, 5000); // Limit to 5000 posts

        // Step 4: Extract comments for each post and append data after each post
        for (let post of posts) {
            if (post.postUrl !== 'No post URL') {
                const { comments, postDate } = await extractComments(page, post.postUrl, 500); // Limit to 500 comments
                post.comments = comments;
                post.postDate = postDate; // Store the extracted post date

                // Append each post data to the file
                appendDataToFile(post);
            }
        }

        console.log('Scraping completed and data appended to file.');
    } catch (error) {
        console.error('Error during scraping:', error);
    } finally {
        await browser.close();
    }
}

// Replace these with actual username, password, and profile URL for Instagram
const username = '';
const password = '';
const profileUrl = 'https://www.instagram.com/chouhanshivrajsingh/?hl=en';

// Run the scraper
scrapeInstagramClone(profileUrl, username, password);
