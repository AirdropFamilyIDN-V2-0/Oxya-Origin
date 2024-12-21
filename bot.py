import requests
import json
import time
import os
from datetime import datetime
from colorama import init, Fore

init(autoreset=True)

class OxyaOriginBot:
    def __init__(self, auth_token):
        self.base_url = "https://api.oxyaorigin.com/api/hunter"
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Origin": "https://quest.oxyaorigin.com",
            "Referer": "https://quest.oxyaorigin.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.6",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Herond";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-Gpc": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        self.user_id = self._get_user_id()

    def _get_user_id(self):
        try:
            response = requests.post(
                f"{self.base_url}/user/create",
                headers=self.headers,
                json={"isLogin": False}
            )
            if response.status_code == 200:
                data = response.json()
                return data['user']['userId']
            return None
        except Exception as e:
            print(f"{Fore.RED}[{self.get_timestamp()}] Error getting user ID: {e}")
            return None

    def get_missions(self):
        try:
            response = requests.get(
                f"{self.base_url}/missions/all",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"{Fore.RED}[{self.get_timestamp()}] Error getting missions: {e}")
            return None

    def get_mission_status(self):
        try:
            print(f"{Fore.CYAN}[{self.get_timestamp()}] Trying to get mission status for user ID: {self.user_id}\n")
            url = f"{self.base_url}/missions/status/all?userId={self.user_id}"
            
            response = requests.get(
                url,
                headers=self.headers
            )
            
            if response.status_code == 200:
                if response.text == "[]":
                    print(f"{Fore.YELLOW}[{self.get_timestamp()}] No completed missions")
                    return []
                return response.json()
            else:
                print(f"{Fore.RED}[{self.get_timestamp()}] Error response: {response.text}")
                return None
        except Exception as e:
            print(f"{Fore.RED}[{self.get_timestamp()}] Error getting mission status: {str(e)}")
            return None

    def complete_mission(self, mission):
        try:
            payload = {
                "ruleId": mission["id"]
            }
            
            response = requests.post(
                f"{self.base_url}/missions/completeRule",
                headers=self.headers,
                json=payload
            )
            
            response_data = {}
            if response.text:
                try:
                    response_data = response.json()
                except:
                    pass
                
            if response.status_code == 200:
                print(f"{Fore.GREEN}[{self.get_timestamp()}] Successfully completed mission: {mission['name']}")
                return {"success": True, "status": "completed"}
            elif response.status_code == 400 and response_data.get("message") == "You have already been rewarded":
                print(f"{Fore.YELLOW}[{self.get_timestamp()}] Mission completed: {mission['name']}")
                return {"success": True, "status": "already_rewarded"}
            else:
                print(f"{Fore.RED}[{self.get_timestamp()}] Failed mission: {mission['name']}")
                return {"success": False, "status": "failed", "error": response.text}
            
        except Exception as e:
            print(f"{Fore.RED}[{self.get_timestamp()}] Error completing mission: {str(e)}")
            return {"success": False, "status": "error", "error": str(e)}

    def auto_complete_missions(self):
        while True:
            try:
                print(f"{Fore.CYAN}[{self.get_timestamp()}] Checking missions...")
                print(f"{Fore.MAGENTA}[{self.get_timestamp()}] User ID: {self.user_id}")

                missions = self.get_missions()
                if not missions:
                    print(f"{Fore.RED}[{self.get_timestamp()}] Failed to get missions")
                    time.sleep(30)
                    continue
                
                mission_status = self.get_mission_status()
                if mission_status is None:
                    print(f"{Fore.RED}[{self.get_timestamp()}] Failed to get mission status")
                    time.sleep(30)
                    continue
                
                status_dict = {
                    status['loyaltyRuleId']: {
                        'status': status['status'],
                        'message': status.get('message', '')
                    }
                    for status in mission_status
                } if mission_status else {}

                for mission in missions:
                    mission_id = mission.get('id')
                    mission_name = mission.get('name')
                    
                    current_status = status_dict.get(mission_id, {}).get('status', 'pending')
                    if current_status == 'completed':
                        print(f"{Fore.GREEN}[{self.get_timestamp()}] Already completed: {mission_name}")
                        continue

                    result = self.complete_mission(mission)
                    
                    if result:
                        response_message = result.get('message', '')
                        if "already been rewarded" in response_message:
                            print(f"{Fore.YELLOW}[{self.get_timestamp()}] Already completed: {mission_name}")
                        elif "try again tomorrow" in response_message:
                            print(f"{Fore.YELLOW}[{self.get_timestamp()}] Daily mission already done: {mission_name}")
                        elif "Completion request added to queue" in response_message:
                            print(f"{Fore.BLUE}[{self.get_timestamp()}] Mission queued: {mission_name}")
                    else:
                        print(f"{Fore.RED}[{self.get_timestamp()}] Failed mission: {mission_name}")
                    
                    time.sleep(2)

                available_missions = missions
                completed = sum(1 for m in available_missions if status_dict.get(m.get('id'), {}).get('status') == 'completed')
                total = len(available_missions)
                print(f"\n[{self.get_timestamp()}] Progress: {completed}/{total} available missions completed")
                
                print(f"{Fore.CYAN}[{self.get_timestamp()}] Waiting 30 seconds before next check...")
                time.sleep(30)

            except Exception as e:
                print(f"{Fore.RED}[{self.get_timestamp()}] Error in auto complete loop: {e}")
                time.sleep(30)

    def get_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def read_tokens_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            tokens = [line.strip() for line in file if line.strip()]
        return tokens
    except Exception as e:
        print(f"{Fore.RED}[{datetime.now()}] Error reading tokens from file: {e}")
        return []

if __name__ == "__main__":
    try:
        tokens = read_tokens_from_file('token.txt')
        if not tokens:
            print(f"{Fore.RED}[{datetime.now()}] No tokens found in token.txt!")
            exit(1)
        
        for AUTH_TOKEN in tokens:
            if AUTH_TOKEN.startswith("Bearer "):
                AUTH_TOKEN = AUTH_TOKEN[7:]
                
            if not AUTH_TOKEN:
                print(f"{Fore.RED}[{datetime.now()}] Token cannot be empty!")
                continue
                
            print(f"{Fore.BLUE}[{datetime.now()}] =====  AirDropFamilyIDN  =====")
            print(f"{Fore.BLUE}[{datetime.now()}] =        Oxya Origin  v1.2   =")
            print(f"{Fore.BLUE}[{datetime.now()}] =  Joiv Vip For Bot Premium  =")
            print(f"{Fore.BLUE}[{datetime.now()}] ========= ADFMIDN ============") 
            print(f"\n[{datetime.now()}] Starting bot for token...")
            bot = OxyaOriginBot(AUTH_TOKEN)
            print(f"{Fore.GREEN}[{datetime.now()}] Bot successfully connected!")
            print(f"{Fore.CYAN}[{datetime.now()}] Starting auto complete missions...\n")
            bot.auto_complete_missions()
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}[{datetime.now()}] Terminated by user")
    except Exception as e:
        print(f"{Fore.RED}[{datetime.now()}] An error occurred: {e}")
