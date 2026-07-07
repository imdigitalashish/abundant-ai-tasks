`pm.sample_smc` has multiple multiprocessing-related failures and regressions that show up when `cores > 1`, especially on platforms that use the `spawn` start method (notably Windows/macOS in some environments) and when models include non-standard Python objects (custom PyTensor ops or black-box likelihoods).

One reproducible crash happens when a model uses a custom PyTensor op created with `pytensor.compile.ops.as_op`. When sampling with `pm.sample_smc(..., cores=2)` (or any value > 1), worker processes fail while deserializing the model/op, raising:

```
AttributeError: module '__main__' has no attribute 'twice'
```

Example:

```python
import pymc as pm
import pytensor.tensor as pt
from pytensor.compile.ops import as_op

@as_op(itypes=[pt.dvector], otypes=[pt.dvector])
def twice(x):
    return 2 * x

with pm.Model() as model:
    x = pm.Normal('x', mu=[0, 0], sigma=1)
    y = twice(x)
    z = pm.Normal('z', mu=y, observed=[1, 1])

    pm.sample_smc(10, cores=2)
```

Expected behavior: parallel SMC should run successfully with `cores > 1` even when the model contains an `as_op` custom op (and more generally, when it contains Python-callable likelihood components), producing a valid trace just like `cores=1`.

Actual behavior: parallel SMC attempts to serialize/deserialize objects in a way that requires the custom op to be importable from `__main__` by name in the worker process, which is not reliable under multiprocessing. This causes the sampling run to fail.

In addition to the crash above, `sample_smc` should not compile PyTensor functions in worker processes. Compilation is not thread-safe and can lead to large startup delays, uneven chain starts, or intermittent stalls/hangs near the final SMC stage. Parallel SMC should initialize/compile the SMC kernel deterministically in the main process and then distribute whatever is needed to workers so that workers can start sampling promptly and finish reliably.

Finally, the SMC progress bar behavior should be consistent with the general `pm.sample` progress bar interface:

- `progressbar=True` should show split-chain progress.
- `progressbar="combined"` should run in combined mode.
- `progressbar="combined+stats"` should enable combined mode and include full stats.
- `progressbar=False` should disable progress display.

A `MCMCProgressBarManager` created with `progressbar=True` must default to split mode (combined progress disabled) and full stats enabled, while `progressbar="combined"` must enable combined progress and disable full stats. When running in a compatible notebook environment that supports a marimo backend, the manager should select that backend and render HTML containing the expected structural elements for the progress table/bars and per-chain failing indicators when a chain is marked as failing.

Overall, `pm.sample_smc` should support:

- Correct parallel execution with `cores > 1` without pickling errors for common “black-box” model components like `as_op`.
- Safe and efficient multiprocessing startup (no worker-side compilation, no long chain startup delays, no intermittent final-stage stalls).
- Progress bar configuration/selection behavior consistent with the existing progress bar manager semantics used by `pm.sample`.
