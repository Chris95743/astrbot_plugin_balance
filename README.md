
<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_balance?name=astrbot_plugin_balance&theme=minecraft&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_balance

_✨ [astrbot](https://github.com/AstrBotDevs/AstrBot) 全能网络工具 - 余额查询、IP查询、网络测试 ✨_  

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4%2B-orange.svg)](https://github.com/Soulter/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-Chris-blue)](https://github.com/Chris95743)

</div>

## 🚀 功能特色

### 💰 余额查询
- **硅基流动** - 查询账户余额、充值余额、总余额等详细信息
- **DeepSeek** - 查询AI平台余额信息
- **OpenAI** - 查询GPT平台账户额度和使用情况

### 🌐 网络工具
- **IP地址查询** - 支持IPv4/IPv6地址和域名查询，原生中文支持
- **增强地理信息** - 详细的地理位置、ISP运营商、ASN、特殊属性标识
- **智能识别** - 自动检测移动网络、代理/VPN、托管服务等特殊属性
- **增强Ping测试** - 双重网络测试（ICMP + TCP端口连通性）
- **智能备用** - ping命令不可用时自动切换TCP连接测试

## 📦 安装方式

### 方式一：插件市场安装（推荐）
1. 在AstrBot插件市场搜索 `astrbot_plugin_balance`
2. 点击安装，等待安装完成
3. 重启AstrBot即可使用

### 方式二：手动克隆安装
```bash
# 进入插件目录
cd /AstrBot/data/plugins

# 克隆仓库
git clone https://github.com/Chris95743/astrbot_plugin_balance

# 重启AstrBot
```

### 🐳 Docker用户特别说明
**重要**: Docker环境默认不包含ping命令，为获得最佳网络测试体验，建议安装：

```bash
# 进入Docker容器
docker exec -it <容器名> /bin/bash

# 安装ping命令
apt-get update && apt-get install -y iputils-ping

# 退出容器
exit
```

**说明**：
- ✅ 不安装ping也能正常使用，插件会自动切换到TCP连接测试
- ✅ 安装ping后可获得更准确的延迟和丢包率测试
- ✅ 所有其他功能（余额查询、IP查询）不受影响

## ⌨️ 使用指南

### 💰 余额查询命令

```plaintext
/硅基余额 <API密钥>     # 查询硅基流动平台余额
/DS余额 <API密钥>       # 查询DeepSeek平台余额  
/GPT余额 <API密钥>      # 查询OpenAI平台余额
```

**使用示例：**
```
/硅基余额 sk-xxxxxxxxxxxxxxxxxxxxx
/DS余额 sk-xxxxxxxxxxxxxxxxxxxxx
/GPT余额 sk-xxxxxxxxxxxxxxxxxxxxx
```

### 🌐 网络工具命令

```plaintext
/查询IP <IP/域名>       # 查询IP地址或域名信息（含IPv6支持）
/ping <域名/IP>         # 增强网络测试（ICMP + 端口连通性）
/查询帮助              # 显示所有命令帮助
```

**使用示例：**
```
/查询IP google.com      # 查询域名的IPv4/IPv6及详细信息
/查询IP 8.8.8.8         # 查询IP地址详细信息
/ping baidu.com         # 双重网络测试
/ping 114.514.1919.810  # 测试IP地址连通性
```

## 📊 功能详解

### IP查询功能特点
- ✅ **双栈支持** - 同时显示IPv4和IPv6地址
- ✅ **智能识别** - 自动识别输入类型（IP地址/域名）
- ✅ **原生中文** - API直接返回中文地理信息
- ✅ **增强信息** - 详细的地理位置、ISP运营商、ASN、时区信息
- ✅ **特殊属性** - 自动检测移动网络、代理/VPN、托管服务等特殊属性
- ✅ **结构化输出** - 分类显示地理位置、网络信息、特殊属性

### 增强Ping测试功能特点
- ✅ **双重测试** - ICMP Ping + TCP端口连通性测试
- ✅ **多端口检测** - 测试端口：22, 23, 80, 443, 5000, 6099, 6185
- ✅ **跨平台支持** - Windows/Linux/macOS全支持
- ✅ **智能解析** - 自动处理中英文ping输出
- ✅ **智能备用** - ping不可用时自动切换TCP测试
- ✅ **网络质量评估** - 根据延迟自动评估网络质量
- ✅ **连接稳定性** - 丢包率分析和稳定性评估

### 输出示例

#### IP查询示例输出：
```
🔍 查询目标: google.com (域名)

IPv4地址: 142.250.191.14
IPv6地址: 2404:6800:4008:c06::71

详细信息 (基于IPv4: 142.250.191.14):
🌍 地理位置:
  国家: 美国 (US)
  省/州: 加利福尼亚州 (CA)
  城市: 山景城
  邮政编码: 94043
  坐标: 37.4056, -122.0775
  时区: America/Los_Angeles

🏢 网络信息:
  ISP运营商: 谷歌
  组织机构: 谷歌云平台
  ASN编号: AS15169
  ASN名称: GOOGLE

🏷️ 特殊属性:
  🖥️ 托管服务
```

#### 增强Ping测试示例输出：
```
Ping测试结果 - baidu.com:
发送数据包: 4个
接收数据包: 4个
丢包率: 0%
最小延迟: 23.50ms
最大延迟: 25.80ms
平均延迟: 24.65ms
网络质量: 优秀
连接稳定性: 稳定

🔌 端口连通性测试:
测试端口: 3/7个可连接
平均连接时间: 45ms
端口测试详情:
  ❌ 端口22: 超时
  ❌ 端口23: 超时
  ✅ 端口80: 43ms
  ✅ 端口443: 47ms
  ✅ 端口5000: 44ms
  ❌ 端口6099: 超时
  ❌ 端口6185: 超时
```

#### 备用连通性测试示例输出（ping不可用时）：
```
连通性测试 - example.com:
⚠️ 系统ping命令不可用，使用TCP连接测试

✅ 域名解析: 成功
测试端口: 3/7个可连接
平均连接时间: 45ms
连接质量: 优秀
主机状态: 可达

端口测试详情:
  ❌ 端口22: 超时
  ❌ 端口23: 超时
  ✅ 端口80: 43ms
  ✅ 端口443: 47ms
  ✅ 端口5000: 44ms
  ❌ 端口6099: 超时
  ❌ 端口6185: 超时

💡 提示: 请安装ping命令获得更准确的延迟测试
```

## 🔒 安全提醒

- ⚠️ **API密钥安全** - 建议私聊使用余额查询功能，避免在群聊中暴露API密钥
- ⚠️ **数据隐私** - IP查询功能使用第三方API服务，请注意数据隐私
- ⚠️ **使用频率** - 合理使用查询功能，避免频繁请求

## 📋 依赖说明

### Python依赖
- **aiohttp>=3.8.0** - 异步HTTP请求库（唯一外部依赖）

### 系统工具（可选）
- **ping** - 系统ping命令（推荐安装以获得更准确的延迟测试）
- **Python标准库** - asyncio, platform, subprocess, re, socket, datetime

### 特点
- 🔧 **依赖最小化** - 仅需1个外部Python包
- 🔄 **智能降级** - 系统工具不可用时自动使用Python实现
- 🌍 **跨平台兼容** - 自动适配不同操作系统

## 👥 贡献指南

- 🌟 **Star项目** - 点击右上角星星支持项目
- 🐛 **报告问题** - 提交Issue报告Bug
- 💡 **功能建议** - 提出新功能想法
- 🔧 **代码贡献** - 提交Pull Request改进代码

## 📞 联系方式

- **QQ交流**: 1436198704
- **GitHub**: [Chris95743](https://github.com/Chris95743)
- **问题反馈**: [Issues页面](https://github.com/Chris95743/astrbot_plugin_balance/issues)

## 📝 更新日志

### v1.4.0 (最新)
- ✨ **全面升级IP查询** - 大幅增强IP查询功能，支持更多信息字段
- 🌍 **原生中文支持** - API直接返回中文地理信息，无需本地翻译
- 🏷️ **特殊属性检测** - 自动识别移动网络、代理/VPN、托管服务等
- 📊 **结构化输出** - 重新设计输出格式，信息分类更清晰
- 🔧 **代码优化重构** - 大幅简化代码结构，提升性能和可维护性
- 🐛 **修复ping解析** - 修复Linux系统ping输出解析问题
- 📖 **完善文档** - 新增Docker用户安装ping命令的详细说明


## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议发布。

---

<div align="center">

**感谢使用 astrbot_plugin_balance！**

如果觉得有用，请给个 ⭐ Star 支持一下！

</div>
