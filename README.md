
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
- **IP地址查询** - 支持IPv4/IPv6地址和域名查询
- **地理位置信息** - 精确的地理位置、运营商、ASN信息
- **中文本地化** - 自动翻译英文地名为中文显示
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
- ✅ **中文显示** - 地名、运营商自动翻译为中文
- ✅ **详细信息** - 地理位置、ISP、ASN、时区等完整信息

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
归属地: 美国 加利福尼亚州 山景城
邮政编码: 94043
运营商: 谷歌
组织: 谷歌
ASN: AS15169 谷歌
时区: America/Los_Angeles
坐标: 37.4056, -122.0775
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

### v1.3.0 (最新)
- ✨ 增强Ping测试功能 - 新增TCP端口连通性测试
- ✨ 智能备用机制 - ping不可用时自动切换TCP连接测试
- 🔧 优化端口测试 - 测试端口22,23,80,443,5000,6099,6185
- 🐛 修复ping命令找不到的问题
- 🔧 优化用户体验和错误处理


## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议发布。

---

<div align="center">

**感谢使用 astrbot_plugin_balance！**

如果觉得有用，请给个 ⭐ Star 支持一下！

</div>
