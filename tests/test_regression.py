import numpy as np
from app.core.regression import linear_regression, compute_log_values

def test_linear_regression():
    # y = 2x + 1
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([3, 5, 7, 9, 11])
    
    res = linear_regression(x, y)
    assert np.isclose(res["slope"], 2.0)
    assert np.isclose(res["intercept"], 1.0)
    assert np.isclose(res["r_squared"], 1.0)
    assert np.allclose(res["fitted_values"], y)
    assert np.allclose(res["residuals"], 0.0)

def test_compute_log_values():
    box_sizes = [2, 4, 8]
    box_counts = [4, 4, 1]
    
    x, y = compute_log_values(box_sizes, box_counts)
    assert np.allclose(x, -np.log(box_sizes))
    assert np.allclose(y, np.log(box_counts))
