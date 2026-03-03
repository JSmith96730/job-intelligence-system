import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm

# ==========================
# 설정
# ==========================

INPUT_CSV = "companies.csv"
OUTPUT_CSV = "greenhouse_results.csv"

HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10


# ==========================
# Careers 페이지 찾기
# ==========================

def find_careers_page(base_url):
    try:
        r = requests.get(base_url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(r.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            if any(keyword in href for keyword in ["career", "job", "join", "work"]):
                return urljoin(base_url, link["href"])

    except Exception:
        return None

    return None


# ==========================
# Greenhouse slug 추출
# ==========================

def extract_greenhouse_slug(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        html = r.text

        # 패턴 1: 일반 링크 또는 iframe
        match = re.search(r"boards\.greenhouse\.io/([a-zA-Z0-9\-]+)", html)
        if match:
            return match.group(1)

        # 패턴 2: embed script
        match = re.search(r"job_board/js\?for=([a-zA-Z0-9\-]+)", html)
        if match:
            return match.group(1)

    except Exception:
        return None

    return None

# ==========================
# Generate slug
# ==========================

def generate_slug(company_name):
    """회사명 → slug 변환"""
    slug = company_name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug

# ==========================
# Slug 검증
# ==========================

def validate_slug(slug):
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}"
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        return r.status_code == 200
    except:
        return False


# ==========================
# 메인 실행
# ==========================

def run_pipeline():
    df = pd.read_csv(INPUT_CSV)

    results = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        company_name = row["company_name"]
        website = row["website"]

        status = "Not Found"
        slug = None
        careers_page = None

        # 1️⃣ Careers 페이지 찾기
        careers_page = find_careers_page(website)
        if not careers_page:
            status = "No Careers Page"
        else:
            # 2️⃣ Greenhouse slug 추출
            slug = extract_greenhouse_slug(careers_page)
            if not slug:
                slug = generate_slug(company_name)

            # 3️⃣ API 검증
            if validate_slug(slug):
                status = "Valid"
            else:
                status = "Slug Invalid"

        results.append({
            "company_name": company_name,
            "website": website,
            "careers_page": careers_page,
            "greenhouse_slug": slug,
            "status": status
        })

    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n완료: {OUTPUT_CSV} 생성됨")


if __name__ == "__main__":
    run_pipeline()