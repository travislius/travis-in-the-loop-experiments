# Knowledge distillation on MNIST (teacher → tiny student)

**Video:** Knowledge Distillation Explained: How Small AI Models Learn From Big Ones

Run on 2026-10-24 with [MLX](https://github.com/ml-explore/mlx) on Apple Silicon.

## Setup
- Data: MNIST (the four standard `*.gz` files; SHA-256 hashes in `results.json`). Download into `data/` before running.
- Teacher: MLP 784-1200-1200-10, ReLU, dropout 0.2, 2,395,210 parameters, trained on all 60,000 images.
- Student: MLP 784-32-10, 25,450 parameters (~94× smaller).
- A: student from hard labels, 2,000 random training images, 40 epochs, 3 seeds.
- B: same images, labels unused, trained to match teacher soft targets at temperature T=4 (loss × T²).
- "Mythical 3": 10,000 random training images with every 3 removed (8,996 left). Hard-label student vs distilled student, tested on the 1,010 test-set 3s. Distilled student optionally gets one additive bias on the "3" logit, chosen to maximize accuracy on 5,000 held-out *training* images (test set never used for tuning), following Hinton et al. 2015 §3.

## Results (mean of 3 seeds)
| | Test accuracy |
|---|---|
| Teacher | 98.0% |
| Student A (hard labels) | 91.7% |
| Student B (distilled) | 92.1% |

| Mythical 3 — test 3s recognized | |
|---|---|
| Hard labels | 0% |
| Distilled, raw | 19% |
| Distilled + 3-bias | 68% |

Per-seed values, soft-target example and settings are in `results.json`.

## Rejected run
`rejected-run/` keeps a first run with a bug: the teacher was left in training mode (dropout on) when producing soft targets. Kept for transparency; not used in the video.

## Run
```bash
pip install mlx numpy
python distill_demo.py
```

Reference: Hinton, Vinyals, Dean, "Distilling the Knowledge in a Neural Network," arXiv:1503.02531.
