#!/usr/bin/env python2
"""
Minimal Example
===============
Generating a square wordcloud from the US constitution using default arguments.
"""

from os import path
from wordcloud import WordCloud
import matplotlib

# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import twitter.settings

def GenerateWordCloud():

    # Read the whole text.
    #d = path.dirname(__file__)
    #text = open(path.join(d, 'word_test.txt')).read()
    #wordcloud = WordCloud(max_font_size=40, relative_scaling=.5).generate(text)

    frequencies = [('one', 1), ('two', 0.5)]
    wordcloud = WordCloud(max_font_size=40, relative_scaling=.5).generate_from_frequencies(frequencies)

    plt.figure()
    plt.imshow(wordcloud)
    plt.axis("off")

    plt.savefig(twitter.settings.STATICFILES_DIR + '/images/test.png')

    # The pil way (if you don't have matplotlib)
    #image = wordcloud.to_image()
    #image.show()