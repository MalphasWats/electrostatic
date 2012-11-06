import os
import time
import re
import codecs

from flask import Blueprint, request, session, redirect, url_for, abort, render_template, flash

from markdown import markdown

from electrostatic import blueprint

import system


@blueprint.route('/')
def index():
    return render_template('control_panel.html', 
                           articles=system.get_articles(),
                           drafts=system.get_drafts())

                           
@blueprint.route('/save', methods=['POST'])
def save():
    if request.form.get('preview') == 'Preview':
        return render_template('preview.html', 
                           preview_html=markdown(request.form['text'], output_format="html5"),
                           rawText=request.form['text'],
                           filename=request.form['filename'])
                           
    if request.form['text'] == '':
        flash("articles must have body text", category='error')
        return redirect(url_for('electrostatic.index'))
        
    text = request.form['text']
        
    title = system.get_title_elements(text)[0]
    safe_title = re.sub('[^a-zA-Z0-9\s]', '', title).replace(' ', '_')
    date = time.strftime('%Y-%m-%d_%H-%M', time.gmtime())
    
    
    if request.form.get('draft') == 'on':
        if request.form['filename'] != '':
            filename = request.form['filename']
        else:
            filename = "%s.txt" % safe_title
        
        system.save_draft(filename, text)
            
    else:
        if request.form['wasDraft'] == 'yes':
            filename = "%s_%s" % (date, system.get_safe_filename(request.form['filename']))
        elif request.form['filename'] != '':
            filename = system.get_safe_filename(request.form['filename'])
            system.kill_item_in_cache(filename)
        else:
            filename = "%s_%s.txt" % (date, safe_title)
        
        system.save_article(filename, text)
        
    
        #TODO: This is not multi-user friendly!!
        author = "%s %s" % (session['user']['forename'], session['user']['surname'])
        system.create_article_from_template(text, title, filename[:-4], author)
            
    
    return redirect(url_for('electrostatic.index'))
    
    
@blueprint.route('/edit/<filename>')
def edit(filename):
    filename = system.get_safe_filename(filename)
    articleElements = system.get_article_elements(filename)
    
    return render_template('editor.html',
                           filename=filename, 
                           rawText=articleElements['rawText'],
                           isDraft=False)
                           
                         
@blueprint.route('/draft/<filename>')
def draft(filename):
    draft = system.get_draft(filename)
    
    return render_template('editor.html',
                           filename=filename, 
                           rawText=draft,
                           isDraft=True)
                           
                           
@blueprint.route('/delete/article/<filename>')
def delete_article(filename):
    system.delete_article(filename)
    return redirect(url_for('electrostatic.index'))
    
    
@blueprint.route('/delete/draft/<filename>')
def delete_draft(filename):
    system.delete_draft(filename)
    return redirect(url_for('electrostatic.index'))
    
    
@blueprint.route('/rebuild')
def rebuild_site():
    #TODO: This is not multi-user friendly!!
    author = "%s %s" % (session['user']['forename'], session['user']['surname'])
    system.rebuild_articles(author)
    system.rebuild_archive_indexes()
    system.rebuild_homepage(author)
    flash('Site rebuilt', category='info')
    return redirect(url_for('electrostatic.index'))
    
    
    
# @blueprint.route('/preview/<filename>')
# def preview_article(filename):
#     filename = get_safe_filename(filename)
#     articleFile = codecs.open("%s/articles/%s" % (blueprint.config['SITE_ROOT_DIR'], filename), encoding='utf-8', mode='r')
#     articleText = articleFile.read()
#     articleFile.close()
#     
#     html = markdown(articleText,
#                            output_format="html5")
#     
#     return render_template("%s/preview.html" % (blueprint.config['SITE_TEMPLATE']), 
#                            content=html,
#                            author=blueprint.config['AUTHOR'],
#                            pubDate="Just now")
