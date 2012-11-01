#needs to be added to settings.py for instruments

ELECTROSTATIC = {
    'SITE_ROOT_DIR': '/path/to/website',
    'SITE_ROOT_URL' : '/', #usually /, change if your blog is built to a subdirectory
    'SITE_TEMPLATES_DIR' : '/path/to/website/templates',
    'SITE_URL' : 'http://www.example.com', #no trailing slash here, added by SITE_ROOT_URL
    'RSS_FEED_FILENAME' : 'blog_feed.xml',

    'DRAFTS_ROOT_DIR' : '/path/to/drafts',

    'SEARCH_INDEX_DIR' : '/path/to/search_index',

    'HOME_ARTICLE_COUNT': 10
}