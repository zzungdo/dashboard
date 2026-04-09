# 이미지 검사 부분
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def compute_md5(path):
    """파일의 MD5 해시 계산"""
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def compare_images_md5(image_folder):
    """MD5 기반 완전 중복 탐지"""
    data = parallel_md5_compute(image_folder)
    results = []

    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            a, b = data[i], data[j]
            if a["md5"] == b["md5"]:
                results.append(
                    {
                        "image_a": a["filename"],
                        "image_b": b["filename"],
                        "note": "완전 중복",
                    }
                )

    print(f"[INFO] 완전 중복 {len(results)}건 탐지 완료")
    return sorted(results, key=lambda x: x["image_a"])

def process_image_md5(path):
    """단일 이미지 MD5 계산"""
    try:
        md5 = compute_md5(path)
        return {"filename": os.path.basename(path), "md5": md5}
    except Exception:
        return None

def parallel_md5_compute(image_folder, max_workers=8):
    """폴더 내 이미지들의 MD5 해시 병렬 계산"""
    files = [
        f
        for f in os.listdir(image_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {
            exe.submit(process_image_md5, os.path.join(image_folder, f)): f
            for f in files
        }
        for fut in tqdm(
            as_completed(futures), total=len(futures), desc="Computing MD5"
        ):
            result = fut.result()
            if result:
                results.append(result)
    return results
