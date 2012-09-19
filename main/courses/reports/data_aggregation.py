from c2g.models import *
from datetime import datetime
import Math
    
def get_dashboard_data(draft_course):
    ready_course = draft_course.image
    
    dd = {'now': datetime.now(), 'ap':{}, 'ps':{}, 'vd':{}}
    
    ### Gets summary dashboard data ###
    # This is all we want to render on the reports page. Additional details such as page visits ... etc are available through the _detailed version.
    # We do this to prevent the instructor from having to wait for a long time everytime they visit the report page.
    
    # Get counts of course instructors, TAs, read-only TAs, and students
    instructors = draft_course.instructor_group.user_set.all()
    students = draft_course.student_group.user_set.all()
    tas = draft_course.tas_group.user_set.all()
    readonly_tas = draft_course.readonly_tas_group.user_set.all()
    
    dd['num_instructors'] = len(instructors)
    dd['num_instructors'] = len(students)
    dd['tas'] = len(tas)
    dd['readonly_tas'] = len(readonly_tas)
    
    # Get list of all videos, problem sets, and additional pages
    dd['ap']['list'] = []
    dd['fl']['list'] = []
    dd['ps']['list'] = []
    dd['vd']['list'] = []
    
    for ap in AdditionalPage.objects.getByCourse(draft_course).all():
        dd['ap']['list'].append({'object': ap})
        
    for ps in ProblemSet.objects.getByCourse(draft_course).all():
        dd['ps']['list'].append({'object': ps})
        
    for vd in Video.objects.getByCourse(draft_course).all():
        dd['vd']['list'].append({'object': vd})
    
    dd['ap']['num_live'] = 0
    dd['fl']['num_live'] = 0
    dd['ps']['num_live'] = 0
    dd['vd']['num_live'] = 0
    
    for key in dd:
        for obj in dd[key]['list']:
            if obj['object'].is_live():
                dd[key]['num_live'] += 1
    
    dd['ps']['num_formative'] = 0
    dd['ps']['num_formative_live'] = 0    
    
    for ps in dd['ps']['list']:
        if ps['object'].assessment_type == 'formative':
            dd['ps']['num_formative'] += 1
            if ps['object'].is_live():
                dd['ps']['num_formative_live'] += 1
                
    dd['ps']['num_summative'] = len(dd['ps']['list']) - dd['ps']['num_formative']
    dd['ps']['num_summative_live'] = dd['ps']['num_live'] - dd['ps']['num_formative_live']
    
    now_minus_one_day = dd['now']-timedelta(days=1)
    now_minus_one_week = dd['now']-timedelta(days=7)
    
    # Get visits for additional pages, problem sets, videos, and the forum
    ap_visits = AdditionalPageVisitLog.objects.filter(course=ready_course)
    ps_visits = ProblemSetVisitLog.objects.filter(course=ready_course)
    vd_visits = VideoVisitLog.objects.filter(course=ready_course)
    fm_visits = ForumVisitLog.objects.filter(course=ready_course)
    
    
    for item in dd['ap']['list']:
        dd['ap']['visits'] = {
            'total':{
                'past_24_hours': len(ap_visits.filter(additional_page=item['object'], time_created__gte=now_minus_one_day)),
                'past_week': len(ap_visits.filter(additional_page=item['object'], time_created__gte=now_minus_one_week)),
                'all_time': len(ap_visits.filter(additional_page=item['object'])),
            },
            'unique':{
                'past_24_hours': len(ap_visits.filter(additional_page=item['object'], time_created__gte=now_minus_one_day).unique('user')),
                'past_week': len(ap_visits.filter(additional_page=item['object'], time_created__gte=now_minus_one_week).unique('user')),
                'all_time': len(ap_visits.filter(additional_page=item['object']).unique('user')),
            }
        }
        
    for item in dd['ps']['list']:
        dd['ps']['visits'] = {
            'total':{
                'past_24_hours': len(ps_visits.filter(problemset=item['object'], time_created__gte=now_minus_one_day)),
                'past_week': len(ps_visits.filter(problemset=item['object'], time_created__gte=now_minus_one_week)),
                'all_time': len(ps_visits.filter(problemset=item['object'])),
            },
            'unique':{
                'past_24_hours': len(ps_visits.filter(problemset=item['object'], time_created__gte=now_minus_one_day).unique('user')),
                'past_week': len(ps_visits.filter(problemset=item['object'], time_created__gte=now_minus_one_week).unique('user')),
                'all_time': len(ps_visits.filter(problemset=item['object']).unique('user')),
            }
        }
        
    for item in dd['vd']['list']:
        dd['vd']['visits'] = {
            'total':{
                'past_24_hours': len(vd_visits.filter(video=item['object'], time_created__gte=now_minus_one_day)),
                'past_week': len(vd_visits.filter(video=item['object'], time_created__gte=now_minus_one_week)),
                'all_time': len(vd_visits.filter(video=item['object'])),
            },
            'unique':{
                'past_24_hours': len(vd_visits.filter(video=item['object'], time_created__gte=now_minus_one_day).unique('user')),
                'past_week': len(vd_visits.filter(video=item['object'], time_created__gte=now_minus_one_week).unique('user')),
                'all_time': len(vd_visits.filter(video=item['object']).unique('user')),
            }
        }
        
    dd['fm']['visits'] = {
        'total':{
            'past_24_hours': len(fm_visits.filter(time_created__gte=now_minus_one_day)),
            'past_week': len(fm_visits.filter(time_created__gte=now_minus_one_week)),
            'all_time': len(fm_visits),
        },
        'unique':{
            'past_24_hours': len(fm_visits.filter(time_created__gte=now_minus_one_day).unique('user')),
            'past_week': len(fm_visits.filter(time_created__gte=now_minus_one_week).unique('user')),
            'all_time': len(fm_visits.unique('user')),
        }
    }
    
    return dd
    
