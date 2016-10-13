#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
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
app.secret_key = '<changeme>'
Bootstrap(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.debug = True
nav.init_app(app)

#t = Taxonomies(manifest_path="../../misp-taxonomies/MANIFEST.json")
t = Taxonomies()


class SearchForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()])
    submit = SubmitField('Search')


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
    form = SearchForm()
    if form.validate_on_submit():
        q = request.form.get('query')
        entries = t.search(q)
        if entries:
            to_display = {e: t.revert_machinetag(e) for e in entries}
            return render_template('search.html', form=form, entries=to_display)
        else:
            return render_template('search.html', form=form, entries=None)
    return render_template('search.html', form=form, entries=None)


def main():
    app.run()
