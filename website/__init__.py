#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from pytaxonomies import Taxonomies


nav = Nav()

@nav.navigation()
def mynavbar():
    return Navbar(
        'MISP taxonomies viewer and editor',
        View('Taxonomies', 'taxonomies'),
        View('Search', 'search'),
    )

app = Flask(__name__)
Bootstrap(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.debug = True
nav.init_app(app)

#t = Taxonomies(manifest_path="../../misp-taxonomies/MANIFEST.json")
t = Taxonomies()

@app.route('/', methods=['GET'])
def index():
    return taxonomies()

@app.route('/taxonomies/', defaults={'name': None})
@app.route('/taxonomies/<name>', methods=['GET'])
def taxonomies(name=None):
    if name and t.get(name):
        return render_template('taxonomy.html', taxonomy=t.get(name))
    else:
        return render_template('taxonomies.html', all_taxonomies=t)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.form.get('query'):
        q = request.form.get('query')
        entries = t.search(q)
        if entries:
            to_display = {e: t.revert_machinetag(e) for e in entries}
            return render_template('search.html', query=q, entries=to_display)
        else:
            return render_template('search.html', query=q, entries=None)
    return render_template('search.html', query=None, entries=None)



def main():
    app.run()

if __name__ == '__main__':
    main()
