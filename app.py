"""
Mobile Review Collector - Streamlit Web Version
앱 스토어 리뷰를 수집하는 웹 애플리케이션
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import html
from datetime import datetime
import time

# 페이지 설정
st.set_page_config(
    page_title="Mobile Review Collector",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: bold;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #7F8C8D;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .brand-text {
        font-size: 0.8rem;
        color: #BDC3C7;
        text-align: center;
        margin-bottom: 2rem;
    }
    .store-card {
        background: linear-gradient(135deg, #F8FBFF 0%, #EBF5FF 100%);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        border: 2px solid #E3F2FD;
        transition: all 0.3s ease;
    }
    .store-card:hover {
        border-color: #0984E3;
        box-shadow: 0 4px 12px rgba(9, 132, 227, 0.15);
    }
    .playstore-card {
        background: linear-gradient(135deg, #F8FFF8 0%, #E8F5E9 100%);
        border-color: #E8F5E9;
    }
    .playstore-card:hover {
        border-color: #27AE60;
        box-shadow: 0 4px 12px rgba(39, 174, 96, 0.15);
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    .review-box {
        background: #F8F9FA;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #3498DB;
    }
    .review-rating {
        color: #F39C12;
        font-size: 1.1rem;
    }
    .review-content {
        color: #2C3E50;
        margin: 0.5rem 0;
    }
    .review-meta {
        color: #95A5A6;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ===== HTML 정리 함수 =====
def clean_html_text(text):
    """HTML 태그와 엔티티를 깨끗한 텍스트로 변환"""
    if not text:
        return text

    # HTML 엔티티 디코딩 (&nbsp; &amp; &quot; 등)
    text = html.unescape(text)

    # <br>, <br/>, <br /> 태그를 줄바꿈으로 변환
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    # <p> 태그를 줄바꿈으로 변환
    text = re.sub(r'</?p\s*/?>', '\n', text, flags=re.IGNORECASE)

    # 모든 HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)

    # 연속된 공백을 하나로
    text = re.sub(r' +', ' ', text)

    # 연속된 줄바꿈을 최대 2개로
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 앞뒤 공백 제거
    text = text.strip()

    return text


# ===== iOS App Store 크롤러 =====
def get_app_id_from_url(url_or_id):
    """URL 또는 ID에서 앱 ID 추출"""
    if url_or_id.isdigit():
        return url_or_id

    match = re.search(r'/id(\d+)', url_or_id)
    if match:
        return match.group(1)

    match = re.search(r'id=(\d+)', url_or_id)
    if match:
        return match.group(1)

    return None


def fetch_ios_reviews(app_id, target_count=100, progress_callback=None):
    """iOS App Store 리뷰 수집"""
    all_reviews = []
    seen_ids = set()

    countries = ["kr", "us", "jp", "gb", "au", "ca"]
    sort_options = ["mostrecent", "mosthelpful"]

    for country in countries:
        if len(all_reviews) >= target_count:
            break

        for sort_by in sort_options:
            if len(all_reviews) >= target_count:
                break

            for page in range(1, 11):
                if len(all_reviews) >= target_count:
                    break

                url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby={sort_by}/xml"

                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code != 200:
                        break

                    soup = BeautifulSoup(response.content, 'xml')
                    entries = soup.find_all('entry')

                    if len(entries) <= 1:
                        break

                    for entry in entries[1:]:
                        review_id = entry.find('id')
                        if review_id:
                            review_id = review_id.text
                            if review_id in seen_ids:
                                continue
                            seen_ids.add(review_id)

                        title_elem = entry.find('title')
                        content_elem = entry.find('content')
                        author_elem = entry.find('author')
                        rating_elem = entry.find('im:rating')
                        date_elem = entry.find('updated')

                        review = {
                            'title': title_elem.text if title_elem else '',
                            'content': content_elem.text if content_elem else '',
                            'author': author_elem.find('name').text if author_elem and author_elem.find('name') else '익명',
                            'rating': int(rating_elem.text) if rating_elem else 0,
                            'date': date_elem.text[:10] if date_elem else '',
                            'country': country
                        }

                        all_reviews.append(review)

                        if progress_callback:
                            progress_callback(len(all_reviews), target_count)

                        if len(all_reviews) >= target_count:
                            break

                    time.sleep(0.2)

                except Exception:
                    break

    return all_reviews[:target_count]


# ===== Google Play Store 크롤러 =====
def get_package_from_url(url_or_package):
    """URL 또는 패키지명에서 패키지 ID 추출"""
    if '.' in url_or_package and '/' not in url_or_package:
        return url_or_package

    match = re.search(r'id=([a-zA-Z0-9._]+)', url_or_package)
    if match:
        return match.group(1)

    return None


def fetch_android_reviews(package_id, target_count=100, progress_callback=None):
    """Google Play Store 리뷰 수집"""
    try:
        from google_play_scraper import reviews, Sort

        all_reviews = []
        continuation_token = None

        while len(all_reviews) < target_count:
            batch_size = min(200, target_count - len(all_reviews))

            result, continuation_token = reviews(
                package_id,
                lang='ko',
                country='kr',
                sort=Sort.NEWEST,
                count=batch_size,
                continuation_token=continuation_token
            )

            if not result:
                break

            for r in result:
                # HTML 태그/엔티티 정리 적용
                raw_content = r.get('content', '')
                cleaned_content = clean_html_text(raw_content)

                review = {
                    'content': cleaned_content,
                    'author': r.get('userName', '익명'),
                    'rating': r.get('score', 0),
                    'date': r.get('at', '').strftime('%Y-%m-%d') if r.get('at') else ''
                }
                all_reviews.append(review)

                if progress_callback:
                    progress_callback(len(all_reviews), target_count)

                if len(all_reviews) >= target_count:
                    break

            if not continuation_token:
                break

            time.sleep(0.3)

        return all_reviews[:target_count]

    except ImportError:
        st.error("google-play-scraper 패키지가 필요합니다.")
        return []
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
        return []


def generate_report(reviews, platform, app_id):
    """리뷰 보고서 텍스트 생성"""
    timestamp = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')
    platform_name = "iOS App Store" if platform == "ios" else "Google Play Store"

    report = f"""{'=' * 55}
    {platform_name} VoC 데이터 수집 보고서
{'=' * 55}

