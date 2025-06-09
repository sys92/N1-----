import os
import httpx
from models.schemas import TranscriptionResult

class AnalysisService:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_api_url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    
    async def analyze(self, transcription: TranscriptionResult) -> str:
        """
        Groq APIを使用してN1分析を実行する
        """
        print(f"🔍 [ANALYSIS] 分析開始 - 文字数: {len(transcription.full_text)}")

        if not self.groq_api_key:
            raise Exception("GROQ_API_KEY environment variable is not set")
        
        # 分析プロンプトを構築
        print(f"📝 [ANALYSIS] プロンプト構築中...")
        prompt = self._build_analysis_prompt(transcription.full_text)
        
        try:
            print(f"🌐 [ANALYSIS] Groq APIにリクエスト送信中...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.groq_api_url,
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                        "stream": False,
                        "temperature": 0.1
                    },
                    timeout=300.0  # 5分のタイムアウト
                )

                if response.status_code != 200:
                    print(f"❌ [ANALYSIS] Groq APIエラー: {response.status_code}")
                    raise Exception(f"Groq API error: {response.status_code} - {response.text}")

                result = response.json()
                analysis_text = result["choices"][0]["message"]["content"]

                print(f"✅ [ANALYSIS] 分析完了 - 結果文字数: {len(analysis_text)}")
                return analysis_text
                
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
    
    def _build_analysis_prompt(self, transcription_text: str) -> str:
        """
        顧客定性調査・広告設計に特化した分析プロンプトを構築する
        """
        prompt = """## ロール
あなたは顧客定性調査・広告設計の専門家です。
以下の「インタビュー全文」を読み、3段階に分けて丁寧に整理してください。

---

## ◆目的
1. インタビューの内容を4つの観点（プロフィール／購入前／印象／購入後）で分類する
2. そこから「既存認知」と「新認知」を抽出し、内容・シーン・感情の3点で記述する
3. 最後に、新認知の情報をもとに、広告台本のプロット（伝える順番）を設計する

---

## ◆分析手順と出力フォーマット

---

### 【第1段階】インタビュー内容の分類

#### ■プロフィール
- 年齢:（【】）
- 住まい:（【】）
- 職業 / 勤務形態:（【】）
- 1日の流れ:（【】）
- 家族構成 / 世帯年収・家族職業:（【】）
- 家計管理スタイル:（【】）
- 住居（持ち家 or 賃貸・家賃・ローン年数 等）:（【】）
- 家の間取り:（【】）
- 買い物傾向（固定費・大きい買い物・金銭感覚・貯蓄目標）:（【】）
- よく見るSNS:（【】）
- 趣味:（【】）
- サービス利用開始時期:（【】）
- MBTI:（【】）
- ●その他情報:（【】）

#### ■購入前
- 購入前の場面:（【】）
- 感情:（【】）
- 感情比率（%）:（【】）
- 購入理由:（【】）
- 試行錯誤した他の手段:
  - 良かった点:（【】）
  - 至らなかった点:（【】）
  - 金額:（【】）
  - 情報経路:（【】）
  - 解決できず感じたこと:（【】）
- 思いついたが試さなかった施策:
  - 理由:（【】）
- 理想を叶える商品の条件（場面・感情・比率）:（【】）
- ●その他情報:（【】）

#### ■印象
- 第一印象（良かった点・懸念・刺さった言葉）:（【】）
- 詳細を知っての印象（懸念／決め手）:（【】）
- リード登録時の印象（該当すれば）:（【】）
- 購入直前の決め手:（【】）
- ●その他情報:（【】）

#### ■購入後
- ビフォー→アフター（感情・行動）:（【】）
- 現在の使い方・頻度:（【】）
- 他商品との違い:（【】）
- 推薦したい人・実際に薦めた経験:（【】）
- ●その他情報:（【】）

#### ■購入商品情報
- 商品名／サービス名:（【】）
- 商品カテゴリー:（【】）
- 商品価格:（【】）
- 商品販路（購入場所）:（【】）
- 金額:（【】）
- その他情報:（【】）

---

### 【第2段階】既存認知／新認知の抽出

#### ■既存認知（購入前にもともと持っていた認識）
- 内容:
  - シーン:
  - 感情・イメージ:
  - タイムスタンプ: 【】

- 内容:
  - シーン:
  - 感情・イメージ:
  - タイムスタンプ: 【】

#### ■新認知（購入の決め手になった新しい理解）
- 内容:
  - シーン:
  - 感情・イメージ:
  - タイムスタンプ: 【】

- 内容:
  - シーン:
  - 感情・イメージ:
  - タイムスタンプ: 【】

---

### 【第3段階】広告プロットの設計

#### ■想定されるよくある既存認知
- 内容:（【】）

#### ■伝えるべき順序（ストーリー構成）
- ステップ①（最初に届けるべき新認知）
  - 内容:（【】）
  - シーン:
  - 感情・イメージ:

- ステップ②（次に伝えるべき補完情報）
  - 内容:（【】）
  - シーン:
  - 感情:

- ステップ③（購入を決めさせる最終情報）
  - 内容:（【】）
  - シーン:
  - 感情:

## 分析対象の書き起こし
""" + transcription_text

        return prompt
