import unittest
from run_budget import choose_role
class WorkerTests(unittest.TestCase):
    def test_unrecorded_role_precedes_paid_retakes(self):
        queue=[dict(id='a',role='CROSSBOW'),dict(id='b',role='INFANTRY_F')]
        totals=dict(CROSSBOW=360,INFANTRY_F=396)
        self.assertEqual(choose_role(queue,dict(a=1),totals),'INFANTRY_F')
        self.assertEqual(choose_role(queue,{},totals),'CROSSBOW')
if __name__=='__main__':unittest.main()
