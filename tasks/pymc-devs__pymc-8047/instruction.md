`pm.sample_smc` fails or behaves poorly when used with multiple cores, especially for models that include custom PyTensor Ops (e.g., created via `pytensor.compile.ops.as_op`) or other non-trivially picklable components.

When running parallel SMC sampling (e.g., `pm.sample_smc(..., cores=2)`), PyMC currently attempts to serialize/deserialize objects needed by worker processes in a way that breaks for custom ops defined in `__main__`. A common failure is:

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
    pm.Normal('z', mu=y, observed=[1, 1])

    pm.sample_smc(10, cores=2)
```

Instead of sampling, this can crash in multiprocessing with an error like:

```
AttributeError: module '__main__' has no attribute 'twice'
```

The expected behavior is that `pm.sample_smc` works with `cores>1` for models that use custom `as_op`/wrapped python Ops, without requiring users to move those functions into importable modules.

Additionally, `pm.sample_smc` has experienced regressions where parallel chains start slowly or sampling can appear to hang/stall near the final stage (notably after progress-bar related changes). Parallel execution should not trigger expensive or unsafe compilation work inside worker processes, and it should not deadlock or stall at the end of sampling.

Fix `pm.sample_smc` parallelization so that:

- Parallel sampling (`cores>1`) does not crash due to pickling/serialization of custom Ops (including functions defined in `__main__`).
- The core SMC sampling routine used by worker processes can be invoked without needing to pickle the full model or other fragile objects.
- Compilation or initialization work that is not safe or efficient to do in parallel workers is handled in a way that avoids long chain start delays and prevents final-stage stalls.
- The public API supports controlling the multiprocessing context used for SMC sampling (so users on platforms that default to spawning can still run successfully), and parallel execution should remain correct when running sequentially (`cores=1`) as well.

After the fix, the example above should run successfully with `cores=2` and produce a valid SMC trace/result, and parallel SMC sampling should not exhibit the reported hangs or large startup delays compared to earlier versions under typical workloads.