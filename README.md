# Engineering-blogs entries order by Hacker News and Reddit votes

1. Get feeds of [Engineering-blogs](https://github.com/kilimchoi/engineering-blogs).
2. Get entries of feeds.
3. Get votes of entries from Hackers News and Reddit.
4. Sort entries with this ranking method

    (votes - 1) / (t + 2)^1.8

[Reference - How Hacker News ranking algorithm works](https://medium.com/hacking-and-gonzo/how-hacker-news-ranking-algorithm-works-1d9b0cf2c08d)

## Deploy

### Environment variables

    PRAW_CLIENT_ID
    PRAW_CLIENT_SECRET
    PRAW_USER_AGENT
    MONGO_ENTRIES
    TORNADO_PORT
