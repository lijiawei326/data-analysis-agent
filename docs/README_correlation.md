# 相关性分析工具

## 功能概述

本工具提供强大的相关性分析功能，支持两变量和多变量相关性分析。

### 主要特性

- **两变量相关性分析**：计算两个变量间的相关性
- **多变量相关性矩阵**：计算3-10个变量的完整相关性矩阵
- **分组分析**：支持按指定列进行分组分析
- **多种计算方法**：Pearson、Spearman、Kendall相关性
- **智能列名映射**：自动匹配用户输入的列名
- **派生字段生成**：自动生成时间、季节、风向等派生字段

## 使用方法

### 基本调用

```python
from custom_types.types import ReadDataParam

result = await correlation_analysis(
    read_data_param=ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="data.csv"
    ),
    correlation_vars=["变量1", "变量2"]
)
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `read_data_param` | ReadDataParam | 是 | 数据读取参数 |
| `correlation_vars` | List[str] | 是 | 相关性变量列表（2-10个） |
| `filters` | Dict[str, str] | 否 | 数据过滤条件 |
| `group_by` | List[str] | 否 | 分组列 |
| `correlation_method` | str | 否 | 相关性方法（默认pearson） |
| `min_sample_size` | int | 否 | 最小样本数（默认15） |
| `max_file_size_mb` | int | 否 | 最大文件大小（默认100MB） |

## 使用示例

### 1. 两变量相关性分析

```python
result = await correlation_analysis(
    read_data_param=ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="weather.csv"
    ),
    correlation_vars=["温度", "湿度"]
)
```

**输出：**
```
| 变量组合 | 相关性 |
|---|---|
| 温度 vs 湿度 | 0.856 |
```

### 2. 多变量相关性矩阵

```python
result = await correlation_analysis(
    read_data_param=ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="weather.csv"
    ),
    correlation_vars=["温度", "湿度", "压力", "风速"]
)
```

**输出：**
```
相关性矩阵 (方法: pearson)

| 变量 | 温度 | 湿度 | 压力 | 风速 |
|---|---|---|---|---|
| 温度 | 1.000 | 0.856 | 0.234 | -0.123 |
| 湿度 | 0.856 | 1.000 | 0.567 | 0.089 |
| 压力 | 0.234 | 0.567 | 1.000 | 0.345 |
| 风速 | -0.123 | 0.089 | 0.345 | 1.000 |
```

### 3. 分组分析

```python
result = await correlation_analysis(
    read_data_param=ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="weather.csv"
    ),
    correlation_vars=["温度", "湿度", "压力"],
    group_by=["季节"]
)
```

**输出：**
```
分组相关性矩阵 (方法: pearson)

**春**

| 变量 | 温度 | 湿度 | 压力 |
|---|---|---|---|
| 温度 | 1.000 | 0.856 | 0.234 |
| 湿度 | 0.856 | 1.000 | 0.567 |
| 压力 | 0.234 | 0.567 | 1.000 |

**夏**

| 变量 | 温度 | 湿度 | 压力 |
|---|---|---|---|
| 温度 | 1.000 | 0.723 | 0.445 |
| 湿度 | 0.723 | 1.000 | 0.678 |
| 压力 | 0.445 | 0.678 | 1.000 |
```

### 4. 高级配置

```python
result = await correlation_analysis(
    read_data_param=ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="large_dataset.csv"
    ),
    correlation_vars=["A", "B", "C", "D", "E"],
    filters={"类型": "实验组"},
    group_by=["批次"],
    correlation_method="spearman",
    min_sample_size=30,
    max_file_size_mb=500
)
```

## 支持的文件格式

- CSV (.csv)
- Excel (.xlsx, .xls)
- Parquet (.parquet)
- JSON (.json)
- Feather (.feather)
- HDF5 (.h5, .hdf)

## 相关性计算方法

| 方法 | 说明 | 适用场景 |
|------|------|----------|
| `pearson` | Pearson线性相关系数 | 线性关系，数据正态分布 |
| `spearman` | Spearman等级相关系数 | 单调关系，非正态分布 |
| `kendall` | Kendall τ相关系数 | 小样本，存在异常值 |

## 错误处理

### 常见错误及解决方案

1. **变量数量错误**
   ```
   ValueError: correlation_vars必须包含至少两个变量
   ```
   确保提供2-10个变量

2. **文件不存在**
   ```
   FileNotFoundError: 文件不存在
   ```
   检查文件路径是否正确

3. **不支持的文件类型**
   ```
   ValueError: 不支持的文件类型
   ```
   使用支持的文件格式

4. **数据不足**
   ```
   输出显示"数据不足"
   ```
   增加数据量或降低min_sample_size参数

## 性能建议

- **文件大小**：建议单个文件不超过100MB
- **变量数量**：建议不超过10个变量
- **数据量**：每组至少15个样本以获得可靠结果
- **内存使用**：大数据集建议分批处理

## 技术支持

如遇问题，请检查：
1. 数据文件格式是否正确
2. 变量名是否存在于数据中
3. 数据是否包含足够的数值型数据
4. 文件大小是否在限制范围内 