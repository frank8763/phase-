"""Offline exact contact comparison with one verified provenance-path rewrite.

Only classification_basis.geom{1,2}.xml may change, and only from the exact
generated pair/assets/isolated_indoor.xml path to its relative path + byte hash.
Every measured contact field and every other provenance field stays unchanged.
The raw uncompressed log digest is still independently checked and preserved.
"""
import argparse
import copy
import gzip
import hashlib
import json
from itertools import zip_longest
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(row, pair, xml_sha):
    row = copy.deepcopy(row)
    generated = (pair / 'assets/isolated_indoor.xml').resolve()
    for geom in ('geom1', 'geom2'):
        basis = row.get('classification_basis', {}).get(geom, {})
        if 'xml' in basis:
            assert isinstance(basis['xml'], str)
            assert Path(basis['xml']).is_absolute()
            assert Path(basis['xml']).resolve() == generated, 'UNEXPECTED_XML_PROVENANCE'
            basis['xml'] = {'verified_relative_path': 'assets/isolated_indoor.xml',
                            'xml_bytes_sha256': xml_sha}
    return row


def compare_contacts(base, repeat):
    base, repeat = Path(base).resolve(), Path(repeat).resolve()
    results = [json.loads((p/'geometry_memory/result.json').read_text()) for p in (base, repeat)]
    xml_hashes = [sha(p/'assets/isolated_indoor.xml') for p in (base, repeat)]
    raw = [hashlib.sha256(), hashlib.sha256()]
    canonical = [hashlib.sha256(), hashlib.sha256()]
    counts = [0, 0]
    differences, original_differences = [], 0
    with gzip.open(base/'geometry_memory/contacts.jsonl.gz','rb') as a, \
            gzip.open(repeat/'geometry_memory/contacts.jsonl.gz','rb') as b:
        for index, pair_lines in enumerate(zip_longest(a, b)):
            normalized, original = [None, None], [None, None]
            for side, line in enumerate(pair_lines):
                if line is None:
                    continue
                raw[side].update(line); counts[side] += 1
                original[side] = json.loads(line)
                normalized[side] = normalize(original[side], (base, repeat)[side], xml_hashes[side])
                canonical[side].update((json.dumps(normalized[side],sort_keys=True,
                                                  separators=(',',':'),allow_nan=False)+'\n').encode())
            original_differences += int(original[0] != original[1])
            if normalized[0] != normalized[1] and len(differences) < 10:
                differences.append(index)
    raw_hashes = [h.hexdigest() for h in raw]
    canonical_hashes = [h.hexdigest() for h in canonical]
    raw_verified = all(h == r['contacts']['contact_log_content_sha256']
                       for h,r in zip(raw_hashes,results))
    counts_verified = all(n == r['contacts']['all_contact_records'] for n,r in zip(counts,results))
    checks = {'same_xml_bytes': xml_hashes[0] == xml_hashes[1],
              'both_raw_content_digests_verified': raw_verified,
              'record_counts_verified': counts_verified,
              'same_number_of_contacts': counts[0] == counts[1],
              'all_contact_fields_equal_after_verified_path_rewrite': not differences,
              'canonical_digest_equal': canonical_hashes[0] == canonical_hashes[1]}
    return {'passed':all(checks.values()), 'checks':checks,
            'base_pair':str(base), 'repeat_pair':str(repeat),
            'raw_content_sha256':raw_hashes, 'raw_content_hashes_identical':raw_hashes[0]==raw_hashes[1],
            'canonical_content_sha256':canonical_hashes, 'xml_bytes_sha256':xml_hashes,
            'contact_records':counts, 'raw_json_different_rows':original_differences,
            'first_non_path_difference_rows':differences,
            'only_permitted_rewrite':'classification_basis.geom1/geom2.xml: exact own pair/assets/isolated_indoor.xml -> relative path and verified byte SHA256; no numeric tolerance or field deletion',
            'simulation_steps':0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('base'); parser.add_argument('repeat')
    parser.add_argument('--output'); args = parser.parse_args()
    result = compare_contacts(args.base,args.repeat)
    if args.output:
        Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
