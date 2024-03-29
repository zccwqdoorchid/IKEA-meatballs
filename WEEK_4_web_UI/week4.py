from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from flask import Flask, render_template, request

import search_articles as sa    #this file defines a func to get data from txt file(wiki articles), replace it later by web scraping funcs (for final project)
from auxilary_boolean_funcs import boolean_detector, rewrite_query


app = Flask(__name__)

# get the wiki articles data
documents = sa.read_file('enwiki-20181001-corpus.100-articles.txt')    # type = a list of strings

tv = TfidfVectorizer(lowercase=True, sublinear_tf=True, use_idf=True, norm="l2")
sparse_matrix_r = tv.fit_transform(documents).T.tocsr()

cv = CountVectorizer(lowercase=True, binary=True)   
sparse_matrix_b = cv.fit_transform(documents).T.tocsr() 

terms = cv.get_feature_names_out()                  
t2i = cv.vocabulary_ 


def invalid_term(query, terms): # output words in the query that are not in the vocab
    invalids = []
    for t in query.lower().split():
        if t not in terms:
            invalids.append(t)
    return ", ".join(invalids)


def boolean_search(query):    # print BOOLEAN search results (top 10 only)
    hits_matrix = eval(rewrite_query(query.lower()))
    hits_list = list(hits_matrix.nonzero()[1])
    num_matches = len(hits_list)    # the number of matching docs
    matches = []                    # the matching content 

    if num_matches:     # found at least 1 matching doc
        doc_count = 0   # count documents displayed
        for idx in hits_list: # get first 10 matching docs
            matches.append(documents[idx][:300])
            # stop printing when doc_count reaches 10
            doc_count += 1
            if doc_count == 10:
                break
    return num_matches, matches        
  

def relevance_search(query):     # print RELEVANCE search results (top 10 only)
    query_vec = tv.transform([query.lower()]).tocsc()       #convert query to vector
    hits = np.dot(query_vec, sparse_matrix_r)
    ranked_scores_and_doc_ids = sorted(zip(np.array(hits[hits.nonzero()])[0], hits.nonzero()[1]), reverse=True)
    num_matches = len(ranked_scores_and_doc_ids)    # the number of matching docs
    matches = []                    # the matching content 

    if num_matches:      # found at least 1 matching doc       
        doc_count = 0
        for r in ranked_scores_and_doc_ids:
            matches.append(documents[r[1]][:300])
            doc_count += 1
            if doc_count == 10:
                break
    return num_matches, matches              

# ------------------------------------------

@app.route('/')
def welcoming_message():
   return "Hi! We are group IKEA Meatballs! Welcome to our search engine!"


@app.route('/searcher')
def search():
    query = str(request.args.get('query'))    #Get query from URL variable
    invalid_words = invalid_term(query, terms)
    matches = []
    num_matches = 0
    search_mode = "Relevance-ranked Search"
    #If query exists (i.e. is not None)
    if query:
        #If there's no invalid term in the query, do the searching
        if not invalid_words:    
            if boolean_detector(query):     # CASE 1: query fits boolean search
                search_mode = "Boolean Search"
                num_matches, matches = boolean_search(query)   
            else:                           # CASE 2: query fits relevance search
                num_matches, matches = relevance_search(query)
    
    return render_template('index_IKEA_meatballs.html', matches=matches, num_matches=num_matches, search_mode=search_mode)
