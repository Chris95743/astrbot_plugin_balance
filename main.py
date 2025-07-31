import aiohttp
import asyncio
import platform
import subprocess
import re
import socket
from datetime import datetime
from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import AstrBotConfig
from astrbot.api.star import Context, Star, register

# 硅基流动余额查询
async def query_siliconflow_balance(api_key):
    url = "https://api.siliconflow.cn/v1/user/info"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('status') and data.get('data'):
                    balance_info = data['data']
                    result = (
                        f"硅基流动账户余额信息:\n"
                        f"用户ID: {balance_info['id']}\n"
                        f"用户名: {balance_info['name']}\n"
                        f"邮箱: {balance_info['email']}\n"
                        f"余额(美元): {balance_info['balance']}\n"
                        f"充值余额(美元): {balance_info['chargeBalance']}\n"
                        f"总余额(美元): {balance_info['totalBalance']}\n"
                    )
                    return result
                else:
                    return "获取硅基流动余额失败：" + data.get('message', '未知错误')
        except aiohttp.ClientError as e:
            return f"请求错误: {e}"

# OpenAI余额查询
async def query_openai_balance(api_key):
    base_url = "https://api.openai.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # 获取今天的日期（格式：YYYY-MM-DD）
        today = datetime.today().strftime('%Y-%m-%d')

        subscription_url = f"{base_url}/v1/dashboard/billing/subscription"
        async with aiohttp.ClientSession() as session:
            async with session.get(subscription_url, headers=headers) as subscription_response:
                subscription_response.raise_for_status()
                subscription_data = await subscription_response.json()

            usage_url = f"{base_url}/v1/dashboard/billing/usage?start_date={today}&end_date={today}"
            async with aiohttp.ClientSession() as session:
                async with session.get(usage_url, headers=headers) as usage_response:
                    usage_response.raise_for_status()
                    usage_data = await usage_response.json()

        account_balance = subscription_data[0].get("soft_limit_usd", 0)
        used_balance = usage_data.get("total_usage", 0) / 100
        remaining_balance = account_balance - used_balance

        result = (
            f"OpenAI账户余额信息:\n"
            f"是否已绑定支付方式: {'是' if subscription_data[0].get('has_payment_method') else '否'}\n"
            f"账户额度(美元): {account_balance:.2f}\n"
            f"已使用额度(美元): {used_balance:.2f}\n"
            f"剩余额度(美元): {remaining_balance:.2f}\n"
            f"API访问权限截止时间: {subscription_data[0].get('access_until', '无限制')}\n"
        )
        return result
    except aiohttp.ClientError as e:
        return f"请求错误: {e}"

# DeepSeek余额查询
async def query_ds_balance(api_key):
    url = "https://api.deepseek.com/user/balance"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('is_available') is False:
                    return "DeepSeek账户不可用或无余额信息（未充值）"

                balance_info = data['balance_infos'][0]
                result = (
                    f"DeepSeek账户余额信息:\n"
                    f"币种: {balance_info['currency']}\n"
                    f"总余额: {balance_info['total_balance']}\n"
                    f"已授予余额: {balance_info['granted_balance']}\n"
                    f"充值余额: {balance_info['topped_up_balance']}\n"
                )
                return result
        except aiohttp.ClientError as e:
            return f"请求错误: {e}"

# Ping域名功能
async def ping_host(host, count=4):
    """使用系统ping命令测试主机连通性和延迟"""
    try:
        # 根据操作系统选择ping命令参数
        system = platform.system().lower()
        
        # 尝试不同的ping命令路径
        ping_commands = []
        if system == "windows":
            ping_commands = [
                ["ping", "-n", str(count), host],
                ["C:\\Windows\\System32\\ping.exe", "-n", str(count), host],
                ["ping.exe", "-n", str(count), host]
            ]
        else:
            ping_commands = [
                ["ping", "-c", str(count), host],
                ["/bin/ping", "-c", str(count), host],
                ["/usr/bin/ping", "-c", str(count), host],
                ["/sbin/ping", "-c", str(count), host]
            ]
        
        # 尝试执行ping命令
        last_error = None
        for cmd in ping_commands:
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                
                if process.returncode == 0:
                    output = decode_output(stdout)
                    ping_result = parse_ping_output(output, host)
                    
                    # 在ping成功时也测试端口连通性
                    port_result = await port_connectivity_test(host)
                    return ping_result + port_result
                else:
                    error = decode_output(stderr)
                    last_error = f"Ping命令执行失败: {error}"
                    
            except FileNotFoundError:
                continue  # 尝试下一个ping命令路径
            except Exception as e:
                last_error = str(e)
                continue
        
        # 如果所有ping命令都失败，使用Python实现的简单连通性测试
        return await fallback_connectivity_test(host)
            
    except asyncio.TimeoutError:
        return f"Ping超时: {host} (30秒无响应)"
    except Exception as e:
        return await fallback_connectivity_test(host)

