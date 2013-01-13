import os
import datetime
import time
import re
import codecs

from flask import request, session, redirect, url_for, abort, flash
import jinja2
from werkzeug import secure_filename

from glob import glob
from markdown import markdown

from electrostatic import blueprint
import search

articleCache = {}

def get_articles():
    path = os.path.join(blueprint.config['SITE_ROOT_DIR'], 'articles', '*.txt')
    files = glob(path)
    files.sort()
    files.reverse()
    articles = []
    
    for f in files:
        filename = os.path.split(f)[1]
        
        elem = get_article_elements(filename)
        articles.append(elem)
        
    return articles
    

def get_drafts():
    path = os.path.join(blueprint.config['DRAFTS_ROOT_DIR'], '*.txt')
    files = glob(path)
    files.sort()
    drafts = []
    
    for f in files:
        filename = os.path.split(f)[1]
        text = get_draft(filename).splitlines()
        line = 1
        snippet = ''
        while snippet == '' and line < len(text):
            snippet = text[line][0:30]
            line += 1

        drafts.append({'title': filename[:-4], 'filename': filename, 'snippet':snippet})
        
    return drafts
    
    
def save_article(filename, text):
    article_path = os.path.join(blueprint.config['SITE_ROOT_DIR'], 'articles', filename)
    try:
        with codecs.open(article_path, encoding='utf-8', mode='w') as article_file:
            article_file.write(text)
    except:
        flash("There was a problem accessing the file %s" % article_path, category='error')
    else:
        flash("The article was saved", category='info')

    
def get_article_elements(filename):
    global articleCache
    articlePath = os.path.join(blueprint.config['SITE_ROOT_DIR'], 'articles', filename)
    if articlePath in articleCache:
        return articleCache[articlePath]
        
    try:
        articleFile = codecs.open(articlePath, encoding='utf-8', mode='r')
    except:
        flash("There was a problem accessing file: %s" % articlePath, category='error')
        return []
        
    rawText = articleFile.read()
    articleFile.close()
    
    html = ''
    title = ''
    link = ''
    if rawText != '':
        html = markdown(rawText, output_format='html5')
        titleElem = get_title_elements(rawText)
        title = titleElem[0]
        link = titleElem[1]
        
    url = build_article_url(articlePath)
    print url
    pubDate = get_pub_date(filename)
    
    article = {'filename': filename, 
               'rawText': rawText,
               'title': title, 
               'link': link, 
               'url': url, 
               'pubDate': pubDate, 
               'html': html,}
           
    articleCache[articlePath] = article
    
    return article
    
    
def delete_article(filename):
    filename = get_safe_filename(filename)
    elem = get_article_elements(filename)
    article_text_path = os.path.join(blueprint.config['SITE_ROOT_DIR'], 'articles', filename)
    try:
        os.remove(article_text_path)
    except:
        flash("unable to delete file: %s" % article_text_path, category='error')
    else:
    
        html_filename = "%s.html" % filename[17:-4]    
        article_html_path = os.path.join(blueprint.config['SITE_ROOT_DIR'], filename[:10].replace('-','/'), html_filename) 
        try:
            os.remove(article_html_path)
        except:
            flash("unable to delete file: %s" % article_html_path, category='error')
        else:
            
            rebuild_archive_indexes()
            
            #TODO: yuck yuck
            author = "%s %s" % (session['user']['forename'], session['user']['surname'])
            rebuild_homepage(author)
            
            kill_item_in_cache(filename)
            
            search.remove_from_index(elem['rawText'], elem['url'])
            
            flash("deleted %s" % filename, category='info')
            
    
    
    
def save_draft(filename, text):
    draft_path = os.path.join(blueprint.config['DRAFTS_ROOT_DIR'], filename)
    try:
        with codecs.open(draft_path, encoding='utf-8', mode='w') as draft_file:
            draft_file.write(text)
    except:
        flash("There was a problem accessing the file %s" % draft_path, category='error')
    else:
        flash("The draft was saved", category='info')


def get_draft(filename):
    draftPath = os.path.join(blueprint.config['DRAFTS_ROOT_DIR'], filename)
    
    try:
        draftFile = codecs.open(draftPath, encoding='utf-8', mode='r')
    except:
        flash("There was a problem accessing file: %s" % draftPath, category='error')
        return ''
    
    rawText = draftFile.read()
    draftFile.close()
    
    return rawText
    
    
def delete_draft(filename):
    draft_path = os.path.join(blueprint.config['DRAFTS_ROOT_DIR'], filename)
    try:
        os.remove(draft_path)
    except:
        flash("unable to delete file: %s" % draft_path, category='error')
    else:
        flash("deleted %s" % filename, category='info')

    
def get_title_elements(rawText):
    title = rawText.splitlines()[0][1:].strip()
    if title[0] == '[':
        title = title.split('](')
        return (title[0][1:], title[1][:-1])
    else:
        return (title, '')

