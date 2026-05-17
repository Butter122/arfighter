
import numpy as np
from pathlib import Path

files = sorted(Path('skeleton_action/data/raw/punch_left').glob('*.npy'))
print(f'样本数: {len(files)}')

# 检查第一个和最后一个样本
for f in [files[0], files[-1]]:
    arr = np.load(f)
    print(f'{f.name}: shape={arr.shape}, dtype={arr.dtype}, x_min={arr[:,0].min():.3f}, x_max={arr[:,0].max():.3f}')
  