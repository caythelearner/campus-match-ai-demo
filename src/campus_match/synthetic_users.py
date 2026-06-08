from __future__ import annotations

import random
from typing import Any


INTERESTS = [
    "羽毛球", "网球", "健身", "跑步", "骑行", "Citywalk", "摄影", "独立电影", "剧本杀",
    "桌游", "咖啡", "烘焙", "猫", "狗", "旅行", "露营", "音乐节", "古典音乐", "爵士",
    "阅读", "心理学", "商业分析", "AI", "编程", "游戏", "动漫", "美术馆", "博物馆",
    "志愿活动", "辩论", "脱口秀", "Livehouse", "舞蹈", "瑜伽", "足球", "篮球"
]

VALUES = [
    "真诚", "边界感", "稳定", "成长型关系", "幽默感", "长期主义", "共同进步", "尊重差异",
    "情绪稳定", "高质量陪伴", "独立空间", "坦诚沟通", "责任感", "松弛感", "安全感"
]

DEAL_BREAKERS = [
    "过度控制", "情绪勒索", "不守时", "冷暴力", "频繁失联", "不尊重边界", "消费观冲突",
    "不诚实", "酒局过多", "作息完全相反", "强迫社交", "缺乏责任感"
]

MAJORS = [
    "信息管理", "工商管理", "金融", "经济学", "计算机科学", "新闻传播", "社会学",
    "心理学", "数学", "统计学", "法学", "中文", "外语", "医学", "环境科学"
]

SCHOOLS = ["管理学院", "经济学院", "计算机学院", "新闻学院", "社会发展学院", "法学院", "文学院", "医学院"]
CAMPUSES = ["邯郸校区", "江湾校区", "枫林校区", "张江校区"]
GRADES = ["大一", "大二", "大三", "大四", "研一", "研二"]
GENDERS = ["female", "male"]
GOALS = ["长期关系", "认真了解", "先交朋友", "轻松社交"]
COMMUNICATION_STYLES = ["慢热但深入", "高频分享", "直接坦诚", "温和倾听", "外向主动", "尊重空间"]
DATE_PREFS = ["咖啡馆", "电影", "散步", "运动", "看展", "音乐现场", "图书馆学习", "校园活动", "周末短途"]


def _sample(rng: random.Random, pool: list[str], min_n: int, max_n: int) -> list[str]:
    return rng.sample(pool, rng.randint(min_n, max_n))


def _preferred_gender(rng: random.Random, gender: str) -> str:
    options = ["female", "male", "any"]
    weights = [0.45, 0.45, 0.10]
    if gender == "female":
        weights = [0.08, 0.84, 0.08]
    if gender == "male":
        weights = [0.84, 0.08, 0.08]
    return rng.choices(options, weights=weights, k=1)[0]


def generate_user(index: int, rng: random.Random) -> dict[str, Any]:
    gender = rng.choice(GENDERS)
    interests = _sample(rng, INTERESTS, 4, 7)
    values = _sample(rng, VALUES, 3, 5)
    deal_breakers = _sample(rng, DEAL_BREAKERS, 2, 4)
    communication_style = rng.choice(COMMUNICATION_STYLES)
    goal = rng.choice(GOALS)
    date_prefs = _sample(rng, DATE_PREFS, 2, 4)
    personality = _sample(
        rng,
        ["内向", "外向", "文艺", "理性", "感性", "计划型", "随性", "幽默", "安静", "探索欲强", "自律"],
        2,
        4,
    )

    intro_templates = [
        "我平时喜欢{interest_text}，性格偏{personality_text}，在关系里比较看重{value_text}。",
        "课余时间常做{interest_text}，朋友说我{personality_text}。希望相处时能保持{value_text}。",
        "我是一个喜欢{interest_text}的人，沟通风格是{comm}，更期待{goal}。",
    ]
    ideal_templates = [
        "希望对方也重视{value_text}，可以一起{date_text}，不太能接受{breaker_text}。",
        "理想的相处是舒服、真诚、有边界，最好能一起{date_text}，关系目标偏{goal}。",
        "希望遇到愿意认真沟通的人，喜欢{date_text}，并且能尊重彼此的节奏。",
    ]

    data = {
        "user_id": f"U{index:03d}",
        "display_name": f"匿名用户{index:03d}",
        "age": rng.randint(18, 25),
        "gender": gender,
        "preferred_gender": _preferred_gender(rng, gender),
        "school": rng.choice(SCHOOLS),
        "major": rng.choice(MAJORS),
        "grade": rng.choice(GRADES),
        "campus": rng.choice(CAMPUSES),
        "relationship_goal": goal,
        "interests": interests,
        "values": values,
        "communication_style": communication_style,
        "personality_tags": personality,
        "available_time": _sample(rng, ["周一晚上", "周三晚上", "周五晚上", "周六下午", "周六晚上", "周日下午"], 2, 3),
        "preferred_date": date_prefs,
        "deal_breakers": deal_breakers,
    }
    data["self_intro"] = rng.choice(intro_templates).format(
        interest_text="、".join(interests[:3]),
        personality_text="、".join(personality[:2]),
        value_text="、".join(values[:3]),
        comm=communication_style,
        goal=goal,
    )
    data["ideal_partner"] = rng.choice(ideal_templates).format(
        value_text="、".join(values[:3]),
        date_text="、".join(date_prefs[:2]),
        breaker_text="、".join(deal_breakers[:2]),
        goal=goal,
    )
    return data


def generate_users(n_users: int = 120, seed: int = 42) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    return [generate_user(i + 1, rng) for i in range(n_users)]
