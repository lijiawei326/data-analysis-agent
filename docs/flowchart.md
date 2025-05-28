flowchart TD
    A[Agent请求] --> B[可视化MCP服务器]
    B --> C[参数检测器]
    
    C --> D{检测输入模式}
    D -->|有correlation_result| E[结果模式]
    D -->|有correlation_params| F[分析模式]
    D -->|有data_source+variables| G[数据模式]
    D -->|参数不足| H[错误：参数不足]
    
    E --> I[直接解析结果]
    I --> J[生成图表]
    
    F --> K[缓存检查器]
    K --> L{相关性结果缓存?}
    L -->|命中| M[使用缓存结果]
    L -->|未命中| N[数据缓存检查]
    
    N --> O{数据文件缓存?}
    O -->|命中| P[使用缓存数据]
    O -->|未命中| Q[加载原始数据]
    Q --> R[存入数据缓存]
    
    P --> S[调用correlation_analysis]
    R --> S
    S --> T[存入相关性缓存]
    T --> U[解析相关性结果]
    M --> U
    U --> J
    
    G --> V[数据缓存检查2]
    V --> W{数据文件缓存?}
    W -->|命中| X[使用缓存数据]
    W -->|未命中| Y[加载原始数据]
    Y --> Z[存入数据缓存]
    X --> AA[生成通用图表]
    Z --> AA
    AA --> J
    
    J --> BB[图表缓存检查]
    BB --> CC{图表文件缓存?}
    CC -->|命中| DD[返回缓存路径]
    CC -->|未命中| EE[生成新图表]
    EE --> FF[存入图表缓存]
    FF --> GG[返回图表路径]
    DD --> GG
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style K fill:#fff3e0
    style BB fill:#fff3e0
    style J fill:#e8f5e8
    style GG fill:#e8f5e8