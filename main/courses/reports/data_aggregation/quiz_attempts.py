from c2g.models import *
from datetime import datetime, timedelta
import time
import math
from django.db.models import Avg
from courses.reports.data_aggregation.utility_functions import *

def get_quiz_attempts_report_data(ready_quiz, order_by='time_created'):
    dl = []
    
    if isinstance(ready_quiz, Video):
        rlns = VideoToExercise.objects.filter(video=ready_quiz).order_by('video_time')
        for rln in rlns:
            attempts = ProblemActivity.objects.filter(video_to_exercise=rln).order_by(order_by, 'time_created').only('student', 'complete', 'count_hints', 'attempt_content', 'time_taken').select_related()
            dl.append({'exercise': rln.exercise, 'attempts': attempts})
    else:
        rlns = ProblemSetToExercise.objects.filter(problemSet=ready_quiz).order_by('number')
        for rln in rlns:
            attempts = ProblemActivity.objects.filter(problemset_to_exercise=rln).order_by(order_by, 'time_created').only('student', 'complete', 'count_hints', 'attempt_content', 'time_taken').select_related()
            dl.append({'exercise': rln.exercise, 'attempts': attempts})
    
    return dl
    