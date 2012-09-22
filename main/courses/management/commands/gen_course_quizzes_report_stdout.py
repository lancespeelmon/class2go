from django.core.management.base import BaseCommand, CommandError
from c2g.models import *
from django.contrib.auth.models import User,Group
from django.db import connection, transaction
from courses.reports.data_aggregation.course_quizzes import *

class Command(BaseCommand):
    help = "Get course dashboard data\n"
        
    def handle(self, *args, **options):
        if len(args) == 0:
            print "No course handle supplied!"
            
        try:
            course = Course.objects.get(handle= args[0], mode='ready')
        except:
            print "Failed to find course with given handle"
            return
            
        qd = get_course_quizzes_report_data(course)
        #import pdb; pdb.set_trace()
        ### Output ###
        
        print "Quizzes Report for %s (%s %d)" % (course.title, course.term.title(), course.year)
        print "--------------------------------------------------------------------"
        print "\n"
        
        print "\n"
        
        for quiz_data in qd: print gen_quiz_report_string(quiz_data) + "\n"
        
        
def gen_quiz_report_string(qd):
    if isinstance(qd['quiz'], Video): type_ = 'video'
    else:
        if qd['quiz'].assessment_type == 'summative': type_ = 'summative problem set'
        else: type_ = 'formative problem set'

    str_  = ''
    str_ += '%s (%s)\n' % (qd['quiz'].title, type_.title())
    str_ += '-' * len(str_) + "\n"
    if not qd['has_attempts']:
        str_ += "No attempts yet for this %s" % type_
        return str_
    
    if type_ == 'summative problem set':
        str_ += "Mean score: %s\t Max score: %s\n" % (str(qd['mean_score']), str(qd['max_score']))
    
    for exercise in qd['exercises']:
        str_ += gen_exercise_report_string(exercise)
        
    return str_
       
def gen_exercise_report_string(ed):
    str_ = ""
    str_ += "\t" + ed['exercise'].get_slug() + "\n"
    str_ += "\t" + '-' * len(ed['exercise'].get_slug()) + "\n"
    
    if not ed['has_attempts']:
        str_ += "\t\tNo attempts yet for this exercise\n"
        return str

    str_ += "\t\tTotal number of attempts: %d (avg %f per student)\n" % (ed['num_attempts'], 1.0*ed['num_attempts']/ed['num_unique_attempts'])        
    str_ += "\t\tMean time per attempt: %d seconds\n" % ed['mean_time_per_attempt']
    if 'max_score' in ed: str_ += "\t\tMean score: %d \t Max score: %d\n" % (ed['max_score'], ed['mean_score'])
    str_ += "\t\tStudents with attempts: %d \t Students with correct attempts: %d (%d percent)\n" % (ed['num_unique_attempts'], ed['num_students_with_correct_attempt'], int(100*ed['num_students_with_correct_attempt']/ed['num_unique_attempts']))
    str_ += "\t\t\tStudents with correct:\t1st attempts: %f percent\t2nd attempts:%f percent\t3rd attempts:%f percent\n" % (100.0*ed['num_students_with_correct_first_attempt']/ed['num_unique_attempts'], 100.0*ed['num_students_with_correct_second_attempt']/ed['num_unique_attempts'], 100.0*ed['num_students_with_correct_third_attempt']/ed['num_unique_attempts'])

    return str_