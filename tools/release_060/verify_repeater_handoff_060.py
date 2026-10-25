"""Issue a preserved v3 handoff after the Repeater IV private selector closure."""
from common import OUT
import verify_final_binding_handoff_060 as final

final.STAGE=OUT/'integration/repeater-context-stage-r1/stage.json'
final.TARGET=OUT/'integration/final-binding-handoff-v3.json'
final.SCHEMA='ccp-060-final-private-binding-handoff/v3'
final.SOURCE_APPLIED=True

if __name__=='__main__':
    final.main()
