# correlation_analysis API 文档

## 函数概述

`correlation_analysis` 是一个异步函数，用于执行相关性分析。支持两变量和多变量相关性分析，包括分组分析和多种计算方法。

## 函数签名

```python
async def correlation_analysis(
    read_data_param: ReadDataParam,
    filters: Optional[Dict[str, str]] = None,
    group_by: Optional[List[str]] = None,
    correlation_vars: Optional[List[str]] = None,
    correlation_method: str = "pearson",
    min_sample_size: int = 15,
    max_file_size_mb: int = 100
) -> str
```

## 参数详解

### 必需参数

#### `read_data_param: ReadDataParam`
数据读取参数对象，包含以下字段：
- `read_data_method: str` - 数据读取方法，目前支持 "PANDAS"
- `read_data_query: str` - 数据文件路径

**示例：**
```python
ReadDataParam(
    read_data_method="PANDAS",
    read_data_query="/path/to/data.csv"
)
```

#### `correlation_vars: List[str]`
要分析相关性的变量列表
- **最少2个变量，最多10个变量**
- 变量名不能重复
- 支持中文列名，会自动进行列名映射

**示例：**
```python
correlation_vars=["温度", "湿度"]  # 两变量分析
correlation_vars=["温度", "湿度", "压力", "风速"]  # 多变量矩阵分析
```

### 可选参数

#### `filters: Optional[Dict[str, str]] = None`
数据过滤条件，键为列名，值为过滤值
```python
filters={"季节": "春", "地区": "北京"}
```

#### `group_by: Optional[List[str]] = None`
分组列名列表，支持多级分组
```python
group_by=["季节"]  # 单级分组
group_by=["季节", "地区"]  # 多级分组
```

#### `correlation_method: str = "pearson"`
相关性计算方法，支持：
- `"pearson"` - Pearson线性相关系数（默认）
- `"spearman"` - Spearman等级相关系数
- `"kendall"` - Kendall τ相关系数

#### `min_sample_size: int = 15`
最小样本数阈值，低于此数量的分组将标记为"数据不足"

#### `max_file_size_mb: int = 100`
最大文件大小限制（MB）

## 返回值

返回 `str` 类型的Markdown格式表格，包含相关性分析结果。

### 两变量分析输出格式
```markdown
| 变量组合 | 相关性 |
|---|---|
| 温度 vs 湿度 | 0.856 |
```

### 多变量矩阵输出格式
```markdown
相关性矩阵 (方法: pearson)

| 变量 | 温度 | 湿度 | 压力 |
|---|---|---|---|
| 温度 | 1.000 | 0.856 | 0.234 |
| 湿度 | 0.856 | 1.000 | 0.567 |
| 压力 | 0.234 | 0.567 | 1.000 |
```

### 分组分析输出格式
```markdown
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

## 调用示例

### 基础两变量分析
```python
from custom_types.types import ReadDataParam

result = await correlation_analysis(
    read_data_param=ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="weather_data.csv"
    ),
    correlation_vars=["温度", "湿度"]
)
print(result)
```

### 多变量矩阵分析
```python
result = await correlation_analysis(
    read_data_param=ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="sensor_data.csv"
    ),
    correlation_vars=["温度", "湿度", "压力", "风速"],
    correlation_method="spearman"
)
```

### 分组分析
```python
result = await correlation_analysis(
    read_data_param=ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="yearly_data.csv"
    ),
    correlation_vars=["温度", "湿度", "压力"],
    group_by=["季节"],
    filters={"年份": "2023"}
)
```

### 高级配置
```python
result = await correlation_analysis(
    read_data_param=ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="large_dataset.csv"
    ),
    correlation_vars=["变量A", "变量B", "变量C", "变量D"],
    filters={"类型": "实验组", "状态": "正常"},
    group_by=["批次", "时段"],
    correlation_method="kendall",
    min_sample_size=30,
    max_file_size_mb=500
)
```

## 异常处理

函数可能抛出以下异常：

### `ValueError`
- 变量数量不符合要求（少于2个或多于10个）
- 变量名重复
- 不支持的相关性方法
- 过滤条件错误

### `FileNotFoundError`
- 数据文件不存在

### `DataLoadError`
- 文件格式不支持
- 文件过大
- 数据为空

### `ColumnMappingError`
- 列名映射失败
- 找不到指定的列

## 支持的文件格式

- CSV (.csv)
- Excel (.xlsx, .xls)
- Parquet (.parquet)
- JSON (.json)
- Feather (.feather)
- HDF5 (.h5, .hdf)

## 智能特性

### 自动列名映射
函数会自动匹配用户输入的列名与数据文件中的实际列名：
```python
# 用户输入："温度"
# 自动匹配到：["Temperature", "temp", "气温", "温度值"] 等
```

### 派生字段生成
自动生成常用的派生字段：
- **时间字段**：自动解析和标准化
- **季节字段**：根据时间自动生成季节信息
- **风向方位**：将风向角度转换为中文方位

### 数据预处理
- 自动转换数值型数据
- 移除缺失值
- 数据质量验证

## 性能考虑

- **变量数量**：建议不超过10个变量
- **文件大小**：默认限制100MB，可调整
- **样本数量**：每组建议至少15个样本
- **内存使用**：大数据集会自动进行内存优化

## 注意事项

1. **异步调用**：必须使用 `await` 关键字
2. **数据类型**：相关性分析只适用于数值型数据
3. **缺失值**：包含缺失值的行会被自动移除
4. **文件路径**：确保文件路径正确且可访问
5. **列名匹配**：如果列名匹配失败，会抛出异常

## 最佳实践

1. **数据准备**：确保数据文件格式正确，列名清晰
2. **变量选择**：选择有意义的数值型变量进行分析
3. **方法选择**：根据数据分布选择合适的相关性方法
4. **分组策略**：合理设置分组，避免分组过细导致样本不足
5. **异常处理**：在调用时添加适当的异常处理逻辑 