import json
import random
import asyncio
from janome.tokenizer import Tokenizer
from pyscript import document, window

# ==========================================
# ここに新しいモデルを自由に追加してください
# {"表示名": "ファイル名.json"} の形式です
# ==========================================
MODEL_LIST = {
    "iwataGPT1.0": "iwataGPT1.0.json",
}

class MarkovAI:
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.reset_model()

    def reset_model(self):
        self.model = {}
        self.starts = []

    def _get_tokens(self, text):
        return [token.surface for token in self.tokenizer.tokenize(text)]

    def learn_from_list(self, json_data):
        self.reset_model()
        for text in json_data:
            tokens = self._get_tokens(text)
            if not tokens: continue
            self.starts.append(tokens[0])
            for i in range(len(tokens) - 1):
                curr, nxt = tokens[i], tokens[i+1]
                self.model.setdefault(curr, []).append(nxt)

    def generate_reply(self, user_input):
        user_tokens = self._get_tokens(user_input)
        candidates = [t for t in user_tokens if t in self.model and len(t) > 1]
        seed = random.choice(candidates if candidates else (self.starts if self.starts else [""]))
        if not seed: return "..."

        result = [seed]; curr = seed
        for _ in range(15):
            next_options = self.model.get(curr)
            if not next_options: break
            curr = random.choice(next_options)
            result.append(curr)
            if curr in ["？", "！", "。", "ｗ"]: break
        return "".join(result)

ai = MarkovAI()

async def load_model_file(filename):
    try:
        response = await window.fetch(filename)
        if not response.ok: raise Exception("File not found")
        text = await response.text()
        data = json.loads(text)
        ai.learn_from_list(data)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# 初期設定：ドロップダウン生成と最初の読込
async def setup():
    select_el = document.querySelector("#model-select")
    for name, file in MODEL_LIST.items():
        opt = document.createElement("option")
        opt.value = file
        opt.text = name
        select_el.add(opt)
    
    # 最初のモデル（リストの1番目）を読み込む
    first_file = list(MODEL_LIST.values())[0]
    await load_model_file(first_file)

asyncio.ensure_future(setup())

async def change_model(event):
    filename = event.target.value
    chat_log = document.querySelector("#chat-log")
    success = await load_model_file(filename)
    status = f"'{filename}' に切り替えました" if success else f"エラー: {filename}"
    chat_log.innerHTML += f"<div style='color:gray; font-size:0.8em;'>--- {status} ---</div>"

def process_input(event):
    input_el = document.querySelector("#user-input")
    chat_log = document.querySelector("#chat-log")
    user_text = input_el.value
    if not user_text: return

    chat_log.innerHTML += f"<div class='user'>俺: {user_text}</div>"
    reply = ai.generate_reply(user_text)
    chat_log.innerHTML += f"<div class='ai'>AI: {reply}</div>"
    input_el.value = ""
    chat_log.scrollTop = chat_log.scrollHeight