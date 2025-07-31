import aiohttp
import asyncio
import platform
import subprocess
import re
import socket
import time
from datetime import datetime
from astrbot.api.message_components import At
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import AstrBotConfig
from astrbot.api.star import Context, Star, register

# API配置常量
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/user/info"
OPENAI_API_BASE_URL = "https://api.openai.com"
DEEPSEEK_API_URL = "https://api.deepseek.com/user/balance"
IP_API_URL = "http://ip-api.com/json/"

# 网络测试配置
PING_TIMEOUT = 30.0
TCP_TIMEOUT = 3
TEST_PORTS = [22, 23, 80, 443, 5000, 6099, 6185]

async def query_siliconflow_balance(api_key):
    """查询硅基流动平台余额信息"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(SILICONFLOW_API_URL, headers=headers) as response:
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

async def query_openai_balance(api_key):
    """查询OpenAI平台余额信息"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        today = datetime.today().strftime('%Y-%m-%d')

        subscription_url = f"{OPENAI_API_BASE_URL}/v1/dashboard/billing/subscription"
        async with aiohttp.ClientSession() as session:
            async with session.get(subscription_url, headers=headers) as subscription_response:
                subscription_response.raise_for_status()
                subscription_data = await subscription_response.json()

            usage_url = f"{OPENAI_API_BASE_URL}/v1/dashboard/billing/usage?start_date={today}&end_date={today}"
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

async def query_ds_balance(api_key):
    """查询DeepSeek平台余额信息"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(DEEPSEEK_API_URL, headers=headers) as response:
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

async def ping_host(host, count=4):
    """使用系统ping命令测试主机连通性和延迟"""
    try:
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
                
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=PING_TIMEOUT)
                
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
        return f"Ping超时: {host} ({PING_TIMEOUT}秒无响应)"
    except Exception as e:
        return await fallback_connectivity_test(host)

async def fallback_connectivity_test(host, timeout=TCP_TIMEOUT):
    """备用连通性测试（当ping命令不可用时）"""
    result = f"连通性测试 - {host}:\n"
    result += "⚠️ 系统ping命令不可用，使用TCP连接测试\n\n"
    
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
        for port in TEST_PORTS:
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
        result += f"测试端口: {successful_connections}/{len(TEST_PORTS)}个可连接\n"
        
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

async def port_connectivity_test(host, timeout=TCP_TIMEOUT):
    """端口连通性测试"""
    successful_connections = 0
    total_time = 0
    connection_results = []
    
    try:
        # 测试指定端口的连通性
        for port in TEST_PORTS:
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
        result += f"测试端口: {successful_connections}/{len(TEST_PORTS)}个可连接\n"
        
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
        # 英文格式: time=165ms 或 time=8.24 ms (注意空格)
        # 中文格式: 时间=165ms 或 ʱ=165ms (编码问题)
        if 'time=' in line.lower() or '时间=' in line or 'ʱ=' in line:
            # 使用正则表达式提取数字，支持带空格的格式
            time_match = re.search(r'(?:time=|时间=|ʱ=)(\d+(?:\.\d+)?)\s*ms', line, re.IGNORECASE)
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

# 精简的中英文对照表（备用翻译，API已支持直接中文返回）
TRANSLATION_MAP = {
    # 常见国家/地区
    'United States': '美国',
    'China': '中国', 
    'Hong Kong': '香港',
    'Taiwan': '台湾',
    'Japan': '日本',
    'South Korea': '韩国',
    'United Kingdom': '英国',
    'Singapore': '新加坡',
    
    # 常见运营商
    'China Telecom': '中国电信',
    'China Unicom': '中国联通', 
    'China Mobile': '中国移动',
    'Alibaba Cloud': '阿里云',
    'Tencent Cloud': '腾讯云',
    'Google LLC': '谷歌',
    'Microsoft Corporation': '微软公司',
    'Amazon Technologies': '亚马逊技术',
    'Cloudflare': 'Cloudflare',
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
            # 构建带中文语言参数和完整字段的URL
            # 请求所有可用字段以获取最完整的信息
            fields = "status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,mobile,proxy,hosting,query"
            url = f"{IP_API_URL}{ip_address}?lang=zh-CN&fields={fields}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            # 检查API响应
            if data['status'] == 'fail':
                return f"无法查询IP地址 {ip_address} 的详细信息: {data.get('message', '未知错误')}"

            # 提取信息，优先使用API返回的中文，必要时进行翻译
            country = data.get('country', '未知')
            country_code = data.get('countryCode', '未知')
            region = data.get('regionName', '未知') 
            region_code = data.get('region', '未知')
            city = data.get('city', '未知')
            zip_code = data.get('zip', '未知')
            isp = data.get('isp', '未知')
            org = data.get('org', '未知')
            asn = data.get('as', '未知')
            asn_name = data.get('asname', '未知')
            lat = data.get('lat', '未知')
            lon = data.get('lon', '未知')
            timezone = data.get('timezone', '未知')
            is_mobile = data.get('mobile', False)
            is_proxy = data.get('proxy', False)
            is_hosting = data.get('hosting', False)

            # 如果API返回的还是英文，则使用翻译表进行翻译
            country = translate_to_chinese(country) if country != '未知' else country
            region = translate_to_chinese(region) if region != '未知' else region
            city = translate_to_chinese(city) if city != '未知' else city
            isp = translate_to_chinese(isp) if isp != '未知' else isp
            org = translate_to_chinese(org) if org != '未知' else org

            # 构建更详细的查询结果
            result = f"🌍 地理位置:\n"
            result += f"  国家: {country}"
            if country_code != '未知':
                result += f" ({country_code})"
            result += f"\n  省/州: {region}"
            if region_code != '未知':
                result += f" ({region_code})"
            result += f"\n  城市: {city}\n"
            result += f"  邮政编码: {zip_code}\n"
            result += f"  坐标: {lat}, {lon}\n"
            result += f"  时区: {timezone}\n\n"
            
            result += f"🏢 网络信息:\n"
            result += f"  ISP运营商: {isp}\n"
            result += f"  组织机构: {org}\n"
            if asn != '未知':
                result += f"  ASN编号: {asn}\n"
            if asn_name != '未知' and asn_name != asn:
                result += f"  ASN名称: {asn_name}\n"
            
            # 特殊属性标识
            special_attrs = []
            if is_mobile:
                special_attrs.append("📱 移动网络")
            if is_proxy:
                special_attrs.append("🔒 代理/VPN")
            if is_hosting:
                special_attrs.append("🖥️ 托管服务")
            
            if special_attrs:
                result += f"\n🏷️ 特殊属性:\n"
                for attr in special_attrs:
                    result += f"  {attr}\n"
            
            return result.rstrip()

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
