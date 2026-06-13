# Cloud bulk-analysis runbook

One-off: run phase 3 + phase 4 over all eligible games on rented GPU(s).
Ballpark on one RTX 4090: phase 3 ≈ 1–2 h, phase 4 ≈ 4–7 days, total ≈ $40–80
at ~$0.40/h. N pods with `--shard i/N` divide phase 4 wall-clock by N.

## 1. Prepare locally (Windows, repo root)

```powershell
python .\cloud\export_snapshot.py     # writes cloud_input.db (eligible games + analysis done so far)
```

You will upload `cloud_input.db` and `games.7z` (the SGF archive) to the pod.

## 2. Rent a pod

vast.ai or RunPod. Pick:
- GPU: RTX 4090 (or better; one GPU per pod)
- Image: `nvcr.io/nvidia/tensorrt:24.07-py3` (ships TensorRT 10.2 + CUDA 12.5,
  matching KataGo's `trt10.2.0-cuda12.5` Linux build). Any recent Python 3 is fine;
  the scripts use only the standard library.
- Disk: ≥ 20 GB.

If that image isn't available, fall back to KataGo's OpenCL Linux build on any
CUDA-capable image — slower but dependency-free.

## 3. Set up the pod

```bash
apt-get update && apt-get install -y p7zip-full unzip wget
git clone https://github.com/corrin/weiqi-estimate-trainer.git
cd weiqi-estimate-trainer

# upload games.7z and cloud_input.db here (scp / runpodctl / vast copy), then:
7z x games.7z                # creates games/
cp cloud_input.db games.db

# KataGo Linux TensorRT build + the b18 net
wget https://github.com/lightvector/KataGo/releases/download/v1.16.5/katago-v1.16.5-trt10.2.0-cuda12.5-linux-x64.zip
unzip katago-v1.16.5-trt10.2.0-cuda12.5-linux-x64.zip -d katago
chmod +x katago/katago
wget https://media.katagotraining.org/uploaded/networks/models/kata1/kata1-b18c384nbt-s9996604416-d4316597426.bin.gz

# sanity + speed check (first run compiles a TRT engine, takes a few minutes)
./katago/katago benchmark -model kata1-b18c384nbt-s9996604416-d4316597426.bin.gz -config analysis_bulk.cfg
```

If the benchmark recommends very different thread counts, adjust
`numAnalysisThreads`/`numSearchThreads`/`nnMaxBatchSize` in `analysis_bulk.cfg`
(keep numSearchThreads small, 2–4, and scale numAnalysisThreads).

## 4. Run

```bash
# phase 3 first — verifies the remaining eligible games (~1-2 h)
python3 phase3_verify.py --katago ./katago/katago --model ./kata1-b18c384nbt-s9996604416-d4316597426.bin.gz

# then phase 4 — single worker:
python3 phase4_analyze.py --shard 0/1 --katago ./katago/katago --model ./kata1-b18c384nbt-s9996604416-d4316597426.bin.gz

# ...or with N pods, run one shard per pod: --shard 0/N, --shard 1/N, ...
# (sharding is deterministic by filepath hash; shards never overlap)
```

Both scripts are resumable (rerun after any crash/restart; they skip done work)
and survive KataGo process deaths. Run inside `tmux` so SSH drops don't kill them.

## 5. Bring results home

Download each pod's `games.db` (rename per shard), then on Windows:

```powershell
python .\cloud\import_results.py shard0.db shard1.db
```

Idempotent — re-importing the same shard adds 0 rows. Local rows always win.
