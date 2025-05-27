#!/usr/bin/env python3
"""
通用日志模块功能测试
展示 UniversalLogger 的各种功能和使用场景
"""

from logger_config import create_logger, UniversalLogger, logger, default_log_config
import time
import os

def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 测试基本功能 ===")
    
    # 创建自定义日志器
    custom_logger = create_logger(
        app_name="test-app",
        log_dir="./test_logs",
        log_level="DEBUG"
    )
    
    logger_instance = custom_logger.get_logger()
    
    # 测试各种日志级别
    logger_instance.debug("这是DEBUG消息")
    logger_instance.info("这是INFO消息")
    logger_instance.warning("这是WARNING消息")
    logger_instance.error("这是ERROR消息")
    logger_instance.critical("这是CRITICAL消息")

def test_tagged_logging():
    """测试带标签的日志"""
    print("\n=== 测试带标签的日志 ===")
    
    # 使用默认日志器
    default_log_config.log_with_tag("info", "这是带标签的消息", "USER")
    default_log_config.log_with_tag("warning", "这是警告消息", "SYSTEM")
    default_log_config.log_with_tag("error", "这是错误消息", "API")

def test_user_actions():
    """测试用户行为日志"""
    print("\n=== 测试用户行为日志 ===")
    
    default_log_config.log_user_action("登录", "成功登录系统", "user123")
    default_log_config.log_user_action("查看", "访问首页", "user456")
    default_log_config.log_user_action("退出", "用户主动退出", "user123")

def test_api_requests():
    """测试API请求日志"""
    print("\n=== 测试API请求日志 ===")
    
    default_log_config.log_api_request("GET", "/api/users", 200, 0.125, "user123")
    default_log_config.log_api_request("POST", "/api/orders", 201, 0.234)
    default_log_config.log_api_request("DELETE", "/api/users/456", 404, 0.089, "admin")

def test_performance_logging():
    """测试性能日志"""
    print("\n=== 测试性能日志 ===")
    
    # 模拟一些操作
    start_time = time.time()
    time.sleep(0.1)  # 模拟操作耗时
    duration = time.time() - start_time
    
    default_log_config.log_performance("数据库查询", duration, "查询用户表")
    default_log_config.log_performance("文件处理", 0.456, "处理100MB文件")
    default_log_config.log_performance("API调用", 1.234, "调用第三方服务")

def test_business_events():
    """测试业务事件日志"""
    print("\n=== 测试业务事件日志 ===")
    
    default_log_config.log_business_event("用户注册", {
        "user_id": "12345",
        "email": "user@example.com",
        "source": "web"
    })
    
    default_log_config.log_business_event("订单创建", {
        "order_id": "ORD-001",
        "user_id": "12345",
        "amount": 99.99,
        "items": 3
    })
    
    default_log_config.log_business_event("支付完成", {
        "order_id": "ORD-001",
        "payment_method": "credit_card",
        "transaction_id": "TXN-456"
    })

def test_error_context():
    """测试错误上下文日志"""
    print("\n=== 测试错误上下文日志 ===")
    
    try:
        # 模拟一个错误
        result = 10 / 0
    except Exception as e:
        default_log_config.log_error_with_context(e, {
            "operation": "division",
            "dividend": 10,
            "divisor": 0,
            "user_id": "user123"
        })
    
    try:
        # 模拟另一个错误
        undefined_variable.some_method()
    except Exception as e:
        default_log_config.log_error_with_context(e, {
            "module": "test_module",
            "function": "test_function",
            "line": 42
        })

def test_security_events():
    """测试安全事件日志"""
    print("\n=== 测试安全事件日志 ===")
    
    default_log_config.log_security_event("登录失败", "WARNING", "用户名: admin, IP: 192.168.1.100, 尝试次数: 3")
    default_log_config.log_security_event("权限提升", "INFO", "用户 user123 被授予管理员权限")
    default_log_config.log_security_event("异常访问", "ERROR", "IP 10.0.0.1 尝试访问受限资源")