def get_body_text(rawText):
    lines = rawText.splitlines()
    return "\n".join(lines[1:])
    
    
def kill_item_in_cache(filename):
    global articleCache
    article_path = os.path.join(blueprint.config['SITE_ROOT_DIR'], 'articles', filename)
    try:
        del articleCache[article_path]
    except:
        pass
    
            
def build_article_url(articlePath):
    filename = os.path.split(articlePath)[1]
    return "%s%s%s/%s.html" % (blueprint.config['SITE_URL'], blueprint.config['SITE_ROOT_URL'], filename[:10].replace('-','/'),  filename[17:-4])


def get_pub_date(filename):
    #legacy pages don't have pubDate in their filename.
    try:
        ts = time.strptime(filename[:16], "%Y-%m-%d_%H-%M")
        pubDate = (time.strftime("%a, %d %b %Y %H:%M:%S GMT", ts), time.strftime("%A, %d %B %Y @ %H:%M", ts))
    except:
        pubDate = ('', '')
        
    return pubDate


def get_safe_filename(filename):
    return secure_filename(filename)
    
    
def create_article_from_template(rawText, title, filename, author):
    articlePath = os.path.join(blueprint.config['SITE_ROOT_DIR'], filename[:10].replace('-','/'))
    if not os.path.exists(articlePath):
        try:
            os.makedirs(articlePath)
        except:
            flash("There was a problem creating directories: %s" % articlePath, category='error')

    article_file_path = os.path.join(articlePath, "%s.html"%filename[17:])
    content = {'title': title,
               'html': markdown(rawText, output_format='html5'),
               'url': "%s%s%s/%s.html" % (blueprint.config['SITE_URL'], 
                                        blueprint.config['SITE_ROOT_URL'],
                                        filename[:10].replace('-','/'),
                                        filename[17:])
              }
              
    template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(blueprint.config['SITE_TEMPLATES_DIR']))
    template = template_env.get_template('article.html')
    try:
        with codecs.open(article_file_path, encoding='utf-8', mode='w') as articleFile:
            articleFile.write(template.render(content = content,
                                              author = author,
                                              pubDate = get_pub_date(filename)[1]))
    except jinja2.TemplateError:
        flash("There was a problem generating the template for: %s" % article_file_path, category='error')        
    except:
        flash("There was a problem accessing file: %s" % article_file_path, category='error')
    else:
        
        search.add_to_index(rawText, content['url'])
        
        rebuild_archive_indexes()
        rebuild_homepage(author)



def rebuild_articles(author):
    path = os.path.join(blueprint.config['SITE_ROOT_DIR'], 'articles', '*.txt')
    articles = glob(path)
    for article in articles:
        elem = get_article_elements(os.path.split(article)[1])
        try: 
            create_article_from_template(elem['rawText'], elem['title'], elem['filename'][:-4], author)
        except:
            pass


