"""
Description
"""

import logging

from courseware.models import StudentModule
import crum

log = logging.getLogger(__name__)


DATABASE = 'csm'
# SQL_query = "SELECT state, grade, max_grade FROM courseware_studentmodule "\
#             "WHERE student_id='{student_id}' AND course_id='{course_id}' "\
#             "AND module_type='problem';"

def get_records():
    notes = "Able to grab the problem by looking at everything before _x_1"
    user = crum.get_current_user()
    template_url = "https://dillon-dumesnil.sandbox.edx.org/xblock/block-v1:{course_id}+type@problem+block@{problem_id}"
    # for record in StudentModule.objects.filter(**{"student_id": user.id, "module_type": "problem"}):

    #     log.critical(record.state)
    return "https://courses.edx.org/xblock/block-v1:MITx+18.01.1x+2T2017+type@problem+block@" + "problem_hw4B-tab3-problem1"
    # return "localhost:18000/xblock/block-v1:DillonX+DAD101+2017_T3+type@problem+block@68b08558f32b49e7aa1841015e24a296"
