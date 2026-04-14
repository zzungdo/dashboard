# Dataset Dashboard

Python/Dash 기반의 데이터셋 분석 및 품질 점검 대시보드입니다.  
이미지와 GT 데이터를 불러와 클래스 분포, 해상도, 중복 박스, 산점도/히트맵 등 다양한 지표를 시각화하여  
데이터셋의 현황을 빠르게 파악하고 검수 효율을 높이기 위해 만들었습니다.

## Overview

데이터셋 구축 및 검수 과정에서는  
- 클래스 불균형
- 해상도 편차
- 중복 또는 이상한 바운딩박스
- 이미지별 라벨 분포 차이  
같은 문제를 빠르게 확인하는 일이 중요합니다.

이 프로젝트는 이런 반복적인 확인 작업을 대시보드로 통합해  
데이터 품질 점검과 현황 파악을 더 쉽게 하도록 만든 도구입니다.

## Key Features

- 클래스별 분포 및 비율 시각화
- 이미지 해상도 분포 확인
- 산점도 및 히트맵 기반 GT 분포 분석
- 이미지 단위 GT 확인
- 중복 바운딩박스 탐지
- 데이터셋 상태를 한 화면에서 확인할 수 있는 대시보드 제공

## Tech Stack

- Python
- Dash
- Plotly
- Pandas

## Project Structure

```bash
dashboard/
├─ app.py
├─ layout.py
├─ assets/
├─ callbacks/
├─ tabs/
└─ utils/
