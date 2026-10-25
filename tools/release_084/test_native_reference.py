import unittest


class NativeReferenceTests(unittest.TestCase):
    def test_native_count_flag_alone_does_not_prove_current_identity_ids(self):
        from native_reference_proof import check_correspondence
        identities=dict(identities=[dict(name='private_actor',pbgid=12)])
        draft=dict(identity_receipt_sha256='ids',added=[dict(path='private_actor.xml',pbgid=12)])
        native=dict(native_source_identity_compile=True,new_identity_instances=1,source_receipt_sha256='draft')
        check_correspondence(native,identities,draft,'ids','draft',{'private_actor':{12}})
        with self.assertRaises(RuntimeError):check_correspondence(native,identities,draft,'ids','draft',{'private_actor':{13}})
        with self.assertRaises(RuntimeError):check_correspondence(native,identities,draft,'new-ids','draft',{'private_actor':{12}})
        with self.assertRaises(RuntimeError):check_correspondence(native,identities,draft,'ids','new-draft',{'private_actor':{12}})


if __name__=='__main__':unittest.main()
