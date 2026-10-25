"""Native category normalization and active actor-edge policy."""


def reference_category(value):
    return value.replace('\\','/').split('/')[0]


def active_speaker_edge(owner_category,path,target_category):
    if path.endswith('/parent_pbg'):return False
    if owner_category=='sbps':
        return '/squad_loadout_ext/' in '/'+path and target_category in ('ebps','attachments')
    if owner_category=='ebps':
        return target_category=='attachments'
    if owner_category=='attachments':
        return target_category in ('attachments','ebps')
    return False
