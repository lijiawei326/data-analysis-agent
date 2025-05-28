# 示例：如何添加新的分析服务器
# 这个文件展示了如何创建一个新的回归分析服务器

from mcp.server.fastmcp import FastMCP
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import json
import os
import sys

# 添加自定义类型路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from custom_types.types import ReadDataParam

# 创建MCP服务器实例
mcp = FastMCP('RegressionAnalysisServer')

@mcp.tool()
async def linear_regression_analysis(
    read_data_param: ReadDataParam,
    target_variable: str,
    feature_variables: List[str],
    test_size: float = 0.2,
    include_intercept: bool = True,
    **kwargs
) -> str:
    """
    执行线性回归分析
    
    Args:
        read_data_param: 数据读取参数
        target_variable: 目标变量（因变量）
        feature_variables: 特征变量列表（自变量）
        test_size: 测试集比例，默认0.2
        include_intercept: 是否包含截距项，默认True
        
    Returns:
        str: 回归分析结果的Markdown格式报告
    """
    try:
        # 读取数据
        if read_data_param.file_path:
            if read_data_param.file_path.endswith('.csv'):
                df = pd.read_csv(read_data_param.file_path)
            elif read_data_param.file_path.endswith('.xlsx'):
                df = pd.read_excel(read_data_param.file_path)
            else:
                return "❌ **错误**: 不支持的文件格式，请使用CSV或Excel文件"
        else:
            return "❌ **错误**: 未提供数据文件路径"
        
        # 验证变量是否存在
        missing_vars = []
        if target_variable not in df.columns:
            missing_vars.append(target_variable)
        for var in feature_variables:
            if var not in df.columns:
                missing_vars.append(var)
        
        if missing_vars:
            return f"❌ **错误**: 以下变量在数据中不存在: {', '.join(missing_vars)}"
        
        # 准备数据
        X = df[feature_variables]
        y = df[target_variable]
        
        # 检查缺失值
        if X.isnull().any().any() or y.isnull().any():
            # 删除包含缺失值的行
            data_clean = df[feature_variables + [target_variable]].dropna()
            X = data_clean[feature_variables]
            y = data_clean[target_variable]
            missing_count = len(df) - len(data_clean)
            if missing_count > 0:
                missing_info = f"\n⚠️ **注意**: 已删除 {missing_count} 行包含缺失值的数据"
            else:
                missing_info = ""
        else:
            missing_info = ""
        
        # 检查数据量
        if len(X) < 10:
            return "❌ **错误**: 有效数据量不足（少于10行），无法进行可靠的回归分析"
        
        # 分割训练集和测试集
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # 创建并训练模型
        model = LinearRegression(fit_intercept=include_intercept)
        model.fit(X_train, y_train)
        
        # 预测
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        # 计算评估指标
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        
        # 生成报告
        report = f"""# 📊 线性回归分析报告

## 📋 分析概况
- **目标变量**: {target_variable}
- **特征变量**: {', '.join(feature_variables)}
- **样本总数**: {len(df):,} 行
- **有效样本**: {len(X):,} 行{missing_info}
- **训练集**: {len(X_train):,} 行 ({(1-test_size)*100:.0f}%)
- **测试集**: {len(X_test):,} 行 ({test_size*100:.0f}%)

## 📈 模型性能

### 决定系数 (R²)
- **训练集 R²**: {train_r2:.4f}
- **测试集 R²**: {test_r2:.4f}

### 均方根误差 (RMSE)
- **训练集 RMSE**: {train_rmse:.4f}
- **测试集 RMSE**: {test_rmse:.4f}

## 🔍 回归系数

| 变量 | 系数 | 标准化系数 |
|------|------|------------|"""

        # 计算标准化系数
        X_std = (X_train - X_train.mean()) / X_train.std()
        y_std = (y_train - y_train.mean()) / y_train.std()
        model_std = LinearRegression(fit_intercept=False)
        model_std.fit(X_std, y_std)
        
        for i, var in enumerate(feature_variables):
            coef = model.coef_[i]
            std_coef = model_std.coef_[i]
            report += f"\n| {var} | {coef:.4f} | {std_coef:.4f} |"
        
        if include_intercept:
            report += f"\n| 截距项 | {model.intercept_:.4f} | - |"
        
        # 模型解释
        report += f"""

## 📝 结果解释

### 模型拟合度
- R² = {test_r2:.4f} 表示模型能够解释目标变量 {test_r2*100:.1f}% 的变异
"""
        
        if test_r2 >= 0.7:
            fit_quality = "**优秀** 🌟"
        elif test_r2 >= 0.5:
            fit_quality = "**良好** ✅"
        elif test_r2 >= 0.3:
            fit_quality = "**一般** ⚠️"
        else:
            fit_quality = "**较差** ❌"
        
        report += f"- 拟合质量: {fit_quality}\n"
        
        # 过拟合检查
        overfitting = train_r2 - test_r2
        if overfitting > 0.1:
            report += f"- ⚠️ **注意**: 可能存在过拟合（训练集R²比测试集R²高 {overfitting:.3f}）\n"
        
        # 变量重要性
        report += "\n### 变量重要性\n"
        importance = [(var, abs(coef)) for var, coef in zip(feature_variables, model_std.coef_)]
        importance.sort(key=lambda x: x[1], reverse=True)
        
        for i, (var, imp) in enumerate(importance, 1):
            report += f"{i}. **{var}**: 标准化系数绝对值 = {imp:.4f}\n"
        
        # 建议
        report += f"""

## 💡 建议

### 模型使用建议
"""
        if test_r2 >= 0.5:
            report += "- ✅ 模型拟合度较好，可以用于预测和解释\n"
        else:
            report += "- ⚠️ 模型拟合度有限，建议考虑添加更多特征或使用非线性模型\n"
        
        if overfitting > 0.1:
            report += "- 🔄 建议使用交叉验证或正则化方法减少过拟合\n"
        
        report += f"""
### 进一步分析建议
- 🔍 检查残差分布，验证线性假设
- 📊 进行多重共线性诊断
- 🎯 考虑特征工程和变量变换
- 📈 尝试其他回归方法（如岭回归、Lasso回归）

---
*分析完成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report
        
    except Exception as e:
        return f"❌ **分析过程中出现错误**: {str(e)}"

@mcp.tool()
async def polynomial_regression_analysis(
    read_data_param: ReadDataParam,
    target_variable: str,
    feature_variable: str,
    degree: int = 2,
    test_size: float = 0.2,
    **kwargs
) -> str:
    """
    执行多项式回归分析（单变量）
    
    Args:
        read_data_param: 数据读取参数
        target_variable: 目标变量
        feature_variable: 特征变量（单个）
        degree: 多项式次数，默认2
        test_size: 测试集比例，默认0.2
        
    Returns:
        str: 多项式回归分析结果
    """
    try:
        # 读取数据
        if read_data_param.file_path:
            if read_data_param.file_path.endswith('.csv'):
                df = pd.read_csv(read_data_param.file_path)
            elif read_data_param.file_path.endswith('.xlsx'):
                df = pd.read_excel(read_data_param.file_path)
            else:
                return "❌ **错误**: 不支持的文件格式"
        else:
            return "❌ **错误**: 未提供数据文件路径"
        
        # 验证变量
        if target_variable not in df.columns:
            return f"❌ **错误**: 目标变量 '{target_variable}' 不存在"
        if feature_variable not in df.columns:
            return f"❌ **错误**: 特征变量 '{feature_variable}' 不存在"
        
        # 准备数据
        data_clean = df[[feature_variable, target_variable]].dropna()
        X = data_clean[[feature_variable]]
        y = data_clean[target_variable]
        
        if len(X) < 10:
            return "❌ **错误**: 有效数据量不足"
        
        # 创建多项式特征
        from sklearn.preprocessing import PolynomialFeatures
        poly_features = PolynomialFeatures(degree=degree)
        X_poly = poly_features.fit_transform(X)
        
        # 分割数据
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X_poly, y, test_size=test_size, random_state=42
        )
        
        # 训练模型
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # 预测和评估
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        
        # 生成报告
        report = f"""# 📈 多项式回归分析报告

