"""Enforce the human's one round -> verified upload -> cleanup -> next order."""
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
AUTH=R/'runs/v1382_weekend_campaign/STORAGE_AUTHORIZATION_15GIB_20261122.json'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def before_next(parent,*,current_round):
    authority=read(AUTH)
    assert authority['storage_limit_bytes']==parent['storage_limit_bytes']==15*1024**3
    assert authority['single_active_round']and parent['active_round']is None
    assert not parent['models_now_authorized']and parent.get('active_math_round')is None
    reviewed=[]
    for row in parent['rounds']:
        if row['id']==current_round:continue
        started=row.get('started_unix')
        if type(started)not in(int,float)or started<authority['recorded_unix']:continue
        assert row['status'].startswith('CLOSED'),'PREVIOUS_ROUND_STILL_ACTIVE'
        link=row.get('post_round_storage_barrier')
        assert isinstance(link,dict),'PREVIOUS_ROUND_NOT_UPLOADED_VERIFIED_AND_CLEANED'
        path=R/link['path'];assert path.is_relative_to(R/'runs')and not path.is_symlink()
        assert sha(path)==link['sha256']
        receipt=read(path);assert receipt['round_id']==row['id']
        assert receipt['passed']and receipt['counters_exact_or_unknown_recorded']
        assert receipt['remote_all_original_members_verified']and receipt['eligible_cleanup_complete']
        proof_path=R/receipt['remote_proof_path'];assert proof_path.is_relative_to(R/'runs')and not proof_path.is_symlink()
        assert sha(proof_path)==receipt['remote_proof_sha256']
        proof=read(proof_path);assert proof['passed']
        assert all(proof[k]is True for k in ('every_asset_actual_download_SHA',
            'every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'))
        assert receipt['cleanup_performed_after_verified_unix']>=proof['verified_unix']
        assert receipt['unverified_original_deleted']is False
        reviewed.append(row['id'])
    return dict(passed=True,reviewed_new_authority_rounds=reviewed,
        authority_sha256=sha(AUTH),storage_limit_bytes=15*1024**3,
        old_frozen_rounds_not_reopened=True)
