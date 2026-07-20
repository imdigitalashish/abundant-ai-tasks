Using `pm.LKJCorr` as the basis for a correlation/covariance matrix in multivariate likelihoods (for example `pm.MvNormal(cov=...)`) can fail during model initialization/log-probability evaluation with a `pymc.exceptions.SamplingError: Initial evaluation of model at starting point failed!`. The failure is intermittent for small dimensions but becomes very likely as the correlation dimension `n` grows (often failing for `n >= 10`). When it fails, the constructed correlation matrix has negative eigenvalues (i.e., it is not positive semidefinite), so downstream computations that require a PSD covariance (e.g., Cholesky factorization used in multivariate logp) error out.

This does not affect forward sampling via `.eval()` / prior predictive draws; it primarily affects the “backwards” direction used for logp computations and for generating valid initial points in samplers (i.e., the mapping from an unconstrained parameterization to a valid correlation structure is not constraining early enough).

The issue can be reproduced by treating `LKJCorr` as the free upper-triangular correlation entries, expanding them into a full correlation matrix, and passing that as `cov` to `MvNormal`. A typical pattern is:

```python
import pymc as pm
import pytensor.tensor as pt

n, eta = 10, 1

def corr_to_mat(corr_values, n):
    corr = pt.zeros((n, n))
    corr = pt.set_subtensor(corr[np.triu_indices(n, k=1)], corr_values)
    return corr + corr.T + pt.identity_like(corr)

with pm.Model():
    corr_values = pm.LKJCorr('corr_values', n=n, eta=eta)
    corr = corr_to_mat(corr_values, n)
    y = pm.MvNormal('y', mu=0, cov=corr, observed=pm.draw(pm.MvNormal.dist(mu=0, cov=corr), 100))
    idata = pm.sample()
```

Expected behavior: `pm.sample()` should consistently be able to initialize and run without failing due to invalid (non-PSD) correlation/covariance matrices implied by `LKJCorr` during logp evaluation. The transform associated with `LKJCorr` should guarantee that the constrained representation corresponds to a valid correlation matrix (positive definite, with unit diagonal) whenever the sampler proposes unconstrained values.

Actual behavior: during initial point evaluation (and potentially later proposals), the transformed values can correspond to an invalid correlation matrix that is not PSD, leading to initialization failure with `SamplingError` and a downstream linear algebra failure.

Implement an unconstraining/constraining transform for `LKJCorr` that maps unconstrained real vectors to valid correlation structures in a way that ensures the implied correlation matrix is positive definite in the constrained space used by logp. This should integrate with PyMC’s transform system (including correct `forward`, `backward`, and `log_jac_det` behavior) so that transformed logp computations and sampling initialization no longer produce non-PSD correlation matrices. The solution must work for larger `n` values (e.g., `n=10`) and must also be compatible with alternative sampling backends that rely on transformed/untransformed variable handling (e.g., JAX-based samplers using `keep_untransformed`).