Using `pm.LKJCorr` as the source of a correlation/covariance matrix in multivariate distributions (e.g., `pm.MvNormal(cov=...)`) can cause the model’s initial log-probability evaluation to fail intermittently, especially for larger `n` (commonly `n>=10`, but can happen as low as `n=3`).

The failure occurs during backward sampling / logp computations (i.e., when evaluating the log-probability at starting points), not during forward draws: calling `.eval()` on LKJCorr-based correlation matrices and prior/predictive sampling typically works. However, when the sampler checks initial values, the correlation matrix reconstructed from the unconstrained representation can be non–positive-semidefinite (has negative eigenvalues). This leads to a `pymc.exceptions.SamplingError` similar to:

```
SamplingError: Initial evaluation of model at starting point failed!
Starting values:
{'corr_values_interval__': array([...])}
```

The core problem is that the transform used for `LKJCorr` does not constrain the unconstrained parameterization early enough (or correctly) during the backward direction used for logp evaluation, so intermediate values can map to invalid correlation matrices.

Implement a proper unconstraining transform for `LKJCorr` so that transforming from an unconstrained real vector into LKJCorr’s support always yields a valid correlation structure suitable for use as a covariance/correlation matrix (in particular, it must be positive definite / at least positive semidefinite as required by downstream multivariate distributions). This transform must work reliably during logp evaluation, so that model initialization and sampling do not randomly fail.

Concretely, after the fix, the following workflow should be stable (no random failures at initialization) for moderate-to-large `n`:

```python
import pymc as pm
import pytensor.tensor as pt
import numpy as np

n, eta = 10, 1

def corr_to_mat(corr_values, n):
    corr = pt.zeros((n, n))
    corr = pt.set_subtensor(corr[np.triu_indices(n, k=1)], corr_values)
    return corr + corr.T + pt.identity_like(corr)

corr = corr_to_mat(pm.LKJCorr.dist(n=n, eta=eta), n)
y = pm.draw(pm.MvNormal.dist(mu=0, cov=corr), 100)

with pm.Model() as m:
    corr_values = pm.LKJCorr('corr_values', n=n, eta=eta)
    corr = corr_to_mat(corr_values, n)
    pm.MvNormal('y_hat', mu=0, cov=corr, observed=y)
    idata = pm.sample()
```

The transform should be compatible with PyMC’s transform interface (forward, backward, and `log_jac_det`) and should preserve the property that applying forward then backward (and vice versa, where applicable) behaves consistently. Additionally, it must behave correctly when sampling via JAX-backed samplers with `keep_untransformed` enabled, so that returned transformed/untransformed values are coherent.

Relevant APIs/classes involved include `pm.LKJCorr` and the correlation-matrix transform used for LKJ correlation parameterizations (e.g., `CholeskyCorrTransform` if used/extended), ensuring that the constrained representation implied by LKJCorr can always be converted into a valid correlation matrix for multivariate likelihoods during logp evaluation.