async def fallback_connectivity_test(host, timeout=3):
    """备用连通性测试（当ping命令不可用时）"""
    import time
    
    result = f"连通性测试 - {host}:\n"
    result += "⚠️ 系统ping命令不可用，使用TCP连接测试\n\n"
    
    # 指定端口列表（从小到大排列）
    test_ports = [22, 23, 80, 443, 5000, 6099, 6185]
    successful_connections = 0
    total_time = 0
    connection_results = []
    
    try:
        # 首先尝试解析域名
        try:
            socket.gethostbyname(host)
            result += f"✅ 域名解析: 成功\n"
        except socket.gaierror:
            result += f"❌ 域名解析: 失败\n"
            return result
        
        # 测试指定端口的连通性
        for port in test_ports:
            start_time = time.time()
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                total_time += response_time
                successful_connections += 1
                connection_results.append(f"✅ 端口{port}: {response_time:.0f}ms")
                
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                connection_results.append(f"❌ 端口{port}: 超时")
            except Exception:
                connection_results.append(f"❌ 端口{port}: 失败")
        
        # 构建结果
        result += f"测试端口: {successful_connections}/{len(test_ports)}个可连接\n"
        
        if successful_connections > 0:
            avg_time = total_time / successful_connections
            result += f"平均连接时间: {avg_time:.0f}ms\n"
            
            if avg_time < 100:
                quality = "优秀"
            elif avg_time < 300:
                quality = "良好"
            else:
                quality = "一般"
            result += f"连接质量: {quality}\n"
            result += f"主机状态: 可达\n\n"
        else:
            result += f"连接质量: 无法连接\n"
            result += f"主机状态: 不可达\n\n"
        
        result += "端口测试详情:\n"
        for conn_result in connection_results:
            result += f"  {conn_result}\n"
            
        result += "\n💡 提示: 请安装ping命令获得更准确的延迟测试"
        
    except Exception as e:
        result += f"连通性测试失败: {str(e)}"
    
    return result

async def port_connectivity_test(host, timeout=3):
    """端口连通性测试"""
    import time
    
    # 指定端口列表（从小到大排列）
    test_ports = [22, 23, 80, 443, 5000, 6099, 6185]
    successful_connections = 0
    total_time = 0
    connection_results = []
    
    try:
        # 测试指定端口的连通性
        for port in test_ports:
            start_time = time.time()
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                total_time += response_time
                successful_connections += 1
                connection_results.append(f"✅ 端口{port}: {response_time:.0f}ms")
                
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                connection_results.append(f"❌ 端口{port}: 超时")
            except Exception:
                connection_results.append(f"❌ 端口{port}: 失败")
        
        # 构建结果
        result = f"\n🔌 端口连通性测试:\n"
        result += f"测试端口: {successful_connections}/{len(test_ports)}个可连接\n"
        
        if successful_connections > 0:
            avg_time = total_time / successful_connections
            result += f"平均连接时间: {avg_time:.0f}ms\n"
        
        result += "端口测试详情:\n"
        for conn_result in connection_results:
            result += f"  {conn_result}\n"
        
        return result
        
    except Exception as e:
        return f"\n🔌 端口连通性测试失败: {str(e)}"

