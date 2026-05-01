import numpy as np
from scipy.optimize import curve_fit

# 测量数据 (测量值cm, 实际值cm)
measured = np.array([130, 153, 58, 188])
actual = np.array([30, 50, 20, 60])

# 尝试线性拟合: actual = a * measured + b
def linear(x, a, b):
    return a * x + b

# 尝试二次拟合: actual = a * measured^2 + b * measured + c
def quadratic(x, a, b, c):
    return a * x**2 + b * x + c

# 尝试倒数拟合: actual = a / measured + b
def reciprocal(x, a, b):
    return a / x + b

print("=== 线性拟合 ===")
params_linear, _ = curve_fit(linear, measured, actual)
a, b = params_linear
print(f"actual = {a:.6f} * measured + {b:.6f}")
residuals_linear = actual - linear(measured, a, b)
rmse_linear = np.sqrt(np.mean(residuals_linear**2))
print(f"RMSE: {rmse_linear:.2f} cm")
print(f"预测值: {linear(measured, a, b)}")
print()

print("=== 二次拟合 ===")
params_quad, _ = curve_fit(quadratic, measured, actual)
a2, b2, c2 = params_quad
print(f"actual = {a2:.8f} * measured^2 + {b2:.6f} * measured + {c2:.6f}")
residuals_quad = actual - quadratic(measured, a2, b2, c2)
rmse_quad = np.sqrt(np.mean(residuals_quad**2))
print(f"RMSE: {rmse_quad:.2f} cm")
print(f"预测值: {quadratic(measured, a2, b2, c2)}")
print()

print("=== 倒数拟合 ===")
params_recip, _ = curve_fit(reciprocal, measured, actual)
a3, b3 = params_recip
print(f"actual = {a3:.6f} / measured + {b3:.6f}")
residuals_recip = actual - reciprocal(measured, a3, b3)
rmse_recip = np.sqrt(np.mean(residuals_recip**2))
print(f"RMSE: {rmse_recip:.2f} cm")
print(f"预测值: {reciprocal(measured, a3, b3)}")
print()

# 选择最佳拟合
best_rmse = min(rmse_linear, rmse_quad, rmse_recip)
if best_rmse == rmse_linear:
    print(f"最佳拟合: 线性 (RMSE={rmse_linear:.2f}cm)")
    print(f"修正公式: actual = {a:.6f} * measured + {b:.6f}")
elif best_rmse == rmse_quad:
    print(f"最佳拟合: 二次 (RMSE={rmse_quad:.2f}cm)")
    print(f"修正公式: actual = {a2:.8f} * measured^2 + {b2:.6f} * measured + {c2:.6f}")
else:
    print(f"最佳拟合: 倒数 (RMSE={rmse_recip:.2f}cm)")
    print(f"修正公式: actual = {a3:.6f} / measured + {b3:.6f}")