## 📋 分析概况
- **目标变量**: {target_variable}
- **特征变量**: {feature_variable}
- **多项式次数**: {degree}
- **有效样本**: {len(X):,} 行

## 📊 模型性能
- **训练集 R²**: {train_r2:.4f}
- **测试集 R²**: {test_r2:.4f}

## 🔍 多项式方程
"""
        
        # 构建方程
        feature_names = poly_features.get_feature_names_out([feature_variable])
        equation = f"{target_variable} = "
        terms = []
        
        for i, (coef, name) in enumerate(zip(model.coef_, feature_names)):
            if abs(coef) > 1e-10:  # 忽略很小的系数
                if name == '1':
                    terms.append(f"{coef:.4f}")
                else:
                    terms.append(f"{coef:.4f}×{name}")
        
        equation += " + ".join(terms)
        if model.intercept_ != 0:
            equation += f" + {model.intercept_:.4f}"
        
        report += f"```\n{equation}\n```\n"
        
        # 模型评估
        if test_r2 >= 0.7:
            quality = "**优秀** 🌟"
        elif test_r2 >= 0.5:
            quality = "**良好** ✅"
        else:
            quality = "**需要改进** ⚠️"
        
        report += f"""
## 📝 结果解释
- **拟合质量**: {quality}
- **解释能力**: 模型能解释 {test_r2*100:.1f}% 的变异

## 💡 建议
- 如果拟合度不理想，可以尝试调整多项式次数
- 注意避免过拟合，特别是高次多项式
- 可以考虑添加更多特征变量
"""
        
        return report
        
    except Exception as e:
        return f"❌ **分析过程中出现错误**: {str(e)}"

# 启动服务器的主函数
if __name__ == '__main__':
    print("🚀 启动回归分析服务器...")
    print("📡 服务器地址: http://127.0.0.1:8001/sse")
    print("🔧 支持的分析类型: regression")
    print("📊 可用工具:")
    print("  - linear_regression_analysis: 线性回归分析")
    print("  - polynomial_regression_analysis: 多项式回归分析")
    
    # 在端口8001上启动服务器（避免与相关性分析服务器冲突）
    mcp.run(transport='sse', port=8001) 