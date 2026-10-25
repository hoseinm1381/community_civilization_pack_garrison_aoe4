from pathlib import Path
import unittest
from check_preservation import permitted_authoring_change


class PreservationTests(unittest.TestCase):
    def test_approval_cannot_cover_gameplay_or_an_unapproved_model(self):
        root=Path('owned-root').resolve();path=root/'art/authoring/release_081/buffalo/r4/model.blend'
        approval=dict(path=str(path),baseline_sha256='old',user_approved=True)
        self.assertTrue(permitted_authoring_change(path,'old',approval,root))
        self.assertFalse(permitted_authoring_change(path,'other',approval,root))
        self.assertFalse(permitted_authoring_change(root/'assets/attrib/unit.xml','old',approval,root))
        self.assertFalse(permitted_authoring_change(path,'old',dict(approval,user_approved=False),root))


if __name__=='__main__':unittest.main()
