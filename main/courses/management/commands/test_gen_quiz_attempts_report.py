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
            course = Course.objects.get(handle= args[0], mode='draft')
        except:
            print "Failed to find course with given handle"
            return
            
        if args[1] == 'video':
            try:
                quiz = Video.objects.get(course=course, slug=args[1])
            except:
                print "Failed to find video with given slug"
                return
        elif args[1] == 'problemset':
            try:
                quiz = ProblemSet.objects.get(course=course, slug=args[2])
            except:
                print "Failed to find problemset with given slug"
                return
        else:
            print "Second arg must be either 'video' or 'problemset'"
            return
        
        if not quiz.image:
            print "This %s has not gone live, and hence has no attempts to export"
            return
            
        quiz = quiz.image
            
        order_by = 'time_created'
        if (len(args) == 4) and (args[3] == 'student'): order_by = 'student'
        ad = get_quiz_attempts_report_data(quiz, order_by)
        
        ### Output ###
        
        print "Quiz Attempts for Quiz \"%s\" in %s (%s %d)" % (quiz.title, course.title, course.term.title(), course.year)
        print "-----------------------------------------------------------------------------------------"
        print "\n"
        
        print "\n"
        
        for d in ad['exercise_data']:
            print "Attempts for \"%s\"" % (d['exercise'].get_slug())
            print "----------------------------------"
            if len(d['attempts']) > 0:
                print "Username" + (' ' * 17) + "Name" + (' ' * 26) + "Time taken" + (' ' * 5) + "Is correct" + (' ' * 5) + "Answer"
                print "--------" + (' ' * 17) + "----" + (' ' * 26) + "----------" + (' ' * 5) + "----------" + (' ' * 5) + "------"
                for attempt in d['attempts']: print gen_attempt_string(attempt)
            else:
                print "This exercise has not been attempted yet"
                
            print "\n"
        
        
        
def gen_attempt_string(attempt):
    return content_pad(attempt.student.username, 25) + content_pad(attempt.student.first_name + ' ' + attempt.student.last_name, 30) + content_pad(str(attempt.time_taken), 15) + content_pad(str(attempt.complete), 15) + attempt.attempt_content

def content_pad(content, length):
    return content + ((' '*(length-len(content))) if len(content) < length else '')