import google.generativeai as genai
import pandas as pd
import re
import json
from transformers import T5Tokenizer, T5ForConditionalGeneration


tokenizer = T5Tokenizer.from_pretrained("t5-small")
model = T5ForConditionalGeneration.from_pretrained("t5-small")

text1 = """
World War II[b] or the Second World War (1 September 1939 – 2 September 1945) was a global
conflict between two coalitions: the Allies and the Axis powers. Nearly all the world's countries—
including all the great powers—participated, with many investing all available economic, industrial, and
scientific capabilities in pursuit of total war, blurring the distinction between military and civilian
resources. Tanks and aircraft played major roles, with the latter enabling the strategic bombing of
population centres and delivery of the only two nuclear weapons ever used in war. World War II was the
deadliest conflict in history, resulting in 70 to 85 million deaths, more than half being civilians. Millions
died in genocides, including the Holocaust of European Jews, as well as from massacres, starvation, and
disease. Following the Allied powers' victory, Germany, Austria, Japan, and Korea were occupied, and
war crimes tribunals were conducted against German and Japanese leaders.
The causes of World War II included unresolved tensions in the aftermath of World War I and the rise of
fascism in Europe and militarism in Japan. Key events leading up to the war included Japan's invasion of
Manchuria, the Spanish Civil War, the outbreak of the Second Sino-Japanese War, and Germany's
annexations of Austria and the Sudetenland. World War II is generally considered to have begun on 1
September 1939, when Nazi Germany, under Adolf Hitler, invaded Poland, prompting the United
Kingdom and France to declare war on Germany. Poland was divided between Germany and the Soviet
Union under the Molotov–Ribbentrop Pact, in which they had agreed on "spheres of influence" in Eastern
Europe. In 1940, the Soviets annexed the Baltic states and parts of Finland and Romania. After the fall of
France in June 1940, the war continued mainly between Germany and the British Empire, with fighting in
the Balkans, Mediterranean, and Middle East, the aerial Battle of Britain and the Blitz, and naval Battle
of the Atlantic. Through a series of campaigns and treaties, Germany took control of much of continental
Europe and formed the Axis alliance with Italy, Japan, and other countries. In June 1941, Germany led
the European Axis in an invasion of the Soviet Union, opening the Eastern Front and initially making
large territorial gains.
"""
text2 = """
Japan aimed to dominate East Asia and the Asia-Pacific, and by 1937 was at war with the Republic of
China. In December 1941, Japan attacked American and British territories in Southeast Asia and the
Central Pacific, including Pearl Harbor in Hawaii, which resulted in the US and the UK declaring war
against Japan, and the European Axis declaring war on the US. Japan conquered much of coastal China
and Southeast Asia, but its advances in the Pacific were halted in mid-1942 after its defeat in the naval
Battle of Midway; Germany and Italy were defeated in North Africa and at Stalingrad in the Soviet
Union. Key setbacks in 1943—including German defeats on the Eastern Front, the Allied invasions of
Sicily and the Italian mainland, and Allied offensives in the Pacific—cost the Axis powers their initiative
and forced them into strategic retreat on all fronts. In 1944, the Western Allies invaded German-occupied
France at Normandy, while the Soviet Union regained its territorial losses and pushed Germany and its
allies westward. At the same time, Japan suffered reversals in mainland Asia, while the Allies crippled the
Japanese Navy and captured key islands.
"""
text3 = """
The war in Europe concluded with the liberation of German-occupied territories; the invasion of
Germany by the Western Allies and the Soviet Union, culminating in the fall of Berlin to Soviet troops;
Hitler's suicide; and the German unconditional surrender on 8 May 1945. Following the refusal of Japan
to surrender on the terms of the Potsdam Declaration, the US dropped the first atomic bombs on
Hiroshima and Nagasaki on 6 and 9 August. Faced with an imminent invasion of the Japanese
archipelago, the possibility of further atomic bombings, and the Soviet declaration of war against Japan
and its invasion of Manchuria, Japan announced its unconditional surrender on 15 August and signed a
surrender document on 2 September 1945, marking the end of the war.
World War II changed the political alignment and social structure of the world, and it set the foundation
of international relations for the rest of the 20th century and into the 21st century. The United Nations
was established to foster international cooperation and prevent conflicts, with the victorious great powers
—China, France, the Soviet Union, the UK, and the US—becoming the permanent members of its
security council. The Soviet Union and the United States emerged as rival superpowers, setting the stage
for the Cold War. In the wake of European devastation, the influence of its great powers waned,
triggering the decolonisation of Africa and Asia. Most countries whose industries had been damaged
moved towards economic recovery and expansion.
"""

