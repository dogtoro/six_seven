"""Publish validated V3 tables and >=100 paired receipts per neural configuration."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import numpy as np
import pandas as pd


def publish():
    source = Path(__file__).resolve().parent.parent
    repo = source.parents[1] / 'six_seven_dam_checkout'
    def git(*args):
        try:
            return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT).decode().strip()
        except subprocess.CalledProcessError as exc:
            print(exc.output.decode(errors='replace'))
            raise
    assert git('branch','--show-current') == 'dam'
    assert git('remote','get-url','origin') == 'https://github.com/dogtoro/six_seven.git'
    assert not git('status','--porcelain'), 'Publish checkout has unrelated local changes'
    git('fetch','origin','dam')
    git('merge','--ff-only','origin/dam')
    paths = [Path(p) for p in ['README.md','HANDOFF_dataset_audit_and_baselines.md','V3_STATUS.md','FEEDBACK_RESPONSE.md','run_v3.ps1','dataset_v3_audit.json','dataset_v3_source_hashes.json','v3_generation_provenance.json','dataset_sample_v3/metadata.json']]
    paths += [Path('OCR_ACCELERATION.md'),Path('ocr_acceleration_validation.json')]
    paths += [Path('benchmarks')/p for p in ['README.md','PREDS_LOCATION.md','models.py','eval_sota.py','build_dataset_sample.py','adcdnet_infer.py','paddle_runtime.py','benchmark_ocr_threads.py','validate_v3.py','validate_v3_results.py','v3_resolution_report.py','package_v3_failure_analysis.py','publish_v3.py','test_detection_scores.py','test_resolution_statistics.py','test_failure_analysis_selection.py']]
    for folder in ['dataset_v3_realistic','v3_generator_source']:
        paths += [p.relative_to(source) for p in (source/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    results = source/'benchmarks/results_v3_realistic'
    paths += [(results/p).relative_to(source) for p in ['resolution_comparison.csv','RESOLUTION_REPORT.md']]
    for kind in ['official_mask','diff_mask']:
        folder = results/kind
        frame = pd.read_csv(folder/'per_image.csv')
        assert len(frame) == 18000 and frame.groupby('model').size().eq(3000).all()
        for name in ['per_image.csv','summary.csv','summary.md','run.log']:
            paths.append((folder/name).relative_to(source))
    for model in ['ext_adcdnet','ext_adcdnet_1024','ext_adcdnet_2048','ext_trufor']:
        folder = results/'official_mask/vis'/model
        authentic = {p.stem.replace('_authentic__','__'):p for p in folder.glob('*_authentic__*.png')}
        tampered = {p.stem.replace('_tampered__','__'):p for p in folder.glob('*_tampered__*.png')}
        by_receipt = {}
        for key in sorted(set(authentic)&set(tampered)): by_receipt.setdefault(key.split('__')[0],key)
        keys = list(by_receipt.values())
        assert len(keys) >= 100
        for i in np.linspace(0,len(keys)-1,100,dtype=int):
            key = keys[i]
            paths += [authentic[key].relative_to(source),tampered[key].relative_to(source)]
    for relative in sorted(set(paths)):
        original = source/relative
        target = repo/'six_seven'/relative
        assert original.is_file(),original
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(original,target)
        assert hashlib.sha256(original.read_bytes()).digest() == hashlib.sha256(target.read_bytes()).digest()
    # Standard input avoids Windows command-length limits for large artifact sets.
    payload = b'\0'.join(('six_seven/'+p.as_posix()).encode('utf-8') for p in sorted(set(paths)))+b'\0'
    subprocess.run(['git','-C',str(repo),'add','-f','--pathspec-from-file=-','--pathspec-file-nul'],input=payload,check=True)
    if git('diff','--cached','--name-only'):
        git('commit','-m','Complete V3 benchmark with native detection scores and resolution analysis')
    git('push','origin','dam')
    commit = git('rev-parse','HEAD')
    assert git('ls-remote','origin','refs/heads/dam').split()[0] == commit
    location = dict(commit=commit,branch='dam',paired_receipts_per_neural_configuration=100,
                    views='https://github.com/dogtoro/six_seven/tree/dam/six_seven/benchmarks/results_v3_realistic/official_mask/vis',
                    raw_map_bundle='v3_failure_analysis_maps.zip (local; not uploaded)')
    (source/'v3_published.json').write_text(json.dumps(location,indent=2))
    print('V3 handoff pushed and verified:',commit)
    return location


if __name__ == '__main__': publish()
