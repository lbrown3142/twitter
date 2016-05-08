#!/usr/bin/env python2
"""
Minimal Example
===============
Generating a square wordcloud from the US constitution using default arguments.
"""


#http://askubuntu.com/questions/156484/how-do-i-install-python-imaging-library-pil

from os import path
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import twitter.settings

def GenerateWordCloud():
    d = path.dirname(__file__)

    # Read the whole text.
    text = open(path.join(d, 'word_test.txt')).read()

    # Generate a word cloud image
    wordcloud = WordCloud().generate(text)

    # Display the generated image:
    # the matplotlib way:
    #plt.imshow(wordcloud)
    #plt.axis("off")

    # take relative word frequencies into account, lower max_font_size
    wordcloud = WordCloud(max_font_size=40, relative_scaling=.5).generate(text)
    plt.figure()
    plt.imshow(wordcloud)
    plt.axis("off")

    plt.savefig(twitter.settings.STATICFILES_DIR + '/images/test.png')

    # The pil way (if you don't have matplotlib)
    #image = wordcloud.to_image()
    #image.show()