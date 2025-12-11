# 가천대학교 2025 가을학기 알고리즘 기말 대체 과제 (LCS 알고리즘이 적용된 표절 감지 서비스 프로토타입 만들기)
##### 부제: 바이브 코딩으로 서비스를 만들어보자
큰 틀은 [이 pdf 문서를](./요구사항%20문서.pdf) 참조해주세요.
## 유의 사항
해당 서비스는 OPENAI의 GPT5-mini를 사용해요. 여기서 비용이 발생할 수 있어요. 만약 공개되어도 괜찮은 정보들만 올라온다면 `Share inputs and outputs with OpenAI` 옵션을 활성화해 비용을 절감할 수 있어요.
## 필요 패키지
pip를 통해서 backend 에 다음 패키지들을 설치해주세요
```
flask
flask-cors
dotenv
pypdf2
openai
bs4
```
## 실행 전에
1. [필요 패키지들을](./README.md#필요-패키지) 확인하고 설치해주세요
2. OPENAPI와 Google API 설정을 각각 해주세요.
   이번 프로젝트에서 세팅한 검색엔진 세팅은 다음과 같아요(참고용)
   ![](https://cdn.discordapp.com/attachments/802845417875701770/1448203694490390558/image.png?ex=693a684b&is=693916cb&hm=396ec956b0ed166291e840b6d746401b31e0492c320609774d4bbfe16bc85f20&)
3. backend 디렉터리에 .env파일을 만들고 다음과 같이 채워주세요.
   ```
   OPENAI_API_KEY=크레딧이 충전되어있는 OPENAPI에서 발급받은 API 키
   GOOGLE_API_KEY=구글 프로젝트의 API 키
   GOOGLE_SEARCHENGINE_ID=구글 커스텀 검색 엔진의 ID
   ``` 
4. 현재 서버는 localhost:8080에서 돌아감을 상정하고 클라이언트 코드가 짜여 있어요. 만일 다른 환경이라면 [index.html](./frontend/index.html)의 103줄을 수정 후 실행해주세요
5. SSL 인증서 키를 발급받아 backend/sslkey에 각각 `fullchain.pem`, `privkey.pem` 이란 이름으로 넣어주세요.