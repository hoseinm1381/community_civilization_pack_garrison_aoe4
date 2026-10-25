"""Local Whisper transcription without an expected-text prompt or API calls."""
import argparse
import json
import os
from pathlib import Path
import time
from local_bank import local_guard as guard
from pipeline import digest, save_json, wav_metrics
from quality import text_matches
from providers import OUT
from local_inputs import verify_inputs

RUNTIME = Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/tool-cache/local-voices-084')


class LocalASR:
    def __init__(self, model='whisper'):
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
        self.torch = torch
        if not torch.cuda.is_available(): raise RuntimeError('Local ASR CUDA unavailable')
        if model not in ['whisper', 'phowhisper', 'phowhisper-medium']: raise ValueError('Unqualified local ASR model')
        self.name = model
        self.inputs = verify_inputs(('vieneu', 'moss', model))
        model_path = str(RUNTIME / 'models' / model)
        self.processor = AutoProcessor.from_pretrained(model_path, local_files_only=True)
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(model_path, torch_dtype=torch.float16,
                    low_cpu_mem_usage=True, use_safetensors=model == 'whisper', local_files_only=True).to('cuda').eval()

    def transcribe(self, path):
        return self.transcribe_batch([path])[0]

    def transcribe_batch(self, paths):
        import soundfile as sf
        import soxr
        audios = []
        for path in paths:
            audio, sr = sf.read(str(path), dtype='float32')
            if audio.ndim != 1: raise ValueError('ASR requires mono audio')
            if sr != 16000: audio = soxr.resample(audio, sr, 16000)
            audios.append(audio)
        if not audios: return []
        inputs = self.processor(audios, sampling_rate=16000, return_tensors='pt', return_attention_mask=True)
        with self.torch.inference_mode():
            ids = self.model.generate(inputs.input_features.to('cuda', dtype=self.torch.float16),
                        attention_mask=inputs.attention_mask.to('cuda'), language='vi', task='transcribe',
                        do_sample=False, max_new_tokens=128)
        return [text.strip() for text in self.processor.batch_decode(ids, skip_special_tokens=True)]


def main():
    guard()
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=OUT / 'local/auditions')
    parser.add_argument('--secondary', action='store_true')
    args = parser.parse_args()
    state = json.loads((args.root / 'state.json').read_text())
    dest = args.root / 'local-asr.json'
    results = json.loads(dest.read_text()) if dest.exists() else {}
    if args.secondary:
        pending = [(key, row) for key, row in state.items() if key in results and results[key]['text_match'] is False
                   and 'phowhisper' not in results[key]]
    else:
        pending = [(key, row) for key, row in state.items() if not (key in results and results[key]['sha256'] == digest(row['path']))]
    if not pending: print('No unchecked audio'); return
    checker = LocalASR('phowhisper' if args.secondary else 'whisper')
    for key, row in pending:
        path = Path(row['path'])
        if digest(path) != row['sha256']: raise RuntimeError('Saved audio hash changed: ' + key)
        metrics = wav_metrics(path.read_bytes())
        text = checker.transcribe(path)
        meta = row['metadata']
        match = text_matches(meta['text'], text) if meta.get('context') != 'effort-probe' else None
        if args.secondary:
            if results[key]['sha256'] != row['sha256']: raise RuntimeError('Primary transcription hash no longer matches')
            results[key]['primary_text_match'] = results[key]['text_match']
            results[key]['phowhisper'] = dict(text=text, text_match=match, model='vinai/PhoWhisper-small', prompted=False)
            results[key]['text_match'] = match
        else:
            results[key] = dict(sha256=row['sha256'], text=text, expected=meta['text'], text_match=match, metrics=metrics,
                                verifier='local Whisper large-v3-turbo; unprompted Vietnamese transcription',
                                acting_approved=False, nonverbal_approved=False)
        save_json(dest, results)
        print('ASR', key, match, text, flush=True)
    summary = dict(checked=len(results), exact_words=sum(r['text_match'] is True for r in results.values()),
                   mismatches=sum(r['text_match'] is False for r in results.values()),
                   effort_probes=sum(r['text_match'] is None for r in results.values()),
                   status='Automated text and audio checks only; acting remains unqualified')
    save_json(args.root / 'local-asr-summary.json', summary)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    from exclusive_job import exclusive_job
    guard()
    with exclusive_job('local transcription'):main()
