import os
import requests

from celery import Celery
from celery.utils.log import get_task_logger

from scrapper import Scrapper
from database import Session
from models import Tasks, Results


REDIS_HOST = os.environ.get('REDIS_HOST')
logger = get_task_logger(__name__)

celery_app = Celery('tasks', broker=f'redis://{REDIS_HOST}', backend=f'redis://{REDIS_HOST}')


@celery_app.task
def count(id):
    logger.info(f'Adding task for id: {id}')
    session = Session()
    task = session.query(Tasks).filter_by(id=id).first()
    res = Results(address=task.address, words_count=0, http_status_code=0)

    try:
        scrpr = Scrapper(task.address)
    except:
        scrpr = None

    if scrpr:
        err = scrpr.get_page()
        if not err:
            task.http_status_code, matches = scrpr.count_matches()
            task.task_status = 'FINISHED'
            res = Results(
                address=task.address, words_count=matches, http_status_code=task.http_status_code)
        else:
            print(err)

    session.add(res)
    session.commit()
    logger.info(task)
    logger.info(res)