def get_quiz_data(ready_course):
    qd = []
    
    students = ready_course.student.group.user_set.all()
    
    for item in ProblemSet.objects.getByCourse(course=ready_course).all():
        item_data = {'type':item.assessment_type.title(), 'title':item.title, 'live_datetime': item.live_datetime, 'exercises': []}
        p2es = ProblemSetToExercise.objects.filter(problemSet=item).order_by('number')
        for p2e in p2es:
            # Get all attempts for this exercise
            attempts = ProblemActivity.objects.filter(problemset_to_exercise=p2e, student__in=students).order_by('time_created')
            item_data['exercises'].append(get_exercise_stats(p2e, attempts, students))
        qd.append(item_data)
        
    for item in Video.objects.getByCourse(course=ready_course).all():
        item_data = {'type':item.assessment_type.title(), 'title':item.title, 'live_datetime': item.live_datetime, 'exercises': []}
        v2es = VideoToExercise.objects.filter(video=item).order_by('video_time')
        for v2e in v2es:
            # Get all attempts for this exercise
            attempts = ProblemActivity.objects.filter(video_to_exercise=v2e, student__in=students).order_by('time_created')
            item_data['exercises'].append(get_exercise_stats(v2e, attempts, students))
        qd.append(item_data)
    
    return sorted(qd, key=lambda k: k['live_datetime'], reverse=True)
   
def get_exercise_stats(relationship, attempts, students): 
    ed = {}
    exercise = relationship.exercise
    
    # Create a decomposition list of attempts by student
    attempts_by_stud = []
    for student in students:
        student_attempts = attempts.filter(student=student)
        if len(student_attempts) > 0:
            time_to_first_correct_attempt = 0
            first_correct_attempt_index=-1 # -1 indicates that the student has no correct attempt
            index = 0
            for a in student_attempts:
                time_to_first_correct_attempt += a.time_taken
                if a.complete > 0:
                    first_correct_attempt_index = index
                    break
                else: index += 1
            if first_correct_attempt_index == -1: time_taken_to_first_attempt = -1
                    
            attempts_by_stud.append({
                'student':student,
                'attempts':student_attempts,
                'first_correct_attempt_index':first_correct_attempt_index,
                'time_to_first_correct_attempt':time_to_first_correct_attempt,
            })
            
            
    
    # For the exercise, this tells course staff about:
    #--------------------------------------------------
    # Name of Problem
        ed['name'] = exercise.get_slug()
        
    # Num of unique students who attempted the problem
        ed['num_unique_attempts'] = len(attempts.unique('student'))
        
    # Mean time taken per attempt
        ed['mean_time_per_attempt'] = Math.ceil(attempts.avg('time_taken'))
        
    # Mean time taken for the whole problem (summing time per attempt), and number of students with a correct attempt, and with a first correct attempt
        ed['num_students_with_correct_attempt'] = 0
        ed['num_students_with_correct_first_attempt'] = 0
        
        total_time_to_first_correct_attempt = 0
        num_students_with_correct_attempt = 0
        for stud_row in attempts_by_stud:
            if stud_row['first_correct_attempt_index'] > -1:
                ed['num_students_with_correct_attempt'] += 1
                if stud_row['first_correct_attempt_index'] == 0: ed['num_students_with_correct_first_attempt'] += 1
                
                total_time_to_first_correct_attempt += stud_row['time_to_first_correct_attempt']
                num_students_with_correct_attempt += 1
        ed['mean_time_to_first_correct_attempt'] = Math.ceil(total_time_to_first_correct_attempt/num_students_with_correct_attempt)
        
    # Mean Num of attempts
        ed['mean_num_attempts_per_student'] = len(attempts)/len(attempts.unique('user'))
        
    # Num of users w/ 1, 2, 3, or more than 3 attempts
        ed['num_students_with_one_attempt'] = 0
        ed['num_students_with_two_attempts'] = 0
        ed['num_students_with_three_attempts'] = 0
        ed['num_students_with_more_than_three_attempts'] = 0
        
        for stud_row in attempts_by_stud:
            if len(stud_row['attempts']) == 1: ed['num_students_with_one_attempt'] += 1
            elif len(stud_row['attempts']) == 2: ed['num_students_with_two_attempts'] += 1
            elif len(stud_row['attempts']) == 3: ed['num_students_with_three_attempts'] += 1
            elif len(stud_row['attempts']) > 3: ed['num_students_with_more_than_three_attempts'] += 1
        
        
    # Num of incorrect attempts submitted overall
        incorrect_attempts = attempts.filter(correct=0)
        ed['num_incorrect_attempts'] = incorrect_attempts.count()
        
    # Most popular incorrect answer (either text/numeric of response,  or text of multiple-choice)
        answer_frequencies_ = {}
        for a in incorrect_attempts:
            if a.attempt_content in answer_frequencies: answer_frequencies[a.attempt_content] += 1
            else: answer_frequencies[a.attempt_content] = 0
            
        answer_frequencies = []
        for answer in answer_frequencies_:
            answer_frequencies.append({'answer':answer, 'count':answer_frequencies_[answer], 'percent':100*answer_frequencies_[answer]/len(incorrect_attempts)})
        
        answer_frequencies.sort(key=lambda k: k['count'], reverse=True)
        
        while len(answer_frequencies) > 0 and answer_frequencies[-1]['percent'] < 10: answer_frequencies.pop()
        
        ed['most_frequent_incorrect_answers'] = answer_frequencies
        
        return ed

