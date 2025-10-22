#!/usr/bin/env python3
"""
SonjayOS 系统性能监控脚本
用于监控AMD Ryzen 7 8845H和Radeon 780M的性能
"""

import psutil
import time
import json
import os
from datetime import datetime
import subprocess

class SystemMonitor:
    def __init__(self, config_path="config/hardware/hardware_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.monitoring = False
        
    def load_config(self):
        """加载硬件配置"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_cpu_info(self):
        """获取CPU信息"""
        cpu_info = {
            "usage_percent": psutil.cpu_percent(interval=1),
            "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            "temperature": self.get_cpu_temperature(),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True)
        }
        return cpu_info
    
    def get_memory_info(self):
        """获取内存信息"""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent,
            "free": memory.free
        }
    
    def get_gpu_info(self):
        """获取GPU信息"""
        try:
            # 尝试使用nvidia-smi或rocm-smi
            result = subprocess.run(['rocm-smi', '--showtemp', '--showuse', '--showmemuse'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return self.parse_rocm_output(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # 回退到基本GPU信息
        return {
            "temperature": 0,
            "utilization": 0,
            "memory_used": 0,
            "memory_total": 0
        }
    
    def parse_rocm_output(self, output):
        """解析ROCm输出"""
        lines = output.strip().split('\n')
        gpu_info = {
            "temperature": 0,
            "utilization": 0,
            "memory_used": 0,
            "memory_total": 0
        }
        
        for line in lines:
            if 'Temperature' in line:
                try:
                    temp = float(line.split(':')[1].strip().replace('C', ''))
                    gpu_info["temperature"] = temp
                except:
                    pass
            elif 'GPU use' in line:
                try:
                    usage = float(line.split(':')[1].strip().replace('%', ''))
                    gpu_info["utilization"] = usage
                except:
                    pass
        
        return gpu_info
    
    def get_cpu_temperature(self):
        """获取CPU温度"""
        try:
            # 尝试读取温度传感器
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read().strip()) / 1000
                return temp
        except:
            return 0
    
    def get_disk_info(self):
        """获取磁盘信息"""
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
    
    def get_network_info(self):
        """获取网络信息"""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    
    def get_system_status(self):
        """获取完整系统状态"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "gpu": self.get_gpu_info(),
            "disk": self.get_disk_info(),
            "network": self.get_network_info()
        }
    
    def check_performance_targets(self, status):
        """检查性能目标"""
        targets = self.config.get("performance_targets", {})
        results = {}
        
        # 检查CPU使用率
        if "idle_cpu_usage" in targets:
            target_cpu = float(targets["idle_cpu_usage"].replace("< ", "").replace("%", ""))
            results["cpu_usage"] = status["cpu"]["usage_percent"] < target_cpu
        
        # 检查内存使用率
        if "idle_memory_usage" in targets:
            target_memory = float(targets["idle_memory_usage"].replace("< ", "").replace("%", ""))
            results["memory_usage"] = status["memory"]["percent"] < target_memory
        
        # 检查GPU利用率
        if "gpu_utilization" in targets:
            target_gpu = float(targets["gpu_utilization"].replace("> ", "").replace("%", ""))
            results["gpu_utilization"] = status["gpu"]["utilization"] > target_gpu
        
        return results
    
    def generate_report(self):
        """生成性能报告"""
        status = self.get_system_status()
        performance_check = self.check_performance_targets(status)
        
        report = {
            "system_status": status,
            "performance_targets": performance_check,
            "recommendations": self.generate_recommendations(status, performance_check)
        }
        
        return report
    
    def generate_recommendations(self, status, performance_check):
        """生成优化建议"""
        recommendations = []
        
        # CPU建议
        if status["cpu"]["usage_percent"] > 80:
            recommendations.append("CPU使用率过高，建议关闭不必要的进程")
        
        if status["cpu"]["temperature"] > 80:
            recommendations.append("CPU温度过高，建议检查散热系统")
        
        # 内存建议
        if status["memory"]["percent"] > 90:
            recommendations.append("内存使用率过高，建议释放内存或增加内存")
        
        # GPU建议
        if status["gpu"]["utilization"] < 50:
            recommendations.append("GPU利用率较低，可以启用更多GPU加速功能")
        
        if status["gpu"]["temperature"] > 85:
            recommendations.append("GPU温度过高，建议检查散热系统")
        
        return recommendations
    
    def start_monitoring(self, interval=5):
        """开始监控"""
        self.monitoring = True
        print("开始系统性能监控...")
        
        while self.monitoring:
            try:
                status = self.get_system_status()
                performance_check = self.check_performance_targets(status)
                
                # 显示实时状态
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 系统状态:")
                print(f"  CPU: {status['cpu']['usage_percent']:.1f}% ({status['cpu']['temperature']:.1f}°C)")
                print(f"  内存: {status['memory']['percent']:.1f}%")
                print(f"  GPU: {status['gpu']['utilization']:.1f}% ({status['gpu']['temperature']:.1f}°C)")
                print(f"  磁盘: {status['disk']['percent']:.1f}%")
                
                # 检查性能目标
                if not all(performance_check.values()):
                    print("⚠️  性能目标未达到:")
                    for key, value in performance_check.items():
                        if not value:
                            print(f"    - {key}: 未达标")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n停止监控...")
                self.monitoring = False
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(interval)
    
    def save_report(self, filename=None):
        """保存性能报告"""
        if filename is None:
            filename = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.generate_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"性能报告已保存到: {filename}")

def main():
    monitor = SystemMonitor()
    
    print("SonjayOS 系统性能监控")
    print("=" * 40)
    
    while True:
        print("\n选择操作:")
        print("1. 实时监控")
        print("2. 生成报告")
        print("3. 查看当前状态")
        print("4. 退出")
        
        choice = input("请选择 (1-4): ").strip()
        
        if choice == '1':
            monitor.start_monitoring()
        elif choice == '2':
            monitor.save_report()
        elif choice == '3':
            status = monitor.get_system_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
        elif choice == '4':
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
