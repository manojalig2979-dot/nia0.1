import json
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

class SmartHomeManager:
    """Manages connections and commands to various smart home devices natively."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = {}
        self.devices = {}
        self.reload_config()
        
    def reload_config(self):
        self.config = self._load_config()
        self.devices = self.config.get("smart_home_devices", {})
        
    def _load_config(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        return {}

    def control_device(self, device_name: str, action: str) -> str:
        """
        Main entry point to turn a device on or off.
        action can be 'on' or 'off'.
        """
        device_name = device_name.lower().strip()
        action = action.lower().strip()
        
        if action not in ["on", "off"]:
            return f"Invalid action '{action}'. Use 'on' or 'off'."
            
        # Try to find a matching device
        matched_device = None
        for name, details in self.devices.items():
            if device_name in name.lower():
                matched_device = details
                break
                
        if not matched_device:
            return f"Device '{device_name}' not found in configuration."
            
        brand = matched_device.get("brand", "").lower()
        
        try:
            if brand == "kasa" or brand == "tplink":
                return self._control_kasa(matched_device, action)
            elif brand == "tuya" or brand == "wipro" or brand == "syska":
                return self._control_tuya(matched_device, action)
            elif brand == "hue" or brand == "philips":
                return self._control_hue(matched_device, action)
            elif brand == "samsung" or brand == "smartthings":
                return self._control_samsung(matched_device, action)
            else:
                return f"Unsupported device brand '{brand}' for {device_name}."
        except Exception as e:
            logger.error(f"Error controlling {device_name}: {e}")
            return f"Failed to control {device_name}: {e}"

    def _control_kasa(self, device: dict, action: str) -> str:
        ip = device.get("ip")
        if not ip:
            return "IP address missing for Kasa device."
        
        try:
            import kasa
            # Using asyncio to run the async kasa methods synchronously for the orchestrator
            async def run_kasa():
                plug = kasa.SmartPlug(ip)
                await plug.update()
                if action == "on":
                    await plug.turn_on()
                else:
                    await plug.turn_off()
            
            asyncio.run(run_kasa())
            return f"Successfully turned {action} Kasa device at {ip}."
        except ImportError:
            return "Missing python-kasa dependency. Run: pip install python-kasa"
        except Exception as e:
            return f"Kasa Error: {e}"

    def _control_tuya(self, device: dict, action: str) -> str:
        device_id = device.get("device_id")
        ip = device.get("ip")
        local_key = device.get("local_key")
        version = device.get("version", 3.3)
        
        if not all([device_id, ip, local_key]):
            return "Missing device_id, ip, or local_key for Tuya device."
            
        try:
            import tinytuya
            d = tinytuya.OutletDevice(device_id, ip, local_key)
            d.set_version(version)
            if action == "on":
                d.turn_on()
            else:
                d.turn_off()
            return f"Successfully turned {action} Tuya device."
        except ImportError:
            return "Missing tinytuya dependency. Run: pip install tinytuya"
        except Exception as e:
            return f"Tuya Error: {e}"

    def _control_hue(self, device: dict, action: str) -> str:
        bridge_ip = self.config.get("smart_home", {}).get("hue_bridge_ip")
        light_name = device.get("name")
        
        if not bridge_ip:
            return "Hue Bridge IP not configured in smart_home.hue_bridge_ip"
            
        try:
            from phue import Bridge
            b = Bridge(bridge_ip)
            # b.connect() # Needs to be run once with button press
            if action == "on":
                b.set_light(light_name, 'on', True)
            else:
                b.set_light(light_name, 'on', False)
            return f"Successfully turned {action} Hue light '{light_name}'."
        except ImportError:
            return "Missing phue dependency. Run: pip install phue"
        except Exception as e:
            return f"Hue Error: {e} (Have you pressed the bridge button?)"

    def _control_samsung(self, device: dict, action: str) -> str:
        token = self.config.get("smart_home", {}).get("smartthings_token")
        device_id = device.get("device_id")
        
        if not token or not device_id:
            return "SmartThings token or device_id missing."
            
        try:
            import pysmartthings
            import aiohttp
            
            async def run_samsung():
                async with aiohttp.ClientSession() as session:
                    api = pysmartthings.SmartThings(session, token)
                    dev = await api.device(device_id)
                    if action == "on":
                        await dev.switch_on()
                    else:
                        await dev.switch_off()
            
            asyncio.run(run_samsung())
            return f"Successfully turned {action} Samsung device."
        except ImportError:
            return "Missing pysmartthings dependency. Run: pip install pysmartthings aiohttp"
        except Exception as e:
            return f"SmartThings Error: {e}"