def summarize_text(text, model, tokenizer, max_input_length=512, summary_length=100):
    input_text = "summarize: " + text
    inputs = tokenizer(input_text, return_tensors="pt", max_length=max_input_length, truncation=True)
    summary_ids = model.generate(
        inputs["input_ids"],
        max_length=summary_length,
        min_length=50,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True,
    )
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

# 긴 텍스트를 분할
texts = [text1, text2, text3]
partial_summaries = [summarize_text(t, model, tokenizer) for t in texts]

# 부분 요약을 하나로 연결하고 최종 요약 생성
final_input = " ".join(partial_summaries)
final_summary = summarize_text(final_input, model, tokenizer, summary_length=150)

print(final_summary)

with open(r'C:\Users\07\Desktop\comfyuitest\secret.json') as f:
    secrets = json.loads(f.read())
    
SECRET_KEY = secrets['gemeni_api']

genai.configure(api_key=SECRET_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content(
    final_summary + 
    """
    긍정적 : "masterpiece, best quality, high detail, dynamic composition, cinematic lighting, vibrant colors, intricate details, realistic textures, award-winning photograph, breathtaking scene"
    부정적 : "low quality, bad composition, unrealistic colors, blurred image, noisy, oversaturated, overexposed, low resolution, distorted details, poorly lit, unbalanced proportions"
    이런 형태의 긍정적 프롬프트와 부정적 프롬프트를 만들어줘
    """
    )
print(response.text)
response_text = response.text

# 긍정적 프롬프트와 부정적 프롬프트를 추출하는 함수
def extract_prompts(response_text):
    # 텍스트를 긍정적과 부정적 섹션으로 분리
    sections = response_text.split("**Negative Prompts:**")
    positive_section = sections[0]
    negative_section = sections[1] if len(sections) > 1 else ""

    # 개선된 정규표현식 패턴을 사용하여 프롬프트 추출
    def extract_quoted_text(text):
        # 따옴표 안의 텍스트를 찾고, 여러 줄 처리
        quotes = re.findall(r'"([^"]*)"', text, re.DOTALL)
        # 각 인용구의 불필요한 공백과 줄바꿈 제거
        return [' '.join(quote.split()) for quote in quotes]

    # 모든 프롬프트를 추출하고 하나로 결합
    positive_prompts = extract_quoted_text(positive_section)
    negative_prompts = extract_quoted_text(negative_section)
    
    # 각각의 프롬프트를 쉼표로 구분하여 하나로 결합
    combined_positive = ", ".join(positive_prompts)
    combined_negative = ", ".join(negative_prompts)
    
    return [combined_positive], [combined_negative]

# 프롬프트 추출
positive_prompts, negative_prompts = extract_prompts(response_text)

# 데이터프레임 생성
data = {
    "Type": ["Positive"] * len(positive_prompts) + ["Negative"] * len(negative_prompts),
    "Prompt": positive_prompts + negative_prompts
}
df = pd.DataFrame(data)

# CSV 파일로 저장
file_name = "test_prompt.csv"
df.to_csv(file_name, index=False, encoding="utf-8")
print(f"CSV 파일이 '{file_name}'로 저장되었습니다.")