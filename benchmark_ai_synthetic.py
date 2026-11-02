"""Perfil local acotado sobre imagen sintética; no necesita DB ni storage real."""
import concurrent.futures
import json
import os
import tempfile
import threading
import time

import psutil
import torch
from PIL import Image

with tempfile.TemporaryDirectory(prefix='smile-ai-bench-') as temp:
    os.environ['YOLO_CONFIG_DIR'] = temp
    from ultralytics import YOLO

    torch.set_num_threads(min(4, torch.get_num_threads()))
    path = os.path.join(temp, 'synthetic.png')
    Image.new('RGB', (320, 320), 'white').save(path)
    proc = psutil.Process()
    before = proc.memory_info().rss
    start = time.perf_counter()
    model = YOLO(os.path.join('train_model', 'best.pt'))
    load_ms = (time.perf_counter()-start)*1000
    peak = [proc.memory_info().rss]
    stopping = threading.Event()

    def monitor():
        while not stopping.wait(0.1):
            peak[0] = max(peak[0], proc.memory_info().rss)

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()

    def predict(_):
        start_wall = time.perf_counter()
        results = model.predict(path, save=False, verbose=False, device='cpu')
        return {'wall_ms': round((time.perf_counter()-start_wall)*1000, 2), 'stages_ms': results[0].speed}

    runs = []
    for concurrency in (1, 2, 5, 10):
        if proc.memory_info().rss > 750_000_000 or psutil.virtual_memory().available < 1_500_000_000:
            break
        cpu_start = time.process_time()
        start_wall = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(predict, i) for i in range(concurrency)]
            samples = []
            errors = 0
            for future in futures:
                try:
                    samples.append(future.result())
                except Exception:
                    errors += 1
        wall = (time.perf_counter()-start_wall)*1000
        runs.append({'concurrency': concurrency, 'wall_ms': round(wall, 2), 'samples': samples, 'errors': errors, 'cpu_seconds': round(time.process_time()-cpu_start, 3), 'peak_rss_bytes': peak[0]})
        if errors or wall > 8000 or any(sample['wall_ms'] > 5000 for sample in samples):
            break
    stopping.set()
    monitor_thread.join()
    print('AI_SYNTHETIC=' + json.dumps({'model_init_ms': round(load_ms, 2), 'runs': runs, 'rss_before_bytes': before, 'peak_rss_bytes': peak[0], 'torch_threads': torch.get_num_threads()}))
