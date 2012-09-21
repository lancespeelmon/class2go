from django.core.management.base import BaseCommand, CommandError
from c2g.models import *
from django.contrib.auth.models import User,Group
from django.db import connection, transaction
from courses.reports.data_aggregation.course_dashboard import *
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = "Get course dashboard data\n"
        
    def handle(self, *args, **options):
        if len(args) == 0:
            print "No course handle supplied!"
            
        try:
            course = Course.objects.get(handle= args[0], mode='draft')
        except:
            print "Failed to find course with given handle"
            return
            
        dd = get_course_dashboard_report_data(course)
        
        ### Output ###
        
        print "Dashboard for %s (%s %d)" % (course.title, course.term.title(), course.year)
        print "----------------------------------------------------------"
        print "\n"
        
        # Members
        print "\tCourse Members"
        print "\t--------------"
        print "\t\t%d professors, %d TAs, %d read-only TAs, and %d students" % (dd['num_instructors'], dd['num_tas'], dd['num_readonly_tas'], dd['num_students'])
        print "\n"
        
        # Content
        print "\tCourse Content"
        print "\t--------------"
        print "\t\tProblem sets: %d (%d live)" % (dd['ps']['num'], dd['ps']['num_live'])
        print "\t\t\tFormative: %d (%d live)\t-\tSummative: %d (%d live)" % (dd['ps']['num_formative'], dd['ps']['num_formative_live'], dd['ps']['num_summative'], dd['ps']['num_summative_live'])
        print "\t\tVideos: %d (%d live)" % (dd['vd']['num'], dd['vd']['num_live'])
        print "\t\tAdditional pages: %d (%d live)" % (dd['ap']['num'], dd['ap']['num_live'])
        print "\t\tFiles: %d (%d live)" % (dd['fl']['num'], dd['fl']['num_live'])
        print "\n"
        
        # Activity
        print "\tCourse Activity (Only Live Course Content is Displayed)"
        print "\t--------------------------------------------------------"
        
        # Problem Sets
        print "\t\tProblem Sets"
        print "\t\t------------"
        print gen_item_list_visits("\t\t", dd['ps']['list'])
        
        # Videos
        print "\t\tVideos"
        print "\t\t------"
        print gen_item_list_visits("\t\t", dd['vd']['list'])
        
        # Additional Pages
        print "\t\tAdditional Pages"
        print "\t\t----------------"
        print gen_item_list_visits("\t\t", dd['ap']['list'])
        
        print "\n"
        
        # Forum
        print "\t\tForum"
        print "\t\t----------------"
        print gen_visit_table("\t\t", dd['fm']['visits'], recent=True)
        
        print "\n"
        

def gen_item_list_visits(tabs, items):
    str = ""
    
    recent_items = []
    older_items = []
    
    for item in items:
        if item['object'].live_datetime and (item['object'].live_datetime > datetime.now() - timedelta(days=14)): recent_items.append(item)
        else: older_items.append(item)
    
    str += "%sRecent (Live within past 2 weeks):\n" % tabs
    str += "%s----------------------------------\n" % tabs
    if len(recent_items) > 0:
        for item in recent_items:
            str += tabs+" * "+item['object'].title + "\n"
            str += gen_visit_table(tabs+"\t", item['visits'], recent=True)
            
    else:
        str += tabs+"\tNone\n"
        
    str += "%sOlder:\n" % tabs
    str += "%s------\n" % tabs
    if len(older_items) > 0:
        for item in older_items:
            str += tabs+" * "+item['object'].title + "\n"
            str += gen_visit_table(tabs+"\t", item['visits'], recent=False)
            
    else:
        str += tabs+"\tNone\n"
        
    return str
        
    
def gen_visit_table(tabs, visits, recent=True):
    addl_tab = "\t\t"
    
    str  = "%sTotal visits\t\tUnique visits\n" % (addl_tab+tabs)
    str += "%s------------\t\t-------------\n\n" % (addl_tab+tabs)
    if recent:
        str += "%s Past 24 hours:\t%d\t\t\t%d\n" % (tabs, visits['total']['past_24_hours'], visits['unique']['past_24_hours'])
        str += "%s Past Week:\t%d\t\t\t%d\n" % (tabs, visits['total']['past_week'], visits['unique']['past_week'])
    str += "%s All time:\t%d\t\t\t%d\n\n" % (tabs, visits['total']['all_time'], visits['unique']['all_time'])
    
    return str
    