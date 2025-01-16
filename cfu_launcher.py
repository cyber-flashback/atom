import subprocess
import os
import webbrowser
import time
import requests
import json
import glob
import threading
import sys
import pandas as pd  # CSV 파일 처리를 위해 pandas 추가


class ComfyUIWorkflowEditor:
    def __init__(self, workflow_path, default_positive_prompt="masterpiece, best quality", default_negative_prompt="low quality, bad anatomy", api_url="http://127.0.0.1:8188"):
        self.workflow_path = workflow_path
        self.default_positive_prompt = default_positive_prompt
        self.default_negative_prompt = default_negative_prompt
        self.api_url = api_url  # ComfyUI API URL
        self.output_dir = r"C:\Users\07\AppData\Roaming\StabilityMatrix\Packages\ComfyUI\output"
        self.last_checked = 0  # 마지막으로 확인한 파일 수정 시간
        self.stop_monitoring = False  # 폴더 감시 종료 플래그

    def load_workflow(self):
        # 워크플로우 JSON 파일 로드
        try:
            with open(self.workflow_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading workflow: {e}")
            return None

    def save_workflow(self, workflow):
        # 워크플로우 JSON 파일 저장
        try:
            with open(self.workflow_path, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2, ensure_ascii=False)
            print("Workflow saved successfully.")
        except Exception as e:
            print(f"Error saving workflow: {e}")

    def update_prompts(self, positive_prompt=None, negative_prompt=None):
        # 긍정 및 부정 프롬프트 수정
        workflow = self.load_workflow()
        if not workflow:
            return None

        updated = False

        # 새 긍정 및 부정 프롬프트 생성
        new_positive_prompt = f"{self.default_positive_prompt}, {positive_prompt}" if positive_prompt else self.default_positive_prompt
        new_negative_prompt = f"{self.default_negative_prompt}, {negative_prompt}" if negative_prompt else self.default_negative_prompt

        for node in workflow.values():
            if isinstance(node, dict) and node.get("class_type") == "CLIPTextEncode":
                if "Positive" in node.get("_meta", {}).get("title", ""):
                    widgets_values = node["inputs"].get("text")
                    if widgets_values and isinstance(widgets_values, str):
                        print(f"Updating positive prompt: {widgets_values} -> {new_positive_prompt}")
                        node["inputs"]["text"] = new_positive_prompt
                        updated = True
                elif "Negative" in node.get("_meta", {}).get("title", ""):
                    widgets_values = node["inputs"].get("text")
                    if widgets_values and isinstance(widgets_values, str):
                        print(f"Updating negative prompt: {widgets_values} -> {new_negative_prompt}")
                        node["inputs"]["text"] = new_negative_prompt
                        updated = True

        if updated:
            self.save_workflow(workflow)
            return workflow
        else:
            print("No prompt nodes found to update.")
            return None

    def queue_workflow(self, workflow):
        # 워크플로우를 API에 전송하여 실행
        try:
            response = requests.post(f"{self.api_url}/prompt", json={"prompt": workflow, "version": 0.4})
            if response.status_code == 200:
                print("Workflow queued successfully.")
                threading.Thread(target=self.monitor_folder, daemon=True).start()
                return response.json()
            else:
                print(f"Failed to queue workflow. Status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error sending workflow to API: {e}")

    def monitor_folder(self):
        # 폴더를 감지하여 새로운 파일이 생성되면 열고 종료
        print(f"Monitoring folder: {self.output_dir}")
        try:
            files = glob.glob(os.path.join(self.output_dir, "*.png"))
            self.last_checked = max([os.path.getmtime(f) for f in files], default=time.time())

            while not self.stop_monitoring:
                files = glob.glob(os.path.join(self.output_dir, "*.png"))
                if files:
                    latest_file = max(files, key=os.path.getmtime)
                    latest_mtime = os.path.getmtime(latest_file)

                    if latest_mtime > self.last_checked:
                        print(f"New image detected: {latest_file}")
                        self.last_checked = latest_mtime
                        self.open_image(latest_file)
                        self.stop_monitoring = True
                        return

                time.sleep(1)
        except Exception as e:
            print(f"Error monitoring folder: {e}")

    def open_image(self, file_path):
        # 이미지 열기
        try:
            print(f"Opening image: {file_path}")
            os.startfile(file_path)
        except Exception as e:
            print(f"Error opening image: {e}")


def check_comfyui_running(max_retries=10):
    # ComfyUI 서버가 응답하는지 확인
    for _ in range(max_retries):
        try:
            response = requests.get("http://127.0.0.1:8188")
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(1)
    return False


def launch_stabilitymatrix_comfyui(auto_launch_browser=True):
    # StabilityMatrix의 ComfyUI를 실행하고 정상 작동 확인 후 터미널 종료
    comfyui_path = os.path.join(
        os.path.expanduser("~"),
        "AppData", "Roaming", "StabilityMatrix", "Packages", "ComfyUI"
    )

    venv_python = os.path.join(
        comfyui_path, "venv", "Scripts", "python.exe"
    )

    main_script = os.path.join(comfyui_path, "main.py")

    env = os.environ.copy()
    env["PYTHON_EXECUTABLE"] = venv_python

    try:
        process = subprocess.Popen(
            args=[venv_python, main_script],
            env=env,
            cwd=comfyui_path,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        if check_comfyui_running():
            print("ComfyUI started successfully!")
            if auto_launch_browser:
                webbrowser.open("http://127.0.0.1:8188")
            return True
        else:
            print("Failed to start ComfyUI")
            process.terminate()
            return False

    except Exception as e:
        print(f"Error launching ComfyUI: {e}")
        return False


def main():
    # ComfyUI 실행 확인 및 실행 (처음 실행 시만 실행)
    if not check_comfyui_running():
        print("ComfyUI is not running. Launching...")
        if not launch_stabilitymatrix_comfyui():
            print("Failed to start ComfyUI. Exiting...")
            sys.exit(1)
    else:
        print("ComfyUI is already running.")

    # JSON 파일 경로 설정
    workflow_path = r"C:\Users\07\Desktop\comfyuitest\war.json"

    # CSV 파일 경로 설정
    csv_path = r"C:\Users\07\Desktop\comfyuitest\test_prompt.csv"

    # CSV 파일 읽기
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"CSV file not found at {csv_path}")
        sys.exit(1)

    # 긍정적 및 부정적 프롬프트 가져오기
    positive_prompts = df[df["Type"] == "Positive"]["Prompt"].tolist()
    negative_prompts = df[df["Type"] == "Negative"]["Prompt"].tolist()

    # 첫 번째 긍정적/부정적 프롬프트 사용
    positive_prompt = positive_prompts[0] if positive_prompts else None
    negative_prompt = negative_prompts[0] if negative_prompts else None

    # 워크플로우 편집기 생성 및 업데이트
    editor = ComfyUIWorkflowEditor(workflow_path)
    workflow = editor.update_prompts(positive_prompt, negative_prompt)

    if workflow:
        queue_prompt = input("Do you want to queue the updated workflow and monitor for new images? (yes/no): ").strip().lower()
        if queue_prompt in ["yes", "y"]:
            editor.queue_workflow(workflow)
            print("Monitoring for new images...")
            while not editor.stop_monitoring:
                time.sleep(1)
            print("Monitoring stopped after new image was opened.")
        else:
            print("Workflow update saved but not queued.")


if __name__ == "__main__":
    main()