[수집 정보]
  - 앱 식별자: {app_id}
  - 수집 일시: {timestamp}
  - 수집 건수: {len(reviews)}건

{'-' * 55}

"""

    for idx, review in enumerate(reviews, 1):
        rating = int(review.get('rating', 0))
        star_display = "●" * rating + "○" * (5 - rating)

        report += f"#{idx}\n"
        report += f"  평점: {star_display} [{rating}/5]\n"
        if review.get('title'):
            report += f"  제목: {review.get('title')}\n"
        report += f"  리뷰: {review.get('content', '-')}\n"
        report += f"  작성자: {review.get('author', '익명')}\n"
        report += f"  날짜: {review.get('date', '-')}\n"
        if review.get('country') and review.get('country') != 'kr':
            report += f"  지역: {review.get('country').upper()}\n"
        report += "\n"

    report += f"{'-' * 55}\n"
    report += f"총 {len(reviews)}건의 VoC 데이터 수집 완료\n"

    return report


# ===== 메인 앱 =====
def main():
    # 세션 상태 초기화
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'platform' not in st.session_state:
        st.session_state.platform = None
    if 'reviews' not in st.session_state:
        st.session_state.reviews = []

    # 홈 페이지
    if st.session_state.page == 'home':
        show_home_page()

    # 크롤링 페이지
    elif st.session_state.page == 'crawl':
        show_crawl_page()

    # 결과 페이지
    elif st.session_state.page == 'result':
        show_result_page()


def show_home_page():
    """홈 페이지 표시"""
    st.markdown('<p class="main-title">📱 Mobile Review Collector</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">앱 스토어에서 사용자 리뷰를 수집하여<br>VoC 분석에 활용할 수 있습니다.</p>', unsafe_allow_html=True)
    st.markdown('<p class="brand-text">멋쟁이사자처럼 부트캠프용 VoC 크롤링</p>', unsafe_allow_html=True)

    st.markdown("### 수집할 스토어를 선택하세요")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem;">🍎</div>
            <h4 style="color: #0984E3; margin: 0.5rem 0;">Apple App Store</h4>
            <p style="color: #7F8C8D; font-size: 0.9rem;">iOS 앱 리뷰 수집</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("App Store 선택", key="ios_btn", type="primary", use_container_width=True):
            st.session_state.platform = 'ios'
            st.session_state.page = 'crawl'
            st.rerun()

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem;">▶️</div>
            <h4 style="color: #27AE60; margin: 0.5rem 0;">Google Play Store</h4>
            <p style="color: #7F8C8D; font-size: 0.9rem;">Android 앱 리뷰 수집</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Play Store 선택", key="android_btn", use_container_width=True):
            st.session_state.platform = 'android'
            st.session_state.page = 'crawl'
            st.rerun()


def show_crawl_page():
    """크롤링 페이지 표시"""
    platform = st.session_state.platform

    # 뒤로가기 버튼
    if st.button("← 뒤로"):
        st.session_state.page = 'home'
        st.session_state.reviews = []
        st.rerun()

    # 제목
    if platform == 'ios':
        st.markdown("## 🍎 App Store 리뷰 크롤링")
        placeholder = "예: https://apps.apple.com/kr/app/앱이름/id123456789 또는 123456789"
        color = "#0984E3"
    else:
        st.markdown("## ▶️ Play Store 리뷰 크롤링")
        placeholder = "예: https://play.google.com/store/apps/details?id=com.example.app 또는 com.example.app"
        color = "#27AE60"

    # 입력 폼
    app_input = st.text_input("앱 URL 또는 앱 ID 입력", placeholder=placeholder)

    review_count = st.slider("수집할 리뷰 개수", min_value=100, max_value=5000, value=500, step=100)

    # 수집 시작 버튼
    if st.button("🚀 리뷰 수집 시작", type="primary", use_container_width=True, disabled=not app_input):
        if platform == 'ios':
            app_id = get_app_id_from_url(app_input)
            if not app_id:
                st.error("올바른 App Store URL 또는 앱 ID를 입력해주세요.")
                return

            with st.spinner("App Store 리뷰를 수집하는 중..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(current, total):
                    progress = min(current / total, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"수집 중... {current}/{total}개")

                reviews = fetch_ios_reviews(app_id, review_count, update_progress)

                st.session_state.reviews = reviews
                st.session_state.app_id = app_id
                st.session_state.page = 'result'
                st.rerun()

        else:
            package_id = get_package_from_url(app_input)
            if not package_id:
                st.error("올바른 Play Store URL 또는 패키지명을 입력해주세요.")
                return

            with st.spinner("Play Store 리뷰를 수집하는 중..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(current, total):
                    progress = min(current / total, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"수집 중... {current}/{total}개")

                reviews = fetch_android_reviews(package_id, review_count, update_progress)

                st.session_state.reviews = reviews
                st.session_state.app_id = package_id
                st.session_state.page = 'result'
                st.rerun()


def show_result_page():
    """결과 페이지 표시"""
    reviews = st.session_state.reviews
    platform = st.session_state.platform
    app_id = st.session_state.get('app_id', '')

    # 뒤로가기 버튼
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← 뒤로"):
            st.session_state.page = 'crawl'
            st.rerun()

    with col2:
        if st.button("🏠 홈으로"):
            st.session_state.page = 'home'
            st.session_state.reviews = []
            st.rerun()

    # 결과 요약
    st.success(f"✅ 총 {len(reviews)}개의 리뷰를 수집했습니다!")

    # 다운로드 버튼
    report = generate_report(reviews, platform, app_id)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{'appstore' if platform == 'ios' else 'playstore'}_voc_{app_id}_{timestamp}.txt"

    st.download_button(
        label="📥 리뷰 데이터 다운로드 (TXT)",
        data=report,
        file_name=filename,
        mime="text/plain",
        use_container_width=True
    )

    # 리뷰 미리보기
    st.markdown("### 📋 수집된 리뷰 미리보기")

    # 필터
    col1, col2 = st.columns(2)
    with col1:
        rating_filter = st.selectbox("평점 필터", ["전체", "5점", "4점", "3점", "2점", "1점"])
    with col2:
        sort_order = st.selectbox("정렬", ["최신순", "평점 높은순", "평점 낮은순"])

    # 필터링
    filtered_reviews = reviews.copy()
    if rating_filter != "전체":
        rating_val = int(rating_filter[0])
        filtered_reviews = [r for r in filtered_reviews if r.get('rating') == rating_val]

    # 정렬
    if sort_order == "평점 높은순":
        filtered_reviews.sort(key=lambda x: x.get('rating', 0), reverse=True)
    elif sort_order == "평점 낮은순":
        filtered_reviews.sort(key=lambda x: x.get('rating', 0))

    # 리뷰 표시 (최대 50개)
    for i, review in enumerate(filtered_reviews[:50]):
        rating = review.get('rating', 0)
        stars = "⭐" * rating + "☆" * (5 - rating)

        with st.container():
            st.markdown(f"""
            <div class="review-box">
                <span class="review-rating">{stars}</span>
                <span style="color: #7F8C8D; font-size: 0.9rem;"> ({rating}/5)</span>
                {f'<p style="font-weight: 600; margin: 0.3rem 0;">{review.get("title")}</p>' if review.get('title') else ''}
                <p class="review-content">{review.get('content', '-')}</p>
                <p class="review-meta">👤 {review.get('author', '익명')} · 📅 {review.get('date', '-')}</p>
            </div>
            """, unsafe_allow_html=True)

    if len(filtered_reviews) > 50:
        st.info(f"📌 전체 {len(filtered_reviews)}개 중 50개만 미리보기로 표시됩니다. 전체 데이터는 다운로드 해주세요.")


if __name__ == "__main__":
    main()
