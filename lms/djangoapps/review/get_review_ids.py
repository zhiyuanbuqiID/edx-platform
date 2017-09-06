'''
Description
'''

import logging

from courseware.models import StudentModule
import crum
import random

log = logging.getLogger(__name__)


DATABASE = 'csm'
# SQL_query = 'SELECT state, grade, max_grade FROM courseware_studentmodule '\
#             'WHERE student_id='{student_id}' AND course_id='{course_id}' '\
#             'AND module_type='problem';'

def get_records():
    notes = 'Able to grab the problem by looking at everything before _x_1'
    user = crum.get_current_user()
    template_url = 'https://dillon-dumesnil.sandbox.edx.org/xblock/block-v1:{course_id}+type@problem+block@{problem_id}'
    problem_ids = []
    for record in StudentModule.objects.filter(**{'student_id': user.id, 'module_type': 'problem'}):
        problem = str(record.module_state_key).split("@")
        problem_ids.append(problem[-1])
    problem_to_show = random.choice(problem_ids)
    return template_url.format(course_id='DillonX+DAD302+2017_T3', problem_id=problem_to_show)
    # return 'https://courses.edx.org/xblock/block-v1:MITx+6.002.1x_1+2T2016+type@problem+block@903ce05eb08e452ba9991a2756d3cce2'
    # return 'localhost:18000/xblock/block-v1:DillonX+DAD101+2017_T3+type@problem+block@68b08558f32b49e7aa1841015e24a296'