def rebuild_archive_indexes():
    archive_year_dirs_path = os.path.join(blueprint.config['SITE_ROOT_DIR'], "[0-9][0-9][0-9][0-9]")
    archiveYearDirs = glob(archive_year_dirs_path)
    archiveYearDirs.sort()
    
    archive_file_path = os.path.join(blueprint.config['SITE_ROOT_DIR'], 'archive.html')
    try:
        archiveFile = codecs.open(archive_file_path, encoding='utf-8', mode='w')
    except:
        flash("There was a problem accessing the file %s" % archive_file_path, category='error')
        return
        
    template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(blueprint.config['SITE_TEMPLATES_DIR']))
    template = template_env.get_template('archive.html')
    
    archiveYears = []
    all_articles_ever = {}
    
    for y in archiveYearDirs:
        year = os.path.split(y)[1]
        archiveYears.append((year, year))
        all_articles_ever[year] = []

        year_articles = {}
        month_articles = {}
        
        walk_path = os.path.join(blueprint.config['SITE_ROOT_DIR'], year)
        for (path, dirs, files) in os.walk(walk_path):
                        
            dirs.sort()
            sPath = path[len(blueprint.config['SITE_ROOT_DIR'])+1:]
            
            if len(sPath) == 4:
                #year directory, dirs is list of months
                all_articles_ever[year] = []
                year_articles = {'path': os.path.join(blueprint.config['SITE_ROOT_DIR'], year, 'index.html')}
                month_articles = {}
                for m in dirs:
                    year_articles[map_month_name(m)[1]] = []
                    
            elif not dirs:
                #leaf directory, files is list of articles
                if 'index.html' in files:
                    files.remove('index.html')
                
                archive_index_path = os.path.join(path, 'index.html')
                try:
                    archiveIndex = codecs.open(archive_index_path, encoding='utf-8', mode='w')
                except:
                    flash("There was a problem accessing the file %s/index.html" % path, category='error')
                    return
                    
                paths = [sPath for x in range(len(files))]
                items = map(map_article_full_title, files, paths)
                month = map_month_name(sPath[5:7])[1]
                all_articles_ever[year] += items
                year_articles[month] += items
                day_name = map_day_name(sPath[8:], sPath[5:7], year)[1]
                month_articles[day_name] += items
                day_articles = {'_%s'%day_name: items}
                
                archiveIndex.write(template.render(site_root_url=blueprint.config['SITE_ROOT_URL'], 
                                                   items=day_articles))
                archiveIndex.close()
                
            else:    
                #month directory, dirs is list of days 
                if month_articles:
                    #month context has changed, need to build the month page from month_articles
                    archive_index_path = month_articles['path']
                    try:
                        archiveIndex = codecs.open(archive_index_path, encoding='utf-8', mode='w')
                    except:
                        flash("There was a problem accessing the file %s/index.html" % path, category='error')
                        return

                    del month_articles['path']
                    
                    archiveIndex.write(template.render(site_root_url=blueprint.config['SITE_ROOT_URL'], 
                                                       items=month_articles))
                    archiveIndex.close()
                
                month_articles = {'path': os.path.join(path, 'index.html')}    
                month = sPath[5:7]
                for d in dirs:
                    month_articles[map_day_name(d, month, year)[1]] = []
            
            
        if month_articles:
            archive_index_path = month_articles['path']
            try:
                archiveIndex = codecs.open(archive_index_path, encoding='utf-8', mode='w')
            except:
                flash("There was a problem accessing the file %s" % archive_index_path, category='error')
                return

            del month_articles['path']
            
            archiveIndex.write(template.render(site_root_url=blueprint.config['SITE_ROOT_URL'], 
                                               items=month_articles))
            archiveIndex.close()
            
        archive_index_path = year_articles['path']
        try:
            archiveIndex = codecs.open(archive_index_path, encoding='utf-8', mode='w')
        except:
            flash("There was a problem accessing the file %s" % archive_index_path, category='error')
            return
        
        del year_articles['path']
        
        archiveIndex.write(template.render(site_root_url=blueprint.config['SITE_ROOT_URL'], 
                                           items=year_articles))
        archiveIndex.close()
                              
    archiveFile.write(template.render(site_root_url=blueprint.config['SITE_ROOT_URL'], 
                                      items=all_articles_ever))
    archiveFile.close()

    
def map_month_name(monthNumber):
    months = ("January", "February", "March", 
              "April", "May", "June", "July", 
              "August", "September", "October", 
              "November", "December")
    return (monthNumber, "%s, %s" % (monthNumber, months[int(monthNumber)-1]))
    
def map_day_name(dayNumber, month, year):
    d = datetime.date(int(year), int(month), int(dayNumber))
    return (dayNumber, "%s, %s, %s" % (dayNumber, d.strftime('%A'), dayNumber))
    
def map_article_full_title(f, path):
    path = os.path.split(path)
    day = path[1]
    path = os.path.split(path[0])
    month = path[1]
    year = path[0]
    article_url_path = "%s/%s/%s/%s" % (year, month, day, f)
    
    article_path = os.path.join(blueprint.config['SITE_ROOT_DIR'],
                                'articles',
                                "%s-%s-%s*_%s.txt" % (year, month, day, f[:-5]))                                              
    articles = glob(article_path)
    if articles:
        article = get_article_elements(os.path.split(articles[0])[1])
        title = article['title']
    else:
        title = f
    
    return (article_url_path, title)
    
    
def rebuild_homepage(author):
    n = blueprint.config['HOME_ARTICLE_COUNT']
    
    articles_path = os.path.join(blueprint.config['SITE_ROOT_DIR'], 'articles', '*.txt')
    articles = glob(articles_path)
    articles.sort()
    articles.reverse()

    articleElements = []

    for article in articles[:n]:
        elem = get_article_elements(os.path.split(article)[1])
        lines = elem['html'].splitlines()
        elem['body_html'] = "\n".join(lines[1:])
        articleElements.append(elem)
        
    template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(blueprint.config['SITE_TEMPLATES_DIR']))
    homepage_template = template_env.get_template('home.html')
    rss_template = template_env.get_template('rss.xml')
        
    homepage_path = os.path.join(blueprint.config['SITE_ROOT_DIR'], 'index.html')
    try:
        homepageFile = codecs.open(homepage_path, encoding='utf-8', mode='w')
    except:
        flash("There was a problem accessing the file %s" % homepage_path, category='error')
    else:
        homepageFile.write(homepage_template.render(articles=articleElements, author=author))
        homepageFile.close()

    lastBuildDate = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.gmtime()) #Thu, 26 Apr 2012 10:09:47 GMT
    rss_file_path = os.path.join(blueprint.config['SITE_ROOT_DIR'], blueprint.config['RSS_FEED_FILENAME'])
    try:
        rssFile = codecs.open(rss_file_path, encoding='utf-8', mode='w')
    except:
        flash("There was a problem accessing the file %s" % rss_file_path, category='error')
    else:
        rssFile.write(rss_template.render(items=articleElements, date=lastBuildDate))
        rssFile.close()
        
        