'''
Description
'''

import logging

from courseware.models import StudentModule
from opaque_keys.edx.locator import CourseLocator
import crum
import random

log = logging.getLogger(__name__)


DATABASE = 'csm'
REVIEW_COURSE_MAPPING = {
    'course-v1:DillonX+DAD401+2017_T3': 'DillonX+DAD402+2017_T3',
    'course-v1:DillonX+DAD301+2017_T3': 'DillonX+DAD302+2017_T3'
}
# SQL_query = 'SELECT state, grade, max_grade FROM courseware_studentmodule '\
#             'WHERE student_id='{student_id}' AND course_id='{course_id}' '\
#             'AND module_type='problem';'

def get_records(num_desired, current_course):
    user = crum.get_current_user()
    problem_ids = []
    # dummy_course = CourseLocator(u'DummyX', u'Dummy1', u'2017_T3', None, None)
    # course = [key for key in user.__dict__['_anonymous_id'].keys() if type(key) == type(dummy_course)][0]
    for record in StudentModule.objects.filter(**{'student_id': user.id, 'course_id': current_course, 'module_type': 'problem'}):
        problem = str(record.module_state_key).split("@")
        problem_ids.append(problem[-1])
    problems_to_show = random.sample(problem_ids, num_desired)
    review_course_id = REVIEW_COURSE_MAPPING[str(current_course)]
    template_url = 'https://dillon-dumesnil.sandbox.edx.org/xblock/block-v1:{course_id}+type@problem+block@{problem_id}'
    # local_template_url = '/xblock/block-v1:{course_id}+type@problem+block@{problem_id}'
    urls = []
    for problem in problems_to_show:
        urls.append(template_url.format(course_id=review_course_id, problem_id=problem))
        # urls.append(local_template_url.format(course_id=review_course_id, problem_id=problem))
    return urls
    # return template_url.format(course_id=review_course_id, problem_id=problem_to_show)
    # return 'https://courses.edx.org/xblock/block-v1:MITx+6.002.1x_1+2T2016+type@problem+block@903ce05eb08e452ba9991a2756d3cce2'
    # return '/xblock/block-v1:DillonX+DAD301+2017_T3+type@problem+block@050d2b4ce4514c888ff654c5972cc1fa'
    # return '/xblock/block-v1:DillonX+DAD101+2017_T3+type@problem+block@68b08558f32b49e7aa1841015e24a296'

