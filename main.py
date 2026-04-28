# main.py
import httpx
import asyncio
from typing import Optional, Dict, Any
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register("mslx_controller", "你的名字", "通过API控制MSLX的服务器和隧道", "1.0.2")
class MSLXAPIController(Star):
    def __init__(self, context: Context, config: Optional[Dict[str, Any]] = None):
        super().__init__(context)
        # 获取插件配置（用户通过 WebUI 填写的内容）
        self.plugin_config = config or {}
        mslx_config = self.plugin_config.get("mslx_api", {})
        self.api_root = mslx_config.get("api_root", "http://localhost:1027")
        api_key = mslx_config.get("api_token", "")
        if not api_key:
            logger.warning("[MSLX控制器] API Token 未配置，部分功能将不可用！")
        # 根据 OpenAPI 规范，认证方式为 x-api-key Header
        self.headers = {"x-api-key": api_key}
        logger.info(f"[MSLX控制器] 已加载配置，API地址: {self.api_root}")

    def _check_admin(self, event: AstrMessageEvent) -> bool:
        """检查用户是否为管理员"""
        return event.role == "admin"

    # ==================== 帮助命令 ====================
    @filter.command("mslx help")
    async def mslx_help(self, event: AstrMessageEvent):
        '''显示所有可用命令 (用法: /mslx help)'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        help_text = (
            "**📖 MSLX 控制器 - 可用命令列表**\n\n"
            "**🖥️ 服务器实例**\n"
            "  `/mslx ser list` - 查看所有服务器实例\n"
            "  `/mslx ser info <ID>` - 查看服务器实例详情\n"
            "  `/mslx ser start <ID>` - 启动服务器\n"
            "  `/mslx ser stop <ID>` - 停止服务器\n"
            "  `/mslx ser restart <ID>` - 重启服务器\n"
            "  `/mslx player <ID>` - 查看在线玩家\n\n"
            "**🔗 FRP 隧道**\n"
            "  `/mslx tun list` - 查看所有隧道\n"
            "  `/mslx tun info <ID>` - 查看隧道详情\n"
            "  `/mslx tun start <ID>` - 启动隧道\n"
            "  `/mslx tun stop <ID>` - 停止隧道\n"
            "  `/mslx tun restart <ID>` - 重启隧道\n\n"
            "💡 提示：所有命令仅限管理员使用。"
        )
        yield event.plain_result(help_text)

    # ==================== 服务器实例控制 ====================
    @filter.command("mslx ser list")
    async def list_servers(self, event: AstrMessageEvent):
        '''获取MSLX服务器实例列表 (用法: /mslx ser list)'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_root}/api/instance/list", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    instances = data.get("data", [])
                    if not instances:
                        reply = "📭 当前没有配置任何服务器实例。"
                    else:
                        msg_lines = ["**📋 当前服务器实例列表:**"]
                        for idx, inst in enumerate(instances, 1):
                            inst_id = inst.get('id')
                            name = inst.get('name', '未命名')
                            status = "🟢 运行中" if inst.get('status') else "🔴 已停止"
                            core = inst.get('core', '未知核心')
                            msg_lines.append(f"{idx}. [{inst_id}] {name} - {status} (核心: {core})")
                        reply = "\n".join(msg_lines)
                else:
                    reply = f"❌ API返回错误: {data.get('message', '未知错误')}"
                yield event.plain_result(reply)
            else:
                yield event.plain_result(f"❌ 获取服务器列表失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 请求发生错误: {e}")

    @filter.command("mslx ser info")
    async def server_info(self, event: AstrMessageEvent, instance_id: str):
        '''获取服务器实例详细信息 (用法: /mslx ser info <实例ID>)'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        if not instance_id.isdigit():
            yield event.plain_result("❌ 实例ID必须是数字。请使用 `/mslx ser list` 查看ID。")
            return
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_root}/api/instance/info",
                    params={"id": int(instance_id)},
                    headers=self.headers
                )
            if response.status_code == 200:
                resp_data = response.json()
                if resp_data.get("code") == 200:
                    inst = resp_data.get("data", {})
                    if not inst:
                        yield event.plain_result(f"❌ 未找到实例 ID `{instance_id}` 的信息。")
                        return
                    name = inst.get('name', '未命名')
                    status = "🟢 运行中" if inst.get('status') else "🔴 已停止"
                    core = inst.get('core', '未知')
                    msg_lines = [
                        f"**🖥️ 服务器实例 [{instance_id}] {name}**",
                        f"状态: {status}",
                        f"核心: {core}",
                    ]
                    # 可选字段
                    if 'node' in inst:
                        msg_lines.append(f"节点: {inst.get('node', '未知')}")
                    if 'createTime' in inst:
                        msg_lines.append(f"创建时间: {inst.get('createTime', '未知')}")
                    if 'updateTime' in inst:
                        msg_lines.append(f"更新时间: {inst.get('updateTime', '未知')}")
                    reply = "\n".join(msg_lines)
                    yield event.plain_result(reply)
                else:
                    yield event.plain_result(f"❌ API返回错误: {resp_data.get('message', '未知错误')}")
            else:
                yield event.plain_result(f"❌ 获取服务器详情失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 请求发生错误: {e}")

    @filter.command("mslx ser start")
    async def start_server(self, event: AstrMessageEvent, instance_id: str):
        '''启动服务器实例 (用法: /mslx ser start <实例ID>)'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        if not instance_id.isdigit():
            yield event.plain_result("❌ 实例ID必须是数字。请使用 `/mslx ser list` 查看ID。")
            return
        payload = {"id": int(instance_id), "action": "start"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_root}/api/instance/action", json=payload, headers=self.headers)
            if response.status_code == 200:
                resp_data = response.json()
                code = resp_data.get("code")
                message = resp_data.get("message", "")
                if code == 200:
                    yield event.plain_result(f"✅ 服务器实例 `{instance_id}` 启动指令已发送。\n{message}")
                else:
                    yield event.plain_result(f"❌ 启动失败 (code={code}): {message}")
            else:
                yield event.plain_result(f"❌ API请求失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 请求发生错误: {e}")

    @filter.command("mslx ser stop")
    async def stop_server(self, event: AstrMessageEvent, instance_id: str):
        '''停止服务器实例 (用法: /mslx ser stop <实例ID>)'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        if not instance_id.isdigit():
            yield event.plain_result("❌ 实例ID必须是数字。")
            return
        payload = {"id": int(instance_id), "action": "stop"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_root}/api/instance/action", json=payload, headers=self.headers)
            if response.status_code == 200:
                resp_data = response.json()
                code = resp_data.get("code")
                message = resp_data.get("message", "")
                if code == 200:
                    yield event.plain_result(f"✅ 服务器实例 `{instance_id}` 停止指令已发送。\n{message}")
                else:
                    yield event.plain_result(f"❌ 停止失败 (code={code}): {message}")
            else:
                yield event.plain_result(f"❌ API请求失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 请求发生错误: {e}")

    @filter.command("mslx ser restart")
    async def restart_server(self, event: AstrMessageEvent, instance_id: str):
        '''重启服务器实例 (用法: /mslx ser restart <实例ID>) - 先停止，等待20秒后启动'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        if not instance_id.isdigit():
            yield event.plain_result("❌ 实例ID必须是数字。请使用 `/mslx ser list` 查看ID。")
            return
        yield event.plain_result(f"🔄 正在重启服务器实例 `{instance_id}`，请稍候...")
        try:
            async with httpx.AsyncClient() as client:
                # 1. 先停止
                stop_payload = {"id": int(instance_id), "action": "stop"}
                stop_resp = await client.post(f"{self.api_root}/api/instance/action", json=stop_payload, headers=self.headers)
                if stop_resp.status_code != 200:
                    yield event.plain_result(f"❌ 停止服务器实例失败 (HTTP {stop_resp.status_code})，无法继续重启。")
                    return
                stop_data = stop_resp.json()
                if stop_data.get("code") != 200:
                    yield event.plain_result(f"❌ 停止失败 ({stop_data.get('message', '未知错误')})，无法继续重启。")
                    return
                # 等待20秒，确保进程完全退出
                await asyncio.sleep(20)
                # 2. 再启动
                start_payload = {"id": int(instance_id), "action": "start"}
                start_resp = await client.post(f"{self.api_root}/api/instance/action", json=start_payload, headers=self.headers)
                if start_resp.status_code == 200:
                    start_data = start_resp.json()
                    if start_data.get("code") == 200:
                        yield event.plain_result(f"✅ 服务器实例 `{instance_id}` 重启完成。\n{start_data.get('message', '启动成功')}")
                    else:
                        yield event.plain_result(f"❌ 停止成功但启动失败: {start_data.get('message', '未知错误')}")
                else:
                    yield event.plain_result(f"❌ 停止成功但启动失败 (HTTP {start_resp.status_code})，请手动启动。")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 重启服务器时发生错误: {e}")

    @filter.command("mslx player")
    async def online_players(self, event: AstrMessageEvent, instance_id: str):
        '''获取服务器在线玩家列表 (用法: /mslx player <实例ID>)'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        if not instance_id.isdigit():
            yield event.plain_result("❌ 实例ID必须是数字。请使用 `/mslx ser list` 查看ID。")
            return
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_root}/api/instance/players/online/{int(instance_id)}",
                    headers=self.headers
                )
            if response.status_code == 200:
                resp_data = response.json()
                if resp_data.get("code") == 200:
                    players = resp_data.get("data", [])
                    if not players:
                        yield event.plain_result(f"📭 服务器实例 `{instance_id}` 当前没有在线玩家。")
                    else:
                        player_list = "\n".join([f"  👤 {p}" for p in players])
                        yield event.plain_result(
                            f"**👥 服务器实例 `{instance_id}` 在线玩家 ({len(players)}人)**\n{player_list}"
                        )
                else:
                    yield event.plain_result(f"❌ API返回错误: {resp_data.get('message', '未知错误')}")
            else:
                yield event.plain_result(f"❌ 获取在线玩家失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 请求发生错误: {e}")

    # ==================== FRP 隧道控制 ====================
    @filter.command("mslx tun list")
    async def list_tunnels(self, event: AstrMessageEvent):
        '''获取MSLX隧道列表 (用法: /mslx tun list)'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_root}/api/frp/list", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    tunnels = data.get("data", [])
                    if not tunnels:
                        reply = "📭 当前没有配置任何隧道。"
                    else:
                        msg_lines = ["**🔗 当前隧道列表:**"]
                        for idx, tun in enumerate(tunnels, 1):
                            tun_id = tun.get('id')
                            name = tun.get('name', '未命名')
                            service = tun.get('service', '未知')
                            config_type = tun.get('configType', '')
                            status = "🟢 运行中" if tun.get('status') else "🔴 已停止"
                            msg_lines.append(f"{idx}. [{tun_id}] {name} - {status} (服务: {service}, 配置: {config_type})")
                        reply = "\n".join(msg_lines)
                else:
                    reply = f"❌ API返回错误: {data.get('message', '未知错误')}"
                yield event.plain_result(reply)
            else:
                yield event.plain_result(f"❌ 获取隧道列表失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 请求发生错误: {e}")

    @filter.command("mslx tun info")
    async def tunnel_info(self, event: AstrMessageEvent, tunnel_id: str):
        '''获取隧道详细信息 (用法: /mslx tun info <隧道ID>)'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        if not tunnel_id.isdigit():
            yield event.plain_result("❌ 隧道ID必须是数字。请使用 `/mslx tun list` 查看ID。")
            return
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_root}/api/frp/info",
                    params={"id": int(tunnel_id)},
                    headers=self.headers
                )
            if response.status_code == 200:
                resp_data = response.json()
                if resp_data.get("code") != 200:
                    yield event.plain_result(f"❌ API返回错误: {resp_data.get('message', '未知错误')}")
                    return
                api_data = resp_data.get("data", {})
                is_running = api_data.get("isRunning", False)
                proxies = api_data.get("proxies", [])
                status_text = "🟢 运行中" if is_running else "🔴 已停止"
                msg_lines = [f"**隧道 ID {tunnel_id} 详情** - {status_text}"]
                if proxies:
                    msg_lines.append("**代理列表:**")
                    for proxy in proxies:
                        proxy_name = proxy.get("ProxyName", "未知")
                        p_type = proxy.get("Type", "未知")
                        local_addr = proxy.get("LocalAddress", "未知")
                        remote_main = proxy.get("RemoteAddressMain", "未知")
                        remote_backup = proxy.get("RemoteAddressBackup", "无")
                        msg_lines.append(
                            f"- {proxy_name} [{p_type}]: 本地 {local_addr} → 远程 {remote_main} (备用 {remote_backup})"
                        )
                else:
                    msg_lines.append("未解析到代理详情（可能配置为INI/CMD格式）。")
                reply = "\n".join(msg_lines)
                yield event.plain_result(reply)
            else:
                yield event.plain_result(f"❌ 获取隧道详情失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 请求发生错误: {e}")

    @filter.command("mslx tun start")
    async def start_tunnel(self, event: AstrMessageEvent, tunnel_id: str):
        '''启动隧道 (用法: /mslx tun start <隧道ID>)'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        if not tunnel_id.isdigit():
            yield event.plain_result("❌ 隧道ID必须是数字。")
            return
        payload = {"action": "start", "id": int(tunnel_id)}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_root}/api/frp/action", json=payload, headers=self.headers)
            if response.status_code == 200:
                resp_data = response.json()
                message = resp_data.get("message", "操作成功")
                yield event.plain_result(f"✅ 隧道 `{tunnel_id}` 启动指令已发送。\n{message}")
            else:
                yield event.plain_result(f"❌ 启动隧道失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 请求发生错误: {e}")

    @filter.command("mslx tun stop")
    async def stop_tunnel(self, event: AstrMessageEvent, tunnel_id: str):
        '''停止隧道 (用法: /mslx tun stop <隧道ID>)'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        if not tunnel_id.isdigit():
            yield event.plain_result("❌ 隧道ID必须是数字。")
            return
        payload = {"action": "stop", "id": int(tunnel_id)}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_root}/api/frp/action", json=payload, headers=self.headers)
            if response.status_code == 200:
                resp_data = response.json()
                message = resp_data.get("message", "操作成功")
                yield event.plain_result(f"✅ 隧道 `{tunnel_id}` 停止指令已发送。\n{message}")
            else:
                yield event.plain_result(f"❌ 停止隧道失败，HTTP状态码: {response.status_code}")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 请求发生错误: {e}")

    @filter.command("mslx tun restart")
    async def restart_tunnel(self, event: AstrMessageEvent, tunnel_id: str):
        '''重启隧道 (用法: /mslx tun restart <隧道ID>) - 先停止再启动，中间等待1秒'''
        if not self._check_admin(event):
            yield event.plain_result("❌ 权限不足：仅管理员可使用此命令。")
            return
        if not tunnel_id.isdigit():
            yield event.plain_result("❌ 隧道ID必须是数字。")
            return
        yield event.plain_result(f"🔄 正在重启隧道 `{tunnel_id}`，请稍候...")
        try:
            async with httpx.AsyncClient() as client:
                # 1. 停止
                stop_payload = {"action": "stop", "id": int(tunnel_id)}
                stop_resp = await client.post(f"{self.api_root}/api/frp/action", json=stop_payload, headers=self.headers)
                if stop_resp.status_code != 200:
                    yield event.plain_result(f"❌ 停止隧道失败 (HTTP {stop_resp.status_code})，无法继续重启。")
                    return
                # 等待1秒，确保进程完全退出
                await asyncio.sleep(1)
                # 2. 启动
                start_payload = {"action": "start", "id": int(tunnel_id)}
                start_resp = await client.post(f"{self.api_root}/api/frp/action", json=start_payload, headers=self.headers)
                if start_resp.status_code == 200:
                    start_data = start_resp.json()
                    start_msg = start_data.get("message", "启动成功")
                    yield event.plain_result(f"✅ 隧道 `{tunnel_id}` 重启完成。\n{start_msg}")
                else:
                    yield event.plain_result(f"❌ 停止成功但启动失败 (HTTP {start_resp.status_code})，请手动启动。")
        except Exception as e:
            logger.error(e)
            yield event.plain_result(f"❌ 重启隧道时发生错误: {e}")
