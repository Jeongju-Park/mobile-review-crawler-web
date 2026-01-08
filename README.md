# Mobile Review Collector (Web Version)

모바일 앱 스토어(Apple App Store, Google Play Store)에서 사용자 리뷰를 수집하는 웹 애플리케이션입니다.

## 🚀 배포 방법 (Streamlit Cloud)

### 1. GitHub 저장소 생성
1. GitHub에서 새 저장소 생성
2. 이 폴더의 모든 파일을 업로드

### 2. Streamlit Cloud 연결
1. [share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 계정으로 로그인
3. "New app" 클릭
4. 저장소 선택 → `app.py` 선택
5. "Deploy!" 클릭

### 3. 배포 완료!
- 약 2-3분 후 URL이 생성됩니다
- 예: `https://your-app-name.streamlit.app`

## 💻 로컬 실행 방법

```bash
# 패키지 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

## 📱 기능

- Apple App Store 리뷰 수집
- Google Play Store 리뷰 수집
- 최대 5,000개 리뷰 수집 가능
- 실시간 진행 상황 표시
- 텍스트 파일 다운로드
- 평점 필터링 및 정렬

## 🎓 멋쟁이사자처럼 부트캠프용 VoC 크롤링