def test_file_management():
    """测试文件管理功能"""
    print("\n=== 测试文件管理功能 ===")
    
    # 获取日志文件信息
    files_info = default_log_config.get_log_files_info()
    print(f"找到 {files_info.get('total_files', 0)} 个日志文件")
    
    for file_info in files_info.get('files', [])[:3]:  # 只显示前3个
        print(f"  {file_info['name']} - {file_info['size_mb']}MB - {file_info['modified']}")
    
    # 读取日志文件内容（如果存在）
    if files_info.get('files'):
        latest_file = files_info['files'][0]
        print(f"\n读取最新日志文件: {latest_file['name']}")
        
        try:
            content = default_log_config.read_log_file(latest_file['name'], lines=5)
            print(f"文件总行数: {content['total_lines']}")
            print(f"显示行数: {content['showing_lines']}")
            print("最后5行内容:")
            print(content['content'][-200:] + "...")  # 只显示最后200个字符
        except Exception as e:
            print(f"读取文件时出错: {e}")

def test_different_configurations():
    """测试不同配置的日志器"""
    print("\n=== 测试不同配置的日志器 ===")
    
    # 只输出到文件的日志器
    file_only_logger = UniversalLogger(
        app_name="file-only",
        log_dir="./test_logs",
        console_output=False,
        file_output=True
    )
    file_only_logger.get_logger().info("这条消息只会保存到文件")
    
    # 只输出到控制台的日志器
    console_only_logger = UniversalLogger(
        app_name="console-only",
        console_output=True,
        file_output=False
    )
    console_only_logger.get_logger().info("这条消息只会显示在控制台")
    
    # 自定义格式的日志器
    custom_format_logger = UniversalLogger(
        app_name="custom-format",
        log_dir="./test_logs",
        custom_format="{time:HH:mm:ss} | {level} | {message}"
    )
    custom_format_logger.get_logger().info("这是自定义格式的消息")

def test_dynamic_features():
    """测试动态功能"""
    print("\n=== 测试动态功能 ===")
    
    # 创建测试日志器
    dynamic_logger = create_logger(app_name="dynamic-test", log_dir="./test_logs")
    
    # 动态修改日志级别
    dynamic_logger.set_log_level("DEBUG")
    dynamic_logger.get_logger().debug("现在可以看到DEBUG消息了")
    
    # 添加额外的文件处理器
    dynamic_logger.add_file_handler(
        "./test_logs/special.log",
        level="WARNING",
        rotation="1 MB"
    )
    dynamic_logger.get_logger().warning("这条警告消息会同时保存到两个文件")

def cleanup_test_files():
    """清理测试文件"""
    print("\n=== 清理测试文件 ===")
    
    import shutil
    test_dirs = ["./test_logs", "./logs"]
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
                print(f"已删除测试目录: {test_dir}")
            except Exception as e:
                print(f"删除目录 {test_dir} 时出错: {e}")

def main():
    """主测试函数"""
    print("🚀 开始通用日志模块功能测试")
    print("=" * 50)
    
    try:
        # 执行各种测试
        test_basic_functionality()
        test_tagged_logging()
        test_user_actions()
        test_api_requests()
        test_performance_logging()
        test_business_events()
        test_error_context()
        test_security_events()
        test_file_management()
        test_different_configurations()
        test_dynamic_features()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成！日志功能正常工作。")
        print("📁 日志文件已保存到 ./logs 目录")
        print("📁 测试日志文件已保存到 ./test_logs 目录")
        
        # 询问是否清理测试文件
        clean_up = input("\n是否删除测试文件？(y/N): ").lower().strip()
        if clean_up == 'y':
            cleanup_test_files()
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        logger.error(f"测试失败: {e}")

if __name__ == "__main__":
    main() 