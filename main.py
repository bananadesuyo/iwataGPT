import json
import random
import asyncio
from janome.tokenizer import Tokenizer
from pyscript import document, window

# ==========================================
# モデルリストの定義
# ==========================================
MODEL_LIST = {
    "iwataGPT1.0": "iwataGPT1.0.json",
    "iwataGPT1.1": "iwataGPT1.1.json"
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
        # 2文字以上の単語でマッチングを優先
        candidates = [t for t in user_tokens if t in self.model and len(t) > 1]
        
        if candidates:
            seed = random.choice(candidates)
        elif any(t in self.model for t in user_tokens):
            seed = random.choice([t for t in user_tokens if t in self.model])
        else:
            seed = random.choice(self.starts) if self.starts else ""

        if not seed: return "..."

        result = [seed]
        curr = seed
        for _ in range(15):
            next_options = self.model.get(curr)
            if not next_options: break
            curr = random.choice(next_options)
            result.append(curr)
            if curr in ["？", "！", "。", "ｗ", "？"]: break
        return "".join(result)

# AIインスタンス
ai = MarkovAI()

async def load_model_file(filename):
    """ネットワーク経由でJSONを取得して学習"""
    try:
        # GitHub上のファイルをフェッチ
        response = await window.fetch(filename)
        if not response.ok:
            return False
        
        text = await response.text()
        data = json.loads(text)
        ai.learn_from_list(data)
        return True
    except Exception as e:
        print(f"Fetch Error: {e}")
        return False

async def setup():
    """初期セットアップ"""
    select_el = document.querySelector("#model-select")
    
    # ドロップダウンを作成
    for name, file in MODEL_LIST.items():
        opt = document.createElement("option")
        opt.value = file
        opt.text = name
        select_el.add(opt)
    
    # 最初のモデルをロード
    first_file = list(MODEL_LIST.values())[0]
    await load_model_file(first_file)
    
    # JavaScriptのhideLoading関数を実行してグレーアウトを解除
    window.hideLoading()
    print("AI Ready!")

# 非同期でセットアップを実行
asyncio.ensure_future(setup())

async def change_model(event):
    filename = event.target.value
    chat_log = document.querySelector("#chat-log")
    
    # ローディング表示を一時的に復活させても良い
    success = await load_model_file(filename)
    
    msg = f"--- モデルを {filename} に切り替えました ---" if success else "--- 切り替え失敗 ---"
    chat_log.innerHTML += f"<div style='color:gray; font-size:0.8em;'>{msg}</div>"

def process_input(event):
    input_el = document.querySelector("#user-input")
    chat_log = document.querySelector("#chat-log")
    user_text = input_el.value
    if not user_text.strip(): return

    # ユーザー発言表示
    chat_log.innerHTML += f"<div class='user'>俺: {user_text}</div>"
    
    # 返答生成
    reply = ai.generate_reply(user_text)
    chat_log.innerHTML += f"<div class='ai'>AI: {reply}</div>"
    
    # 入力欄をクリアしてスクロール
    input_el.value = ""
    chat_log.scrollTop = chat_log.scrollHeight