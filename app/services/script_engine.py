import os
import json
import re
from typing import Dict, Any, Optional
from app.database import get_setting

# Try importing google-genai
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class ScriptEngine:
    def __init__(self):
        pass

    def _get_gemini_client(self) -> Optional[Any]:
        api_key = get_setting("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        if HAS_GENAI and api_key:
            try:
                return genai.Client(api_key=api_key)
            except Exception:
                return None
        return None

    def generate_script(self, topic: str, duration: int = 30, niche: str = "일반") -> Dict[str, Any]:
        """
        Generates structured Shorts script:
        - hook: 강력한 첫 3초 훅 문구
        - body: 2~3문장의 핵심 가치 및 흥미로운 정보
        - cta: 마무리 행동 유도
        - yt_title: 클릭률 높은 유튜브 제목
        - yt_description: SEO 최적화 설명
        - yt_tags: 추천 해시태그 목록
        """
        client = self._get_gemini_client()
        if client:
            try:
                return self._generate_with_gemini(client, topic, duration, niche)
            except Exception as e:
                print(f"[ScriptEngine] Gemini API error, falling back to smart engine: {e}")

        # Intelligent Built-in Prompt & Creative Generation Engine
        return self._generate_with_smart_engine(topic, duration, niche)

    def _generate_with_gemini(self, client: Any, topic: str, duration: int, niche: str) -> Dict[str, Any]:
        target_words = {
            15: "약 30~40단어 (읽었을 때 15초 내외)",
            30: "약 60~75단어 (읽었을 때 30초 내외)",
            45: "약 90~110단어 (읽었을 때 45초 내외)",
            60: "약 120~140단어 (읽었을 때 60초 내외)"
        }.get(duration, "약 65단어")

        prompt = f"""당신은 100만 구독자를 보유한 유튜브 쇼츠(Shorts) 전문 크리에이티브 디렉터입니다.
다음 주제에 대해 시청 지속 시간(Retention) 80% 이상을 달성할 수 있는 고품질 쇼츠 스크립트와 메타데이터를 작성해주세요.

[입력 정보]
- 주제/키워드: {topic}
- 목표 영상 길이: {duration}초 ({target_words})
- 콘텐츠 분야: {niche}

[요구사항]
1. Hook: 첫 3초 이내에 스크롤을 멈추게 할 파격적이고 호기심을 자극하는 문장 (1~2문장)
2. Body: 시청자에게 실질적인 충격, 공감, 깨달음을 주는 핵심 내용 (간결하고 리듬감 있는 문장)
3. CTA: 자연스럽게 댓글 또는 구독을 유도하는 마무리 멘트 (1문장)
4. 모든 문장은 TTS로 읽었을 때 매끄러운 구어체(한국어)로 작성.
5. 반드시 아래 JSON 형식으로만 응답하세요:

{{
  "hook": "첫 3초 훅 멘트",
  "body": "본론 스토리라인 (간결하고 강렬한 정보)",
  "cta": "마무리 유도 멘트",
  "yt_title": "이모지가 포함된 클릭률 높은 유튜브 쇼츠 제목",
  "yt_description": "유튜브 쇼츠 설명글 (2~3줄 요약)",
  "yt_tags": ["#Shorts", "#쇼츠", "#{topic.replace(' ', '')}", "#정보", "#꿀팁"]
}}
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        text = response.text
        return json.loads(text)

    def _generate_with_smart_engine(self, topic: str, duration: int, niche: str) -> Dict[str, Any]:
        """High-retention rule-based and template-enhanced creative script generator"""
        clean_topic = topic.strip().rstrip(".!?")
        
        # Determine topic tone
        is_money = any(k in clean_topic for k in ["돈", "재테크", "주식", "부자", "월급", "비트코인", "투자", "소득"])
        is_history = any(k in clean_topic for k in ["역사", "비밀", "미스터리", "사건", "괴담", "고대", "조선"])
        is_tech = any(k in clean_topic for k in ["AI", "인공지능", "테크", "스마트폰", "로봇", "미래", "컴퓨터", "우주"])
        is_life = any(k in clean_topic for k in ["직장", "인간관계", "습관", "인생", "꿀팁", "생존", "심리", "멘탈"])

        if is_money:
            hook = f"아직도 {clean_topic} 모르고 계셨나요? 99%의 사람들이 모르는 부자들의 진짜 비밀입니다."
            body = f"대부분의 사람들은 돈을 버는 데 집중하지만, 상위 1%는 돈이 스스로 일하게 만듭니다. 첫째, 불필요한 고정 지출부터 즉시 차단하세요. 둘째, 매달 소액이라도 우량 자산에 복리로 투자하세요. 작은 습관의 차이가 5년 뒤 상상 이상의 격차를 만듭니다."
            cta = "지금 통장 잔고를 바꾸고 싶다면 구독 누르고 매일 부의 추월차선에 올라타세요!"
            title_prefix = "💰 상위 1%만 아는"
        elif is_history:
            hook = f"교과서에서는 절대 알려주지 않는 {clean_topic}의 충격적인 진실, 알고 계셨나요?"
            body = f"우리가 당연하게 믿었던 역사적 사실 뒤에는 감춰진 기록이 있었습니다. 당시의 비밀 문서에 따르면, 사건의 진짜 배후는 상상도 못한 인물이었습니다. 역사는 승자의 기록이지만 진실은 결코 사라지지 않습니다."
            cta = "더 소름 돋는 미스터리가 궁금하다면 지금 바로 구독과 좋아요를 눌러주세요!"
            title_prefix = "🕵️ 역사 속에 감춰진"
        elif is_tech:
            hook = f"앞으로 3년 뒤, {clean_topic} 모르면 완전히 도태될 수 있습니다."
            body = f"지금 전 세계 기술의 판도가 완전히 뒤집히고 있습니다. 이미 글로벌 기업들은 모든 시스템을 개편하고 있죠. 변화를 두려워하는 사람은 사라지지만, 이 흐름을 먼저 타는 사람은 압도적인 기회를 잡게 됩니다."
            cta = "미래 테크 트렌드를 가장 빠르게 잡고 싶다면 지금 구독하세요!"
            title_prefix = "⚡ 2026 미래 기술"
        elif is_life:
            hook = f"{clean_topic}, 이 세 가지만 기억해도 인생 스트레스 90%는 사라집니다."
            body = f"첫째, 타인의 시선에 내 에너지를 낭비하지 마세요. 둘째, 해결할 수 없는 고민은 지금 당장 머릿속에서 삭제하세요. 셋째, 오늘 하루 단 10분이라도 나만을 위한 몰입의 시간을 가지세요. 결국 남는 건 내 실력과 마음의 평화뿐입니다."
            cta = "오늘 하루도 치열하게 살아낸 당신을 응원합니다. 함께 성장할 분은 구독해주세요!"
            title_prefix = "💡 멘탈 관리 필수 꿀팁"
        else:
            hook = f"당신이 지금까지 몰랐던 {clean_topic}에 대한 놀라운 비밀 1위는 무엇일까요?"
            body = f"전문가들조차 깜짝 놀란 사실이 밝혀졌습니다. 핵심은 바로 우리가 당연하게 생각했던 일상의 작은 디테일 속에 있었습니다. 이 원리를 제대로 이해하고 적용하는 순간 당신의 하루가 완전히 달라집니다."
            cta = "유익하셨다면 좋아요와 구독으로 다음 꿀팁도 놓치지 마세요!"
            title_prefix = "🔥 꼭 알아야 할"

        # Adjust length if duration is short (15s) or long (60s)
        if duration <= 15:
            body_sentences = body.split(". ")
            body = ". ".join(body_sentences[:2]) + "."
        elif duration >= 60:
            body += f" 특히 {clean_topic}과 관련된 핵심 포인트는 아무도 쉽게 가르쳐주지 않습니다. 지금 바로 실천해 보세요."

        yt_title = f"{title_prefix} {clean_topic}의 충격적인 진실! 😱 #Shorts"
        yt_description = f"{clean_topic}에 대해 반드시 알아야 할 핵심 정보를 30초 만에 완벽 정리해 드립니다!\n\n#Shorts #쇼츠 #지식 #{clean_topic.replace(' ', '')}"
        
        hashtag_topic = re.sub(r'[^a-zA-Z0-9가-힣]', '', clean_topic)
        yt_tags = ["#Shorts", "#쇼츠", f"#{hashtag_topic}", "#꿀팁", "#정보", "#AI쇼츠"]

        return {
            "hook": hook,
            "body": body,
            "cta": cta,
            "yt_title": yt_title,
            "yt_description": yt_description,
            "yt_tags": yt_tags
        }
