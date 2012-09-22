from django.core.management.base import BaseCommand, CommandError
from c2g.models import *
from django.contrib.auth.models import User,Group
from django.db import connection, transaction
from courses.reports.data_aggregation.quiz_attempts import *

class Command(BaseCommand):
    help = "Get quiz attempts data. Syntax: manage.py gen_quiz_attempts_report <course_handle> <type {'video' | 'problemset'}> <quiz_slug> <order_by={['time'] | 'student'}>\n"
        
    def handle(self, *args, **options):
        if len(args) < 3:
            print "Missing course or quiz handle or quiz type!"
        
        try:
            ready_course = Course.objects.get(handle= args[0], mode='ready')
        except:
            print "Failed to find course with given handle"
            return
            
        if args[1] == 'video':
            try:
                ready_quiz = Video.objects.get(course=ready_course, slug=args[1])
            except:
                print "Failed to find video with given slug"
                return
        elif args[1] == 'problemset':
            try:
                ready_quiz = ProblemSet.objects.get(course=ready_course, slug=args[2])
            except:
                print "Failed to find problemset with given slug"
                return
        else:
            print "Second arg must be either 'video' or 'problemset'"
            return
            
        order_by = 'time_created'
        if (len(args) == 4) and (args[3] == 'student'): order_by = 'student'
        ex_att_dl = get_quiz_attempts_report_data(ready_quiz, order_by)
        ad = aggregate_quiz_attempts_report_data(ready_quiz, ex_att_dl)
        
        ### Output ###
        is_summative = isinstance(ready_quiz, ProblemSet) and (ready_quiz.assessment_type == 'summative')
        res_table = ad['res_table']
        sorted_usernames = sorted(res_table.keys())
        
        print "Quiz Attempts for Quiz \"%s\" in %s (%s %d)" % (ready_quiz.title, ready_course.title, ready_course.term.title(), ready_course.year)
        print "-----------------------------------------------------------------------------------------"
        print "\n"
        
        for ex in ad['exercises']:
            
            print ex.get_slug()
            print "------------------"
            
            print "Username" + (' ' * 17) + "Name" + (' ' * 26) + "Avg Time/Attempt" + ((' ' * 4) + "Score" if is_summative else '') + (' ' * 5) + "Attempts"
            print "--------" + (' ' * 17) + "----" + (' ' * 26) + "----------------" + ((' ' * 4) + "-----" if is_summative else '') + (' ' * 5) + "--------"

            for stud_username in sorted_usernames:
                if ex.id in res_table[stud_username]: stud_ex_res = res_table[stud_username][ex.id]
                else:
                    stud_ex_res = {'attempts': [], 'mean_attempt_time': '', 'score': ''}
                    for e in res_table[stud_username]:
                        stud_ex_res['student'] = res_table[stud_username][e]['student']
                        break
                print gen_stud_ex_res_string(stud_ex_res['student'], stud_ex_res['mean_attempt_time'], stud_ex_res['score'], stud_ex_res['attempts'], is_summative)
                
            print "\n"
        
        
def gen_stud_ex_res_string(student, mean_attempt_time, score, attempts, is_summative):
    str_ = content_pad(student.username, 25) + content_pad(student.first_name + ' ' + student.last_name, 30) + content_pad(mean_attempt_time, 20)
    if is_summative: str_ += content_pad(score, 10)
    
    if len(attempts) > 0:
        for i in range(len(attempts)):
            if i > 0: str_ += ' | '
            str_ += attempts[i]
    else:
        str_ += 'No attempts'
        
    return str_

def content_pad(content, length):
    return content + ((' '*(length-len(content))) if len(content) < length else '')