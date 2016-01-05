from celery import Celery

app = Celery('twitter', broker='django://', backend='sqla+sqlite:///celerydb.sqlite')

@app.task
def add(x, y):
    return x + y

