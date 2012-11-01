import os
import codecs
import re

from flask import Flask, flash, request
import jinja2
                   
from electrostatic import blueprint
from instruments.core import public_endpoint


def add_to_index(text, identifier):
    words = get_words(text)
    for w in words:
        indexFilename = os.path.join(blueprint.config['SEARCH_INDEX_DIR'], w)
        items = []
        if os.path.exists(indexFilename):
            try:
                indexFile = codecs.open(indexFilename, encoding='utf-8', mode='r')
            except:
                pass
            else:
                items = indexFile.read().splitlines()
                indexFile.flush()
                indexFile.close()
        
        items.append(identifier)
        items = set(items)
        try:
            indexFile = codecs.open(indexFilename, encoding='utf-8', mode='w')
        except:
            flash('Unable to create search index: %s' % indexFilename, category='error')
            return
        
        items = "\n".join(items)
        indexFile.write(items)
        indexFile.close()
        

def remove_from_index(text, identifier):
    words = get_words(text)
    for w in words:
        indexFilename = os.path.join(blueprint.config['SEARCH_INDEX_DIR'], w)
        if os.path.exists(indexFilename):
            indexFile = codecs.open(indexFilename, encoding='utf-8', mode='r')
            items = indexFile.read().splitlines()
            indexFile.close()
            try:
                items.remove(identifier)
            except:
                #wasn't ever indexed, don't care
                pass
            if len(items) > 0:
                indexFile = codecs.open(indexFilename, encoding='utf-8', mode='w')
                items = "\n".join(items)
                indexFile.write(items)
                indexFile.close()
            else:
                os.remove(indexFilename)
                
                
@blueprint.route('/search', methods=['GET', 'POST'])
@public_endpoint
def search():
    if request.method == 'POST':
        terms = get_words(request.form['search_string'])
    else:
        terms = get_words(request.args.get('s', ''))
    results = []
    for t in terms:
        indexFilename = os.path.join(blueprint.config['SEARCH_INDEX_DIR'], t)
        if os.path.exists(indexFilename):
            indexFile = codecs.open(indexFilename, encoding='utf-8', mode='r')
            results = indexFile.read().splitlines() + results
            indexFile.close()
    
    result_set = set(results)
    
    ranked_results = []
    for r in result_set:
        ranked_results.append((results.count(r), r, os.path.split(r)[1]))
    
    ranked_results.sort()
    ranked_results.reverse()
    
    template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(blueprint.config['SITE_TEMPLATES_DIR']))
    template = template_env.get_template('search_results.html')
    
    return template.render(terms=" ".join(terms),
                           results=ranked_results)


def get_words(text):
    depunc = re.sub('[^a-z_\-\s]', ' ', text.lower())

    all_words = set(depunc.split())
    words = []

    for w in all_words:
        if len(w) > 2 and not w.isdigit():
            words.append(w.strip('-'))

    return words
    
    
# #@app.route('/rebuild/search_index')
# def rebuild_index():
#     articles = get_articles()
#     for article in articles:
#         add_to_index(article['rawText'], article['url'])
#     
#     return redirect(url_for('control_panel'))