def decode_output(data):
    """尝试多种编码方式解码输出"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'cp936', 'latin1']
    
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    
    # 如果所有编码都失败，使用utf-8并忽略错误
    return data.decode('utf-8', errors='ignore')

def parse_ping_output(output, host):
    """解析ping命令输出"""
    lines = output.split('\n')
    
    # 提取基本信息
    result = f"Ping测试结果 - {host}:\n"
    
    # 查找延迟信息
    delays = []
    packet_loss = "未知"
    packets_sent = 0
    packets_received = 0
    
    for line in lines:
        line = line.strip()
        
        # 解析延迟时间（支持中英文和各种格式）
        # 英文格式: time=165ms
        # 中文格式: 时间=165ms 或 ʱ=165ms (编码问题)
        if 'time=' in line.lower() or '时间=' in line or 'ʱ=' in line:
            # 使用正则表达式提取数字
            time_match = re.search(r'(?:time=|时间=|ʱ=)(\d+(?:\.\d+)?)ms', line, re.IGNORECASE)
            if time_match:
                try:
                    delay = float(time_match.group(1))
                    delays.append(delay)
                except ValueError:
                    pass
        
        # 解析丢包率（支持中英文）
        # 英文: (0% packet loss) 或 (0% loss)
        # 中文: (0% 丢失) 或类似格式
        if '% packet loss' in line.lower() or '% loss' in line.lower() or '% 丢失' in line or '%' in line:
            # 提取百分比数字
            loss_match = re.search(r'(\d+(?:\.\d+)?)%', line)
            if loss_match:
                packet_loss = f"{loss_match.group(1)}%"
        
        # 解析数据包统计（Windows中文格式）
        # 数据包: 已发送 = 4，已接收 = 4，丢失 = 0 (0% 丢失)
        if '已发送' in line or '已接收' in line or 'ѷ' in line or 'ѽ' in line:
            sent_match = re.search(r'(?:已发送|ѷ)\s*=\s*(\d+)', line)
            recv_match = re.search(r'(?:已接收|ѽ)\s*=\s*(\d+)', line)
            if sent_match:
                packets_sent = int(sent_match.group(1))
            if recv_match:
                packets_received = int(recv_match.group(1))
    
    # 构建结果
    if delays:
        min_delay = min(delays)
        max_delay = max(delays)
        avg_delay = sum(delays) / len(delays)
        
        # 如果有数据包统计，使用它；否则使用延迟数据个数
        sent_count = packets_sent if packets_sent > 0 else len(delays)
        recv_count = packets_received if packets_received > 0 else len(delays)
        
        result += f"发送数据包: {sent_count}个\n"
        result += f"接收数据包: {recv_count}个\n"
        result += f"丢包率: {packet_loss}\n"
        result += f"最小延迟: {min_delay:.2f}ms\n"
        result += f"最大延迟: {max_delay:.2f}ms\n"
        result += f"平均延迟: {avg_delay:.2f}ms\n"
        
        # 网络质量评估
        if avg_delay < 50:
            quality = "优秀"
        elif avg_delay < 100:
            quality = "良好"  
        elif avg_delay < 200:
            quality = "一般"
        else:
            quality = "较差"
        
        result += f"网络质量: {quality}"
        
        # 如果解析出丢包率，提供连接稳定性评估
        if packet_loss != "未知" and packet_loss != "0%":
            result += f"\n连接稳定性: 有丢包，建议检查网络"
        elif packet_loss == "0%":
            result += f"\n连接稳定性: 稳定"
            
    else:
        result += "无法解析延迟信息\n"
        result += f"丢包率: {packet_loss}\n"
        
        # 如果有原始的数据包统计但没有延迟，至少显示连通性
        if packets_sent > 0:
            result += f"发送数据包: {packets_sent}个\n"
            result += f"接收数据包: {packets_received}个\n"
            if packets_received > 0:
                result += "连接状态: 可达\n"
            else:
                result += "连接状态: 不可达\n"
        
        # 显示部分原始输出用于调试
        result += "\n原始输出片段:\n" + output[:300] + "..."
    
    return result

# 查询IP地址信息的API URL
IP_API_URL = "http://ip-api.com/json/"

# 中英文对照表
TRANSLATION_MAP = {
    # 国家名称
    'United States': '美国',
    'China': '中国',
    'Japan': '日本',
    'South Korea': '韩国',
    'United Kingdom': '英国',
    'Germany': '德国',
    'France': '法国',
    'Russia': '俄罗斯',
    'Canada': '加拿大',
    'Australia': '澳大利亚',
    'Singapore': '新加坡',
    'Hong Kong': '香港',
    'Taiwan': '台湾',
    'India': '印度',
    'Brazil': '巴西',
    'Netherlands': '荷兰',
    'Switzerland': '瑞士',
    'Sweden': '瑞典',
    'Norway': '挪威',
    'Denmark': '丹麦',
    'Finland': '芬兰',
    'Italy': '意大利',
    'Spain': '西班牙',
    'Poland': '波兰',
    'Turkey': '土耳其',
    'Mexico': '墨西哥',
    'Argentina': '阿根廷',
    'Chile': '智利',
    'Colombia': '哥伦比亚',
    'Peru': '秘鲁',
    'Venezuela': '委内瑞拉',
    'Ecuador': '厄瓜多尔',
    'Uruguay': '乌拉圭',
    'Paraguay': '巴拉圭',
    'Bolivia': '玻利维亚',
    'Thailand': '泰国',
    'Vietnam': '越南',
    'Malaysia': '马来西亚',
    'Indonesia': '印度尼西亚',
    'Philippines': '菲律宾',
    'Myanmar': '缅甸',
    'Cambodia': '柬埔寨',
    'Laos': '老挝',
    'Bangladesh': '孟加拉国',
    'Pakistan': '巴基斯坦',
    'Sri Lanka': '斯里兰卡',
    'Nepal': '尼泊尔',
    'Maldives': '马尔代夫',
    'Iran': '伊朗',
    'Iraq': '伊拉克',
    'Israel': '以色列',
    'Jordan': '约旦',
    'Lebanon': '黎巴嫩',
    'Syria': '叙利亚',
    'Kuwait': '科威特',
    'Saudi Arabia': '沙特阿拉伯',
    'United Arab Emirates': '阿联酋',
    'Qatar': '卡塔尔',
    'Bahrain': '巴林',
    'Oman': '阿曼',
    'Yemen': '也门',
    'Egypt': '埃及',
    'Libya': '利比亚',
    'Tunisia': '突尼斯',
    'Algeria': '阿尔及利亚',
    'Morocco': '摩洛哥',
    'Sudan': '苏丹',
    'Ethiopia': '埃塞俄比亚',
    'Kenya': '肯尼亚',
    'Tanzania': '坦桑尼亚',
    'Uganda': '乌干达',
    'Rwanda': '卢旺达',
    'South Africa': '南非',
    'Nigeria': '尼日利亚',
    'Ghana': '加纳',
    'Ivory Coast': '科特迪瓦',
    'Senegal': '塞内加尔',
    'Mali': '马里',
    'Burkina Faso': '布基纳法索',
    'Niger': '尼日尔',
    'Chad': '乍得',
    'Cameroon': '喀麦隆',
    'Central African Republic': '中非共和国',
    'Democratic Republic of the Congo': '刚果民主共和国',
    'Republic of the Congo': '刚果共和国',
    'Gabon': '加蓬',
    'Equatorial Guinea': '赤道几内亚',
    'São Tomé and Príncipe': '圣多美和普林西比',
    'Cape Verde': '佛得角',
    'Guinea-Bissau': '几内亚比绍',
    'Guinea': '几内亚',
    'Sierra Leone': '塞拉利昂',
    'Liberia': '利比里亚',
    'New Zealand': '新西兰',
    'Fiji': '斐济',
    'Papua New Guinea': '巴布亚新几内亚',
    'Vanuatu': '瓦努阿图',
    'Solomon Islands': '所罗门群岛',
    'Samoa': '萨摩亚',
    'Tonga': '汤加',
    'Kiribati': '基里巴斯',
    'Tuvalu': '图瓦卢',
    'Nauru': '瑙鲁',
    'Palau': '帕劳',
    'Marshall Islands': '马绍尔群岛',
    'Micronesia': '密克罗尼西亚',
    
    # 美国州名
    'California': '加利福尼亚州',
    'New York': '纽约州',
    'Texas': '得克萨斯州',
    'Florida': '佛罗里达州',
    'Pennsylvania': '宾夕法尼亚州',
    'Illinois': '伊利诺伊州',
    'Ohio': '俄亥俄州',
    'Georgia': '乔治亚州',
    'North Carolina': '北卡罗来纳州',
    'Michigan': '密歇根州',
    'New Jersey': '新泽西州',
    'Virginia': '弗吉尼亚州',
    'Washington': '华盛顿州',
    'Arizona': '亚利桑那州',
    'Massachusetts': '马萨诸塞州',
    'Tennessee': '田纳西州',
    'Indiana': '印第安纳州',
    'Missouri': '密苏里州',
    'Maryland': '马里兰州',
    'Wisconsin': '威斯康星州',
    'Colorado': '科罗拉多州',
    'Minnesota': '明尼苏达州',
    'South Carolina': '南卡罗来纳州',
    'Alabama': '阿拉巴马州',
    'Louisiana': '路易斯安那州',
    'Kentucky': '肯塔基州',
    'Oregon': '俄勒冈州',
    'Oklahoma': '俄克拉荷马州',
    'Connecticut': '康涅狄格州',
    'Utah': '犹他州',
    'Iowa': '爱荷华州',
    'Nevada': '内华达州',
    'Arkansas': '阿肯色州',
    'Mississippi': '密西西比州',
    'Kansas': '堪萨斯州',
    'New Mexico': '新墨西哥州',
    'Nebraska': '内布拉斯加州',
    'West Virginia': '西弗吉尼亚州',
    'Idaho': '爱达荷州',
    'Hawaii': '夏威夷州',
    'New Hampshire': '新罕布什尔州',
    'Maine': '缅因州',
    'Montana': '蒙大拿州',
    'Rhode Island': '罗得岛州',
    'Delaware': '特拉华州',
    'South Dakota': '南达科他州',
    'North Dakota': '北达科他州',
    'Alaska': '阿拉斯加州',
    'Vermont': '佛蒙特州',
    'Wyoming': '怀俄明州',
    
    # 城市名称
    'New York City': '纽约市',
    'Los Angeles': '洛杉矶',
    'Chicago': '芝加哥',
    'Houston': '休斯顿',
    'Phoenix': '凤凰城',
    'Philadelphia': '费城',
    'San Antonio': '圣安东尼奥',
    'San Diego': '圣地亚哥',
    'Dallas': '达拉斯',
    'San Jose': '圣何塞',
    'Austin': '奥斯汀',
    'Jacksonville': '杰克逊维尔',
    'Fort Worth': '沃思堡',
    'Columbus': '哥伦布',
    'Charlotte': '夏洛特',
    'San Francisco': '旧金山',
    'Indianapolis': '印第安纳波利斯',
    'Seattle': '西雅图',
    'Denver': '丹佛',
    'Washington D.C.': '华盛顿特区',
    'Boston': '波士顿',
    'El Paso': '埃尔帕索',
    'Nashville': '纳什维尔',
    'Detroit': '底特律',
    'Oklahoma City': '俄克拉荷马城',
    'Portland': '波特兰',
    'Las Vegas': '拉斯维加斯',
    'Memphis': '孟菲斯',
    'Louisville': '路易斯维尔',
    'Baltimore': '巴尔的摩',
    'Milwaukee': '密尔沃基',
    'Albuquerque': '阿尔伯克基',
    'Tucson': '图森',
    'Fresno': '弗雷斯诺',
    'Mesa': '梅萨',
    'Sacramento': '萨克拉门托',
    'Atlanta': '亚特兰大',
    'Kansas City': '堪萨斯城',
    'Colorado Springs': '科罗拉多斯普林斯',
    'Miami': '迈阿密',
    'Raleigh': '罗利',
    'Omaha': '奥马哈',
    'Long Beach': '长滩',
    'Virginia Beach': '弗吉尼亚海滩',
    'Oakland': '奥克兰',
    'Minneapolis': '明尼阿波利斯',
    'Tampa': '坦帕',
    'Tulsa': '塔尔萨',
    'Arlington': '阿灵顿',
    'New Orleans': '新奥尔良',
    
    # 中国城市
    'Beijing': '北京',
    'Shanghai': '上海',
    'Guangzhou': '广州',
    'Shenzhen': '深圳',
    'Hangzhou': '杭州',
    'Nanjing': '南京',
    'Chengdu': '成都',
    'Wuhan': '武汉',
    'Xi\'an': '西安',
    'Chongqing': '重庆',
    'Tianjin': '天津',
    'Shenyang': '沈阳',
    'Dalian': '大连',
    'Qingdao': '青岛',
    'Jinan': '济南',
    'Harbin': '哈尔滨',
    'Changchun': '长春',
    'Kunming': '昆明',
    'Fuzhou': '福州',
    'Xiamen': '厦门',
    'Hefei': '合肥',
    'Zhengzhou': '郑州',
    'Taiyuan': '太原',
    'Shijiazhuang': '石家庄',
    'Urumqi': '乌鲁木齐',
    'Lhasa': '拉萨',
    'Hohhot': '呼和浩特',
    'Yinchuan': '银川',
    'Xining': '西宁',
    'Lanzhou': '兰州',
    'Nanning': '南宁',
    'Haikou': '海口',
    'Sanya': '三亚',
    
    # 其他重要城市
    'Tokyo': '东京',
    'Osaka': '大阪',
    'Kyoto': '京都',
    'Seoul': '首尔',
    'Busan': '釜山',
    'London': '伦敦',
    'Manchester': '曼彻斯特',
    'Birmingham': '伯明翰',
    'Berlin': '柏林',
    'Munich': '慕尼黑',
    'Hamburg': '汉堡',
    'Paris': '巴黎',
    'Lyon': '里昂',
    'Marseille': '马赛',
    'Moscow': '莫斯科',
    'Saint Petersburg': '圣彼得堡',
    'Toronto': '多伦多',
    'Vancouver': '温哥华',
    'Montreal': '蒙特利尔',
    'Sydney': '悉尼',
    'Melbourne': '墨尔本',
    'Brisbane': '布里斯班',
    'Perth': '珀斯',
    'Amsterdam': '阿姆斯特丹',
    'Rotterdam': '鹿特丹',
    'Zurich': '苏黎世',
    'Geneva': '日内瓦',
    'Stockholm': '斯德哥尔摩',
    'Oslo': '奥斯陆',
    'Copenhagen': '哥本哈根',
    'Helsinki': '赫尔辛基',
    'Rome': '罗马',
    'Milan': '米兰',
    'Naples': '那不勒斯',
    'Madrid': '马德里',
    'Barcelona': '巴塞罗那',
    'Warsaw': '华沙',
    'Istanbul': '伊斯坦布尔',
    'Ankara': '安卡拉',
    'Mexico City': '墨西哥城',
    'Buenos Aires': '布宜诺斯艾利斯',
    'São Paulo': '圣保罗',
    'Rio de Janeiro': '里约热内卢',
    'Bangkok': '曼谷',
    'Ho Chi Minh City': '胡志明市',
    'Kuala Lumpur': '吉隆坡',
    'Jakarta': '雅加达',
    'Manila': '马尼拉',
    'Yangon': '仰光',
    'Phnom Penh': '金边',
    'Vientiane': '万象',
    'Dhaka': '达卡',
    'Karachi': '卡拉奇',
    'Islamabad': '伊斯兰堡',
    'Colombo': '科伦坡',
    'Kathmandu': '加德满都',
    'Male': '马累',
    'Tehran': '德黑兰',
    'Baghdad': '巴格达',
    'Tel Aviv': '特拉维夫',
    'Jerusalem': '耶路撒冷',
    'Amman': '安曼',
    'Beirut': '贝鲁特',
    'Damascus': '大马士革',
    'Kuwait City': '科威特城',
    'Riyadh': '利雅得',
    'Dubai': '迪拜',
    'Abu Dhabi': '阿布扎比',
    'Doha': '多哈',
    'Manama': '麦纳麦',
    'Muscat': '马斯喀特',
    'Sanaa': '萨那',
    'Cairo': '开罗',
    'Tripoli': '的黎波里',
    'Tunis': '突尼斯',
    'Algiers': '阿尔及尔',
    'Rabat': '拉巴特',
    'Khartoum': '喀土穆',
    'Addis Ababa': '亚的斯亚贝巴',
    'Nairobi': '内罗毕',
    'Dar es Salaam': '达累斯萨拉姆',
    'Kampala': '坎帕拉',
    'Kigali': '基加利',
    'Cape Town': '开普敦',
    'Johannesburg': '约翰内斯堡',
    'Lagos': '拉各斯',
    'Accra': '阿克拉',
    'Auckland': '奥克兰',
    'Wellington': '惠灵顿',
    'Suva': '苏瓦',
    'Port Moresby': '莫尔兹比港',
    
    # 省份/州/地区
    'Guangdong': '广东',
    'Jiangsu': '江苏',
    'Zhejiang': '浙江',
    'Shandong': '山东',
    'Henan': '河南',
    'Sichuan': '四川',
    'Hubei': '湖北',
    'Hunan': '湖南',
    'Anhui': '安徽',
    'Hebei': '河北',
    'Jiangxi': '江西',
    'Shanxi': '山西',
    'Liaoning': '辽宁',
    'Fujian': '福建',
    'Shaanxi': '陕西',
    'Heilongjiang': '黑龙江',
    'Guangxi': '广西',
    'Yunnan': '云南',
    'Jilin': '吉林',
    'Guizhou': '贵州',
    'Xinjiang': '新疆',
    'Gansu': '甘肃',
    'Inner Mongolia': '内蒙古',
    'Ningxia': '宁夏',
    'Qinghai': '青海',
    'Tibet': '西藏',
    'Hainan': '海南',
    
    # 运营商和组织
    'China Telecom': '中国电信',
    'China Unicom': '中国联通',
    'China Mobile': '中国移动',
    'Alibaba Cloud': '阿里云',
    'Tencent Cloud': '腾讯云',
    'Amazon Technologies': '亚马逊技术',
    'Google LLC': '谷歌',
    'Microsoft Corporation': '微软公司',
    'Facebook': 'Facebook',
    'Apple': '苹果',
    'Cloudflare': 'Cloudflare',
    'Akamai Technologies': 'Akamai技术',
    'DigitalOcean': 'DigitalOcean',
    'Linode': 'Linode',
    'Vultr Holdings': 'Vultr',
    'Hetzner Online': 'Hetzner在线',
    'OVH SAS': 'OVH',
    'China Unicom Beijing': '中国联通北京',
    'China Telecom Shanghai': '中国电信上海',
    'China Mobile Guangdong': '中国移动广东',
    'Baidu': '百度',
    'NetEase': '网易',
    'Sina': '新浪',
    'Sohu': '搜狐',
    'JD.com': '京东',
    'Huawei Cloud': '华为云',
    'UCloud': 'UCloud',
    'QingCloud': '青云',
}

def translate_to_chinese(text):
    """将英文文本翻译成中文"""
    if not text or text == '未知':
        return text
    
    # 直接查找完整匹配
    if text in TRANSLATION_MAP:
        return TRANSLATION_MAP[text]
    
    # 尝试部分匹配（用于处理复合词汇）
    result = text
    for en_text, cn_text in TRANSLATION_MAP.items():
        if en_text.lower() in text.lower():
            result = result.replace(en_text, cn_text)
    
    return result

# 获取域名的IPv4和IPv6地址
def get_domain_ips(domain):
    """获取域名的IPv4和IPv6地址"""
    ipv4_addresses = []
    ipv6_addresses = []
    
    try:
        # 获取IPv4地址
        try:
            ipv4_info = socket.getaddrinfo(domain, None, socket.AF_INET)
            ipv4_addresses = list(set([info[4][0] for info in ipv4_info]))
        except socket.gaierror:
            pass
        
        # 获取IPv6地址
        try:
            ipv6_info = socket.getaddrinfo(domain, None, socket.AF_INET6)
            ipv6_addresses = list(set([info[4][0] for info in ipv6_info]))
        except socket.gaierror:
            pass
            
    except Exception:
        pass
    
    return ipv4_addresses, ipv6_addresses

# 检查是否为IP地址
def is_ip_address(address):
    """检查字符串是否为有效的IP地址（IPv4或IPv6）"""
    try:
        socket.inet_pton(socket.AF_INET, address)
        return True, "IPv4"
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, address)
            return True, "IPv6"
        except socket.error:
            return False, None

# 注册插件的装饰器
@register(
    "astrbot_plugin_balance",
    "Chris", 
    "支持硅基流动、OpenAI、DeepSeek余额查询及IP查询功能", 
    "v1.1.0", 
    "https://github.com/Chris95743/astrbot_plugin_balance"
)
class PluginBalanceIP(Star):
    
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.context = context  # 保存context对象，供后续方法使用
        # 如果没有提供config，尝试手动创建它
        self.config = config or AstrBotConfig()

    # 提取API密钥或IP地址的公共方法
    def _get_command_argument(self, event: AstrMessageEvent):
        messages = event.get_messages()
        if not messages:
            return None

        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 @ 消息
            message_text = message.text
            break

        if not message_text:
            return None

        parts = message_text.split()
        if len(parts) < 2:
            return None
        return parts[1].strip()

    # 查询硅基余额命令
    @filter.command("硅基余额")
    async def siliconflow_balance(self, event: AstrMessageEvent):
        """查询硅基流动余额"""
        api_key = self._get_command_argument(event)
        if not api_key:
            yield event.plain_result("请输入API密钥，格式为：硅基余额 <你的API密钥>")
            return

        result = await query_siliconflow_balance(api_key)
        yield event.plain_result(result)

    # 查询GPT余额命令
    @filter.command("GPT余额")
    async def openai_balance(self, event: AstrMessageEvent):
        """查询OpenAI余额"""
        api_key = self._get_command_argument(event)
        if not api_key:
            yield event.plain_result("请输入API密钥，格式为：GPT余额 <你的API密钥>")
            return

        result = await query_openai_balance(api_key)
        yield event.plain_result(result)

    # 查询DS余额命令
    @filter.command("DS余额")
    async def ds_balance(self, event: AstrMessageEvent):
        """查询DeepSeek余额"""
        api_key = self._get_command_argument(event)
        if not api_key:
            yield event.plain_result("请输入API密钥，格式为：DS余额 <你的API密钥>")
            return

        result = await query_ds_balance(api_key)
        yield event.plain_result(result)

    # 查询IP命令
    @filter.command("查询IP")
    async def query_ip_info(self, event: AstrMessageEvent):
        """查询指定IP地址或域名的归属地和运营商"""
        target = self._get_command_argument(event)
        if not target:
            yield event.plain_result("请输入IP地址或域名，格式为：查询IP <IP地址/域名（不用加https:/）>")
            return

        try:
            # 检查输入是否为IP地址
            is_ip, ip_type = is_ip_address(target)
            
            result_parts = []
            
            if is_ip:
                # 直接查询IP地址
                result_parts.append(f"🔍 查询目标: {target} ({ip_type}地址)")
                ip_info = await self._query_single_ip(target)
                result_parts.append(ip_info)
            else:
                # 域名解析
                result_parts.append(f"🔍 查询目标: {target} (域名)")
                
                # 获取域名的IP地址
                ipv4_addresses, ipv6_addresses = get_domain_ips(target)
                
                if not ipv4_addresses and not ipv6_addresses:
                    yield event.plain_result(f"无法解析域名 {target}，请检查域名是否有效。")
                    return
                
                # 显示解析的IP地址
                if ipv4_addresses:
                    result_parts.append(f"IPv4地址: {', '.join(ipv4_addresses)}")
                if ipv6_addresses:
                    result_parts.append(f"IPv6地址: {', '.join(ipv6_addresses[:3])}{'...' if len(ipv6_addresses) > 3 else ''}")
                
                # 查询第一个IPv4地址的详细信息（ip-api.com主要支持IPv4）  
                if ipv4_addresses:
                    result_parts.append(f"详细信息 (基于IPv4: {ipv4_addresses[0]}):")
                    ip_info = await self._query_single_ip(ipv4_addresses[0])
                    result_parts.append(ip_info)
                else:
                    result_parts.append(f"该域名仅有IPv6地址，当前API服务暂不支持IPv6地理信息查询")

            final_result = '\n'.join(result_parts)
            yield event.plain_result(final_result)

        except Exception as e:
            yield event.plain_result(f"查询IP信息时发生错误: {str(e)}")

    async def _query_single_ip(self, ip_address):
        """查询单个IP地址的详细信息"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{IP_API_URL}{ip_address}") as response:
                    data = await response.json()

            # 检查API响应
            if data['status'] == 'fail':
                return f"无法查询IP地址 {ip_address} 的详细信息: {data.get('message', '未知错误')}"

            # 提取信息并翻译
            country = translate_to_chinese(data.get('country', '未知'))
            region = translate_to_chinese(data.get('regionName', '未知'))
            city = translate_to_chinese(data.get('city', '未知'))
            zip_code = data.get('zip', '未知')
            isp = translate_to_chinese(data.get('isp', '未知'))
            org = translate_to_chinese(data.get('org', '未知'))
            asn = data.get('as', '未知')
            lat = data.get('lat', '未知')
            lon = data.get('lon', '未知')
            timezone = data.get('timezone', '未知')

            # 返回查询结果（中文）
            result = (
                f"归属地: {country} {region} {city}\n"
                f"邮政编码: {zip_code}\n"
                f"运营商: {isp}\n"
                f"组织: {org}\n"
                f"ASN: {asn}\n"
                f"时区: {timezone}\n"
                f"坐标: {lat}, {lon}"
            )
            return result

        except aiohttp.ClientError as e:
            return f"查询IP详细信息时发生网络错误: {str(e)}"

    # Ping域名命令
    @filter.command("ping")
    async def ping_domain(self, event: AstrMessageEvent):
        """Ping指定域名或IP地址"""
        target = self._get_command_argument(event)
        if not target:
            yield event.plain_result("请输入要ping的域名或IP地址，格式为：ping <域名/IP地址>")
            return

        yield event.plain_result(f"正在ping {target}，请稍候...")
        result = await ping_host(target)
        yield event.plain_result(result)

    # 查询帮助命令
    @filter.command("查询帮助")
    async def query_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        help_text = (
            "使用方法：\n"
            "/硅基余额 <API密钥>: 查询硅基流动平台的余额\n"
            "/DS余额 <API密钥>: 查询DeepSeek平台的余额\n"
            "/GPT余额 <API密钥>: 查询OpenAI平台的余额\n"
            "/查询IP <IP地址/域名（不用加https:/）>: 查询指定IP地址的归属地和运营商信息\n"
            "/ping <域名/IP地址>: 测试指定域名或IP的连通性和延迟\n"
            "/查询帮助: 显示命令的帮助信息\n"
        )
        yield event.plain_result(help_text)
