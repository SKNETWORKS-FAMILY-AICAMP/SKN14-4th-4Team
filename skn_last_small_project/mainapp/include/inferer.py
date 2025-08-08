import base64
import os
import threading
from io import BytesIO
import ast

from PIL import Image
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class Inferer:
    def image_to_base64(self, image: Image):
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()

    @classmethod
    def to_pil_image(self, file_path:str):
        return Image.open(file_path).convert('RGB')


class OpenAIInferer(Inferer):
    def __init__(self, model_id="gpt-4.1-nano", temperature=.0, api_key=None):
        self.model_id    = model_id
        self.temperature = temperature

        api_key = api_key if api_key else os.environ.get("OPENAI_API_KEY")
        self.llm         = ChatOpenAI(model=model_id, temperature=temperature, api_key=api_key)
        self.system_msg  = SystemMessage("""
당신은 전 세계 음식들을 모두 다 알고 있는 음식전문가입니다.

당신은 사용자가 제시한 음식 이미지의 정확한 음식명을 반환해야 합니다.
- 답변은 반드시 단답형의 음식명과 그 음식에 들어간 재료 목록을 반환해야 합니다.
- 음식명과 재료목록은 ("음식명", "재료목록") 의 형태로 답변해야 합니다.
- 음식명과 재료목록은 반드시 한글이어야 합니다.
- 답변은 [("음식명", "재료목록")] 과 같이 배열로 감싼 형태여야 합니다.
- 이미지에 음식의 개수가 여러가지라면, 최대 5개의 음식을 배열로 감싸서 반환합니다.
- 만약 음식이미지가 아니라면, 답변 예시를 무시하고 반드시 "not_food" 라고만 답해야 합니다.

< 답변 예시 >
[("짜장면", "춘장, 돼지고기, 양파, 면, 카라멜")]
[("햄버거", "패티, 번, 양상추, 양파, 머스타드소스, 치즈, 피클"), ("베이컨 연어 셀러드", "베이컨, 훈제연어, 양상추, 토마토")]
""")

    def infer(self, image:Image, filename:str, storage:dict, parser=StrOutputParser()):
        """
        음식 이미지를 보고 음식 이름과 재료를 추론한다.
        :param image:       추론할 음식 이미지
        :param filename:    이미지파일 이름. storage 에 저장될 키값으로 사용.
        :param storage:     추론 결과를 저장할 딕셔너리.
        :return: {
            "food1.jpg" : [ ("짜장면", "춘장, 돼지고기, 양파, 면, 카라멜") ],
            "food2.jpg" : [ ("햄버거", "패티, 번, 양상추, 양파, 머스타드소스, 치즈, 피클") ],
        }
        """
        b64_image = self.image_to_base64(image)
        user_msg = HumanMessage([{'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64, {b64_image}'}}])
        prompt = ChatPromptTemplate.from_messages([self.system_msg, user_msg])
        chain = prompt | self.llm | parser

        try:
            result = chain.invoke({})           # '[ ("짜장면", "춘장, 돼지고기, 양파, 면, 카라멜") ]'
            result = ast.literal_eval(result)   #  [ ("짜장면", "춘장, 돼지고기, 양파, 면, 카라멜") ]
            result = {"name" : result[0][0], "ingredients" : result[0][1]}

            storage[filename] = result
        except:
            print("It's not food image.")

    def __call__(self, images:list[Image], *, parser=StrOutputParser()):
        storage = {}
        threads = [threading.Thread(target=self.infer, args=(img, f"food_{i+1}", storage, parser)) for i,img in enumerate(images)]

        for thread in threads:  thread.start()
        for thread in threads:  thread.join()

        return storage

# if __name__ == "__main__":
#     import os
#     from dotenv import load_dotenv
#
#     load_dotenv("../../.env")
#
#     inferer = OpenAIInferer()
#     img1 = Image.open("food1.jpg")
#     img2 = Image.open("food2.jpg")
#     _list = [img1, img2]
#     result = inferer(_list)
#     print(result)