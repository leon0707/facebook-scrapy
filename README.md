# facebook-scrapy

This spider can start crawling from a group of profile urls, then expend to all the friends. It will collect all basic information on the profile page and all posts on the timeline.

0. install virtual environment
```
virtualenv venv
source venv/bin/activate
```
1. install packges
```
pip install -r requuirements.txt
```
2. add environment variables
```
FACEBOOK_EMAIL=xxxx
FACEBOOK_PASS=xxxx
```
3. start crawling
```
scrapy crawl facebook
```
