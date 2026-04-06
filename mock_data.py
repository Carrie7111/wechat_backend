# -*- coding: utf-8 -*-
"""
模拟数据源（内存），无真实数据库，服务重启后数据重置。
果树花 + 油菜花七类统一：flowerKey 与花期预测、地图、路线、讲解一致（中文键）。
"""
from datetime import datetime, timedelta
import os

# 七种：可结果果树花 + 油菜花（经济作物）；key 与 predict 衍生 flowerKey 一致
FLOWER_SPECIES = [
    {"key": "桃花", "name": "桃花", "color": "#ff7a7c"},
    {"key": "梨花", "name": "梨花", "color": "#c8d4e8"},
    {"key": "樱桃花", "name": "樱桃花", "color": "#ffb7c5"},
    {"key": "李花", "name": "李花", "color": "#f5f0ff"},
    {"key": "枇杷花", "name": "枇杷花", "color": "#fff3e0"},
    {"key": "柑橘花", "name": "柑橘花", "color": "#fffde7"},
    {"key": "油菜花", "name": "油菜花", "color": "#f4d03f"},
]

FLOWER_AI_HINTS = {
    "桃花": "龙泉驿水蜜桃产区，花期多3–4月。宜俯拍花海层次，长焦压缩景深；农旅园区注意错峰与步道安全。",
    "梨花": "川内梨树经济林集中区，花期略早于桃。宜拍花序与田园肌理，雨后注意防滑。",
    "樱桃花": "樱桃果树开花（非观赏樱花），与座果相关。宜晴天上午观花，忌暴雨冲刷花粉。",
    "李花": "脆李等主产区春季白花成片。宜拍疏朗花枝，田间观光勿攀折。",
    "枇杷花": "秋冬至早春开花，与春季桃李错季。园区多近郊丘陵，注意缓坡行走。",
    "柑橘花": "春季柑橘花香浓郁，关系当年产量。宜拍花叶同框，勿擅摘幼果。",
    "油菜花": "冬油菜春季金黄，兼具油用与观光。宜低机位衬蓝天，爱护田埂勿碾压作物。",
}

BANNERS = [
    {"id": 1, "image": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=800&q=80", "linkSpotId": 1, "title": "龙泉山桃花"},
    {"id": 2, "image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&q=80", "linkSpotId": 5, "title": "简阳樱桃花沟"},
    {"id": 3, "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80", "linkSpotId": 13, "title": "崇州油菜花海"},
]

FLOWER_PHASES = [
    {"key": "budding", "name": "萌芽期", "desc": "桃李梨李枇杷柑橘等果树芽萌动，油菜冬前苗期转入返青。", "progress": 15},
    {"key": "early_bloom", "name": "初花期", "desc": "枇杷等早花树种与部分李梨进入初花，宜关注倒春寒。", "progress": 35},
    {"key": "peak_bloom", "name": "盛花期", "desc": "桃、梨、樱桃、李、柑橘与油菜等进入最佳观赏与农事窗口。", "progress": 75},
    {"key": "late_fall", "name": "落花末期", "desc": "春花渐谢，幼果形成，油菜进入角果期。", "progress": 92},
    {"key": "wither", "name": "休养期", "desc": "花谢果长，园区转入抚育与病虫害统防。", "progress": 100},
]

CROWD_LEVEL_COLOR = {
    "少": "#52c41a",
    "中": "#1890ff",
    "多": "#fa8c16",
    "爆满": "#f5222d",
}

# 人流量：花种 → 多个景区（二级结构，演示数据）
CROWD_FLOWER_GROUPS = [
    {
        "flowerKey": "桃花",
        "flowerName": "桃花",
        "spots": [
            {
                "spotName": "龙泉山城市森林公园桃源",
                "crowdLevel": "多",
                "percent": 76,
                "description": "主路车流大，周末午后拥挤，建议公共交通或错峰。",
            },
            {
                "spotName": "桃花故里观景台",
                "crowdLevel": "中",
                "percent": 58,
                "description": "观景台步道适中，上午人流相对较少。",
            },
        ],
    },
    {
        "flowerKey": "梨花",
        "flowerName": "梨花",
        "spots": [
            {
                "spotName": "新津梨花溪风景区",
                "crowdLevel": "中",
                "percent": 52,
                "description": "河谷梨花带，周末亲子游略多。",
            },
            {
                "spotName": "金堂栖贤梨花沟",
                "crowdLevel": "少",
                "percent": 34,
                "description": "近郊分散，停车压力较小。",
            },
        ],
    },
    {
        "flowerKey": "樱桃花",
        "flowerName": "樱桃花",
        "spots": [
            {
                "spotName": "简阳樱桃沟旅游区",
                "crowdLevel": "多",
                "percent": 68,
                "description": "农旅热点，采摘季与花期重叠时车流集中。",
            },
            {
                "spotName": "蒲江光明樱桃山",
                "crowdLevel": "中",
                "percent": 49,
                "description": "山地步道，宜早间入园。",
            },
        ],
    },
    {
        "flowerKey": "李花",
        "flowerName": "李花",
        "spots": [
            {
                "spotName": "青白江李子产业园观花带",
                "crowdLevel": "少",
                "percent": 28,
                "description": "产业道路较宽，人流分散。",
            },
            {
                "spotName": "彭州葛仙山李花林",
                "crowdLevel": "中",
                "percent": 45,
                "description": "丘陵花带，周末摄影团略多。",
            },
        ],
    },
    {
        "flowerKey": "枇杷花",
        "flowerName": "枇杷花",
        "spots": [
            {
                "spotName": "双流枇杷采摘园片区",
                "crowdLevel": "少",
                "percent": 31,
                "description": "错季开花，观光与采摘分流，人流平稳。",
            },
            {
                "spotName": "龙泉驿枇杷基地观光点",
                "crowdLevel": "中",
                "percent": 44,
                "description": "与桃园相邻，节假日联动车流需注意。",
            },
        ],
    },
    {
        "flowerKey": "柑橘花",
        "flowerName": "柑橘花",
        "spots": [
            {
                "spotName": "蒲江丑柑产业园花海径",
                "crowdLevel": "中",
                "percent": 55,
                "description": "园区道路较窄，建议单向游览。",
            },
            {
                "spotName": "金堂三溪柑橘观光园",
                "crowdLevel": "少",
                "percent": 36,
                "description": "滨江柑橘带，步道开阔。",
            },
        ],
    },
    {
        "flowerKey": "油菜花",
        "flowerName": "油菜花",
        "spots": [
            {
                "spotName": "金堂三溪油菜花海",
                "crowdLevel": "中",
                "percent": 48,
                "description": "河谷花田视野好，周末自驾略多。",
            },
            {
                "spotName": "崇州重庆路油菜花带",
                "crowdLevel": "多",
                "percent": 72,
                "description": "公路沿线打卡热，注意靠边停车与安全。",
            },
        ],
    },
]


def crowd_flow_payload():
    """花 → 多景区，每条景区附加 color。"""
    rows = []
    for g in CROWD_FLOWER_GROUPS:
        item = {"flowerKey": g["flowerKey"], "flowerName": g["flowerName"], "spots": []}
        for s in g.get("spots", []):
            sc = dict(s)
            lv = sc.get("crowdLevel") or ""
            sc["color"] = CROWD_LEVEL_COLOR.get(lv, "#999999")
            item["spots"].append(sc)
        rows.append(item)
    return rows


# 成都全市赏花点（示意坐标）；每景区仅归属一种主花卉（flowerKey 为中文）
ATTRACTIONS = [
    {"id": 1, "flowerKey": "桃花", "name": "龙泉山城市森林公园桃源", "lat": 30.650, "lng": 104.280,
     "cover": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=600&q=80",
     "tags": ["桃花", "全景"], "brief": "千亩桃林，春季成都经典赏花地。", "openTime": "08:30-18:00"},
    {"id": 2, "flowerKey": "桃花", "name": "桃花故里观景台", "lat": 30.642, "lng": 104.275,
     "cover": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=600&q=80",
     "tags": ["打卡", "摄影"], "brief": "制高点俯瞰花海，长焦友好。", "openTime": "09:00-18:00"},
    {"id": 3, "flowerKey": "梨花", "name": "新津梨花溪风景区", "lat": 30.428, "lng": 103.811,
     "cover": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&q=80",
     "tags": ["梨花", "亲水"], "brief": "河谷梨花与溪流相映。", "openTime": "09:00-17:30"},
    {"id": 4, "flowerKey": "梨花", "name": "金堂栖贤梨花沟", "lat": 30.758, "lng": 104.612,
     "cover": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&q=80",
     "tags": ["梨花", "徒步"], "brief": "丘陵梨花带，空气清新。", "openTime": "全天开放"},
    {"id": 5, "flowerKey": "樱桃花", "name": "简阳樱桃沟旅游区", "lat": 30.495, "lng": 104.548,
     "cover": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=600&q=80",
     "tags": ["樱桃花", "采摘"], "brief": "果树樱桃花期与采摘季衔接。", "openTime": "08:30-18:00"},
    {"id": 6, "flowerKey": "樱桃花", "name": "蒲江光明樱桃山", "lat": 30.192, "lng": 103.506,
     "cover": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600&q=80",
     "tags": ["樱桃花", "山地"], "brief": "梯田式樱桃园，花期层次丰富。", "openTime": "09:00-18:00"},
    {"id": 7, "flowerKey": "李花", "name": "青白江李子产业园观花带", "lat": 30.884, "lng": 104.254,
     "cover": "https://images.unsplash.com/photo-1604977042232-bf6d5eedbeb4?w=600&q=80",
     "tags": ["李花", "产业"], "brief": "脆李主产区春季白花连片。", "openTime": "08:00-18:00"},
    {"id": 8, "flowerKey": "李花", "name": "彭州葛仙山李花林", "lat": 31.098, "lng": 103.892,
     "cover": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=600&q=80",
     "tags": ["李花", "登山"], "brief": "丘陵李花与步道结合。", "openTime": "08:30-17:30"},
    {"id": 9, "flowerKey": "枇杷花", "name": "双流枇杷采摘园片区", "lat": 30.573, "lng": 103.923,
     "cover": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=600&q=80",
     "tags": ["枇杷花", "近郊"], "brief": "秋冬至早春观花，春夏采摘衔接。", "openTime": "09:00-17:00"},
    {"id": 10, "flowerKey": "枇杷花", "name": "龙泉驿枇杷基地观光点", "lat": 30.638, "lng": 104.268,
     "cover": "https://images.unsplash.com/photo-1520763185298-1b434c919102?w=600&q=80",
     "tags": ["枇杷花", "农旅"], "brief": "与桃园片区相邻，可串联游览。", "openTime": "08:30-18:00"},
    {"id": 11, "flowerKey": "柑橘花", "name": "蒲江丑柑产业园花海径", "lat": 30.196, "lng": 103.505,
     "cover": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600&q=80",
     "tags": ["柑橘花", "花香"], "brief": "春季柑橘花香浓郁，产业景观道。", "openTime": "08:00-18:00"},
    {"id": 12, "flowerKey": "柑橘花", "name": "金堂三溪柑橘观光园", "lat": 30.858, "lng": 104.612,
     "cover": "https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?w=600&q=80",
     "tags": ["柑橘花", "滨江"], "brief": "沿江柑橘带，花期满园清香。", "openTime": "全天开放"},
    {"id": 13, "flowerKey": "油菜花", "name": "金堂三溪油菜花海", "lat": 30.860, "lng": 104.615,
     "cover": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600&q=80",
     "tags": ["油菜花", "田园"], "brief": "河谷成片金黄，花期较长。", "openTime": "全天开放"},
    {"id": 14, "flowerKey": "油菜花", "name": "崇州重庆路油菜花带", "lat": 30.630, "lng": 103.672,
     "cover": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=600&q=80",
     "tags": ["油菜花", "自驾"], "brief": "公路沿线花带，注意安全停车。", "openTime": "全天开放"},
    {"id": 15, "flowerKey": "桃花", "name": "洛带古镇周边桃园", "lat": 30.638, "lng": 104.298,
     "cover": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=600&q=80",
     "tags": ["桃花", "古镇"], "brief": "客家古镇与近郊桃林可一日串联。", "openTime": "08:30-18:00"},
    {"id": 16, "flowerKey": "桃花", "name": "山泉镇桃花沟步道", "lat": 30.628, "lng": 104.265,
     "cover": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=600&q=80",
     "tags": ["桃花", "徒步"], "brief": "沿山步道穿行桃林，适合慢行。", "openTime": "09:00-17:30"},
    {"id": 17, "flowerKey": "桃花", "name": "同安街道万亩桃园", "lat": 30.655, "lng": 104.288,
     "cover": "https://images.unsplash.com/photo-1604977042232-bf6d5eedbeb4?w=600&q=80",
     "tags": ["桃花", "自驾"], "brief": "连片桃海，花季周末车流大建议早到。", "openTime": "08:00-18:00"},
    {"id": 18, "flowerKey": "桃花", "name": "茶店镇观光桃园", "lat": 30.618, "lng": 104.252,
     "cover": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&q=80",
     "tags": ["桃花", "亲子"], "brief": "近龙泉城区，配套农家乐较多。", "openTime": "08:30-18:00"},
    {"id": 19, "flowerKey": "梨花", "name": "都江堰天马镇梨园", "lat": 31.015, "lng": 103.658,
     "cover": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&q=80",
     "tags": ["梨花", "田园"], "brief": "坝区梨园与林盘院落相映。", "openTime": "09:00-17:00"},
    {"id": 20, "flowerKey": "梨花", "name": "温江和盛镇梨花带", "lat": 30.712, "lng": 103.818,
     "cover": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&q=80",
     "tags": ["梨花", "近郊"], "brief": "成都西向近郊，半日往返方便。", "openTime": "全天开放"},
    {"id": 21, "flowerKey": "梨花", "name": "崇州白头镇梨园观光区", "lat": 30.598, "lng": 103.702,
     "cover": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=600&q=80",
     "tags": ["梨花", "摄影"], "brief": "川西林盘与梨花结合，宜拍人文风光。", "openTime": "08:30-18:00"},
    {"id": 22, "flowerKey": "樱桃花", "name": "成都东部新区石板凳街道樱桃沟", "lat": 30.448, "lng": 104.562,
     "cover": "https://images.unsplash.com/photo-1528821128474-27f963b062bf?w=600&q=80",
     "tags": ["樱桃花", "山地"], "brief": "龙泉山东麓樱桃主产区之一，花季可结合采摘体验。", "openTime": "08:30-18:00"},
    {"id": 23, "flowerKey": "樱桃花", "name": "简阳贾家镇樱桃沟", "lat": 30.452, "lng": 104.482,
     "cover": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600&q=80",
     "tags": ["樱桃花", "采摘"], "brief": "成都东向经典樱桃产区，花季可预约入园。", "openTime": "09:00-17:30"},
    {"id": 24, "flowerKey": "樱桃花", "name": "青白江区福洪镇樱桃采摘园", "lat": 30.782, "lng": 104.382,
     "cover": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=600&q=80",
     "tags": ["樱桃花", "研学"], "brief": "龙泉山脉西麓，春季樱桃花与农旅活动集中。", "openTime": "08:00-18:00"},
    {"id": 25, "flowerKey": "李花", "name": "大邑雾中山李花观赏区", "lat": 30.582, "lng": 103.378,
     "cover": "https://images.unsplash.com/photo-1604977042232-bf6d5eedbeb4?w=600&q=80",
     "tags": ["李花", "山地"], "brief": "海拔略高，李花层次与云雾同框。", "openTime": "08:30-17:00"},
    {"id": 26, "flowerKey": "李花", "name": "邛崃南宝山李花带", "lat": 30.358, "lng": 103.248,
     "cover": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=600&q=80",
     "tags": ["李花", "自驾"], "brief": "沿山公路分布，注意弯道与停车。", "openTime": "全天开放"},
    {"id": 27, "flowerKey": "李花", "name": "彭州通济镇李园", "lat": 31.128, "lng": 103.892,
     "cover": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&q=80",
     "tags": ["李花", "避暑"], "brief": "山区气候凉爽，花期略晚于坝区。", "openTime": "09:00-17:30"},
    {"id": 28, "flowerKey": "枇杷花", "name": "新津花源镇枇杷园", "lat": 30.438, "lng": 103.835,
     "cover": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=600&q=80",
     "tags": ["枇杷花", "滨河"], "brief": "近南河湿地，冬春观花体验佳。", "openTime": "09:00-17:00"},
    {"id": 29, "flowerKey": "枇杷花", "name": "双流区永安镇枇杷基地", "lat": 30.518, "lng": 103.882,
     "cover": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=600&q=80",
     "tags": ["枇杷花", "产业"], "brief": "牧马山片区枇杷种植集中，冬春之交花香浓郁。", "openTime": "08:30-18:00"},
    {"id": 30, "flowerKey": "枇杷花", "name": "天府新区永兴枇杷观光点", "lat": 30.412, "lng": 104.118,
     "cover": "https://images.unsplash.com/photo-1520763185298-1b434c919102?w=600&q=80",
     "tags": ["枇杷花", "近郊"], "brief": "城南近郊，可与兴隆湖行程组合。", "openTime": "09:00-18:00"},
    {"id": 31, "flowerKey": "柑橘花", "name": "蒲江长滩湖柑橘景观带", "lat": 30.215, "lng": 103.458,
     "cover": "https://images.unsplash.com/photo-1547514701-42782101795e?w=600&q=80",
     "tags": ["柑橘花", "湖景"], "brief": "湖光与柑橘园相间，春季花香浓郁。", "openTime": "08:00-18:00"},
    {"id": 32, "flowerKey": "柑橘花", "name": "金堂县五凤镇柑橘产业园", "lat": 30.718, "lng": 104.678,
     "cover": "https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?w=600&q=80",
     "tags": ["柑橘花", "产业"], "brief": "沱江峡谷两岸柑橘林，春季花香与古镇游可串联。", "openTime": "08:30-17:30"},
    {"id": 33, "flowerKey": "柑橘花", "name": "邛崃夹关镇柑橘园", "lat": 30.328, "lng": 103.312,
     "cover": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600&q=80",
     "tags": ["柑橘花", "茶马古道"], "brief": "古镇周边柑橘林，文化游与观花结合。", "openTime": "09:00-17:00"},
    {"id": 34, "flowerKey": "油菜花", "name": "邛崃冉义镇万亩油菜花", "lat": 30.402, "lng": 103.458,
     "cover": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600&q=80",
     "tags": ["油菜花", "田园"], "brief": "平坝大田连片金黄，航拍友好。", "openTime": "全天开放"},
    {"id": 35, "flowerKey": "油菜花", "name": "郫都唐昌镇油菜花田", "lat": 30.858, "lng": 103.878,
     "cover": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=600&q=80",
     "tags": ["油菜花", "近郊"], "brief": "成都西北近郊，公交自驾均可。", "openTime": "全天开放"},
    {"id": 36, "flowerKey": "油菜花", "name": "新都清流镇油菜花海", "lat": 30.782, "lng": 104.082,
     "cover": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=600&q=80",
     "tags": ["油菜花", "亲子"], "brief": "田园步道平缓，适合家庭出游。", "openTime": "08:00-18:00"},
    {"id": 37, "flowerKey": "梨花", "name": "彭州市桂花镇梨花沟", "lat": 31.052, "lng": 103.928,
     "cover": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&q=80",
     "tags": ["梨花", "山地"], "brief": "浅丘梨园与山间步道，春季梨花成片。", "openTime": "09:00-17:00"},
    {"id": 38, "flowerKey": "樱桃花", "name": "蒲江县大兴镇樱桃园", "lat": 30.218, "lng": 103.528,
     "cover": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600&q=80",
     "tags": ["樱桃花", "节庆"], "brief": "蒲江樱桃主产区之一，花季常与樱桃节活动结合。", "openTime": "08:30-18:00"},
    {"id": 39, "flowerKey": "李花", "name": "崇州市道明镇李花观赏区", "lat": 30.592, "lng": 103.648,
     "cover": "https://images.unsplash.com/photo-1604977042232-bf6d5eedbeb4?w=600&q=80",
     "tags": ["李花", "林盘"], "brief": "川西林盘与脆李花田相间，宜慢行拍照。", "openTime": "08:30-18:00"},
    {"id": 40, "flowerKey": "枇杷花", "name": "双流区黄龙溪古镇枇杷园片区", "lat": 30.318, "lng": 103.968,
     "cover": "https://images.unsplash.com/photo-1520763185298-1b434c919102?w=600&q=80",
     "tags": ["枇杷花", "古镇"], "brief": "古镇周边枇杷林，冬春观花与古镇游一体。", "openTime": "08:30-18:00"},
    {"id": 41, "flowerKey": "柑橘花", "name": "都江堰市柳街镇柑橘观光带", "lat": 30.852, "lng": 103.628,
     "cover": "https://images.unsplash.com/photo-1547514701-42782101795e?w=600&q=80",
     "tags": ["柑橘花", "田园"], "brief": "坝区柑橘林与田园景观道，春季花香扑鼻。", "openTime": "08:00-18:00"},
    {"id": 42, "flowerKey": "桃花", "name": "成都市植物园桃花专类园", "lat": 30.708, "lng": 104.148,
     "cover": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=600&q=80",
     "tags": ["桃花", "市区"], "brief": "城区公共交通直达，适合半日观花与亲子。", "openTime": "08:30-17:00"},
]

# 商城：按对应果实分类（categoryId 稳定供前端筛选）
MALL_CATEGORIES = [
    {"id": "fruit_peach", "name": "桃"},
    {"id": "fruit_pear", "name": "梨"},
    {"id": "fruit_cherry", "name": "樱桃"},
    {"id": "fruit_plum", "name": "李"},
    {"id": "fruit_loquat", "name": "枇杷"},
    {"id": "fruit_citrus", "name": "柑橘"},
    {"id": "oil_rapeseed", "name": "菜籽油"},
]

PRODUCTS = [
    {
        "id": 101,
        "categoryId": "fruit_peach",
        "name": "龙泉驿水蜜桃（礼盒）",
        "price": 39.9,
        "unit": "箱/5斤",
        "cover": "https://images.unsplash.com/photo-1604977042232-bf6d5eedbeb4?w=600&q=80",
        "stock": 200,
        "desc": "清晨采摘，冷链到家，香甜多汁。",
    },
    {
        "id": 102,
        "categoryId": "fruit_peach",
        "name": "黄桃切块即食装",
        "price": 28.0,
        "unit": "盒/500g",
        "cover": "https://images.unsplash.com/photo-1629828874514-d05f8589f7a8?w=600&q=80",
        "stock": 120,
        "desc": "开袋即食，出游便携。",
    },
    {
        "id": 103,
        "categoryId": "fruit_pear",
        "name": "金堂丰水梨",
        "price": 32.0,
        "unit": "箱/5斤",
        "cover": "https://images.unsplash.com/photo-1514756331096-242fdeb70d04?w=600&q=80",
        "stock": 150,
        "desc": "脆甜多汁，冷藏更佳。",
    },
    {
        "id": 104,
        "categoryId": "fruit_pear",
        "name": "雪梨银耳炖品套装",
        "price": 45.0,
        "unit": "套",
        "cover": "https://images.unsplash.com/photo-1596040033229-a98c47c6e77e?w=600&q=80",
        "stock": 80,
        "desc": "炖品搭配，润燥养颜。",
    },
    {
        "id": 105,
        "categoryId": "fruit_cherry",
        "name": "简阳大樱桃（果径分级）",
        "price": 88.0,
        "unit": "盒/1斤",
        "cover": "https://images.unsplash.com/photo-1528821128474-27f963b062bf?w=600&q=80",
        "stock": 90,
        "desc": "冷链锁鲜，酸甜适口。",
    },
    {
        "id": 106,
        "categoryId": "fruit_cherry",
        "name": "樱桃果酱",
        "price": 35.0,
        "unit": "瓶/220g",
        "cover": "https://images.unsplash.com/photo-1559181567-c3190ca9959b?w=600&q=80",
        "stock": 200,
        "desc": "低糖熬制，抹面包优选。",
    },
    {
        "id": 107,
        "categoryId": "fruit_plum",
        "name": "青脆李（当季）",
        "price": 29.9,
        "unit": "箱/3斤",
        "cover": "https://images.unsplash.com/photo-1590362891998-f192e78d5f5a?w=600&q=80",
        "stock": 160,
        "desc": "果肉紧实，酸甜开胃。",
    },
    {
        "id": 108,
        "categoryId": "fruit_plum",
        "name": "李子果干",
        "price": 22.0,
        "unit": "袋/200g",
        "cover": "https://images.unsplash.com/photo-1596040033229-a98c47c6e77e?w=600&q=80",
        "stock": 300,
        "desc": "无核切片，休闲零食。",
    },
    {
        "id": 109,
        "categoryId": "fruit_loquat",
        "name": "龙泉枇杷鲜果",
        "price": 48.0,
        "unit": "盒/1.5斤",
        "cover": "https://images.unsplash.com/photo-1615485925606-6c6c4c1b6b0a?w=600&q=80",
        "stock": 100,
        "desc": "皮薄肉厚，初夏限定。",
    },
    {
        "id": 110,
        "categoryId": "fruit_loquat",
        "name": "枇杷膏（手工熬制）",
        "price": 56.0,
        "unit": "瓶/280g",
        "cover": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
        "stock": 70,
        "desc": "温水冲服，润喉常备。",
    },
    {
        "id": 111,
        "categoryId": "fruit_citrus",
        "name": "蒲江丑柑（精品果）",
        "price": 42.0,
        "unit": "箱/8斤",
        "cover": "https://images.unsplash.com/photo-1547514701-42782101795e?w=600&q=80",
        "stock": 180,
        "desc": "自然脱酸，鲜食榨汁皆宜。",
    },
    {
        "id": 112,
        "categoryId": "fruit_citrus",
        "name": "柑橘蜜饯礼盒",
        "price": 38.0,
        "unit": "盒",
        "cover": "https://images.unsplash.com/photo-1544787219-7f47ccb7651f?w=600&q=80",
        "stock": 110,
        "desc": "茶点搭配，老少皆宜。",
    },
    {
        "id": 113,
        "categoryId": "oil_rapeseed",
        "name": "压榨菜籽油（非转）",
        "price": 69.0,
        "unit": "桶/5L",
        "cover": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=600&q=80",
        "stock": 400,
        "desc": "本地油菜籽压榨，家常烹饪。",
    },
    {
        "id": 114,
        "categoryId": "oil_rapeseed",
        "name": "菜籽调和油（小瓶）",
        "price": 19.9,
        "unit": "瓶/900ml",
        "cover": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&q=80",
        "stock": 500,
        "desc": "小包装尝鲜，油烟少。",
    },
]

ADOPTION_TREES = [
    {"id": "T-001", "treeKind": "桃树", "flowerKey": "桃花", "code": "桃源东-12号", "area": "龙泉山东区", "ageYear": 4, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?w=600&q=80"},
    {"id": "T-002", "treeKind": "桃树", "flowerKey": "桃花", "code": "桃源西-07号", "area": "环湖带", "ageYear": 5, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1462275646964-a0e3386b89a0?w=600&q=80"},
    {"id": "T-003", "treeKind": "梨树", "flowerKey": "梨花", "code": "梨园A-03号", "area": "新津片区", "ageYear": 6, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=600&q=80"},
    {"id": "T-004", "treeKind": "梨树", "flowerKey": "梨花", "code": "梨园B-11号", "area": "金堂栖贤", "ageYear": 5, "status": "已认养", "previewImage": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&q=80"},
    {"id": "T-005", "treeKind": "樱桃树", "flowerKey": "樱桃花", "code": "樱桃沟-05号", "area": "简阳", "ageYear": 4, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1528821128474-27f963b062bf?w=600&q=80"},
    {"id": "T-006", "treeKind": "樱桃树", "flowerKey": "樱桃花", "code": "樱桃山-08号", "area": "蒲江", "ageYear": 3, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600&q=80"},
    {"id": "T-007", "treeKind": "李树", "flowerKey": "李花", "code": "李园-02号", "area": "青白江", "ageYear": 5, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1590362891998-f192e78d5f5a?w=600&q=80"},
    {"id": "T-008", "treeKind": "李树", "flowerKey": "李花", "code": "李园-15号", "area": "彭州葛仙山", "ageYear": 4, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1604977042232-bf6d5eedbeb4?w=600&q=80"},
    {"id": "T-009", "treeKind": "枇杷树", "flowerKey": "枇杷花", "code": "枇杷园-06号", "area": "双流", "ageYear": 7, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1615485925606-6c6c4c1b6b0a?w=600&q=80"},
    {"id": "T-010", "treeKind": "枇杷树", "flowerKey": "枇杷花", "code": "枇杷园-09号", "area": "龙泉驿", "ageYear": 6, "status": "已认养", "previewImage": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=600&q=80"},
    {"id": "T-011", "treeKind": "柑橘树", "flowerKey": "柑橘花", "code": "柑橘园-04号", "area": "蒲江", "ageYear": 5, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1547514701-42782101795e?w=600&q=80"},
    {"id": "T-012", "treeKind": "柑橘树", "flowerKey": "柑橘花", "code": "柑橘园-12号", "area": "金堂三溪", "ageYear": 4, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?w=600&q=80"},
    {"id": "T-013", "treeKind": "油菜种植区", "flowerKey": "油菜花", "code": "油菜区-A块", "area": "崇州重庆路片区", "ageYear": 1, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600&q=80"},
    {"id": "T-014", "treeKind": "油菜种植区", "flowerKey": "油菜花", "code": "油菜区-B块", "area": "金堂三溪河谷", "ageYear": 1, "status": "可认养", "previewImage": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=600&q=80"},
]

REVIEWS_SEED = [
    {
        "id": 1,
        "userNick": "旅人小周",
        "avatar": "https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0",
        "rating": 5,
        "content": "盛花期太震撼了，按花种看人流和AI路线很省心！",
        "images": ["https://images.unsplash.com/photo-1522383225653-ed111181a951?w=400&q=80"],
        "createdAt": "2026-03-28 14:20",
    },
]


def default_addresses():
    return [
        {
            "id": 1,
            "name": "张三",
            "phone": "13800000000",
            "region": "四川省 成都市 龙泉驿区",
            "detail": "桃源大道88号",
            "isDefault": True,
        }
    ]


def ok(data=None, msg="ok"):
    return {"code": 0, "msg": msg, "data": data}


def err(msg="error", code=400, data=None):
    return {"code": code, "msg": msg, "data": data}


def _fmt_cn_day(dt):
    return f"{dt.month}月{dt.day}日"


def _viewing_period_str(peak_dt, span_days=4):
    lo = peak_dt - timedelta(days=span_days)
    hi = peak_dt + timedelta(days=span_days)
    return f"{_fmt_cn_day(lo)}-{_fmt_cn_day(hi)}"


def _open_degree(peak_dt, now):
    diff_days = abs((peak_dt - now).days)
    return max(0.0, min(1.0, round(1.0 - diff_days / 24.0, 3)))


def _phase_key_name_from_countdown(countdown_days: int):
    """与桃花盛花日相对天数 → 阶段键与阶段名（作物物候）。"""
    if countdown_days > 25:
        return "budding", "萌芽期"
    if 7 < countdown_days <= 25:
        return "early_bloom", "初花期"
    if -7 <= countdown_days <= 7:
        return "peak_bloom", "盛花期"
    if -30 <= countdown_days < -7:
        return "late_fall", "落花末期"
    return "wither", "休养期"


# 以 predict.py 桃花盛花预测日为唯一基准，其余花种仅做日历偏移（同一套模型输出，不另训模型）
PEACH_MODEL_FLOWER_OFFSETS = [
    ("桃花", "桃花", 0),
    ("梨花", "梨花", -6),
    ("樱桃花", "樱桃花", -4),
    ("李花", "李花", -5),
    ("枇杷花", "枇杷花", -42),
    ("柑橘花", "柑橘花", 12),
    ("油菜花", "油菜花", 7),
]


def _flower_description_text(flower_key: str, peak_dt, now):
    """各花种农事与观赏说明（桃花保留农业预测与农事提示；油菜含经济作物与观光）。"""
    d = (peak_dt - now).days
    timing = (
        f"据模型推演，盛花高峰约在{peak_dt.strftime('%Y年%m月%d日')}前后；"
        if d > 3
        else f"当前临近或处于盛花窗口；"
    )
    if flower_key == "桃花":
        return (
            timing
            + "龙泉驿水蜜桃主产区以「平坝山脚盛花期」为训练目标，本结果由气象候值与线性回归模型给出，供花期预报与农事安排参考。"
            "农事提示：盛花前后注意疏花定果、蚜虫与褐腐病防治；遇倒春寒可灌水调温或熏烟防霜。游园采摘请关注园区人流与道路管制。"
        )
    if flower_key == "梨花":
        return (
            timing
            + "梨树为川内重要经济林果，花期略早于桃。与桃花同一套气象—模型推演逻辑，仅按物候差做日历偏移。"
            "农事提示：重视授粉与晚霜防护，幼果期疏果可提高商品果率；赏花宜选晴天上午并注意田间安全。"
        )
    if flower_key == "樱桃花":
        return (
            timing
            + "此处指樱桃果树开花期（非观赏樱花），座果与当年产量密切相关，推演方法与桃花模型一致。"
            "农事提示：花期忌暴雨冲刷花粉；可结合叶面肥与病虫害统防；农旅园区建议错峰入园、文明观花。"
        )
    if flower_key == "李花":
        return (
            timing
            + "李树花期在桃李混栽区常见，脆李等品种可据花量指导疏花。"
            "农事提示：花期湿冷易诱发花腐病，注意开沟排水与树冠通风；观光请勿攀折花枝。"
        )
    if flower_key == "枇杷花":
        return (
            timing
            + "枇杷秋冬至早春开花，与春季桃盛花错季，仍由同一桃花模型基准日按物候偏移推算，便于茬口衔接。"
            "农事提示：关注冻害与花腐病；枇杷果春夏上市，经济价值高，可结合当地枇杷节安排采摘与物流。"
        )
    if flower_key == "柑橘花":
        return (
            timing
            + "柑橘类春季开花，花香浓郁，关系当年产量；推演与桃树模型同源，仅偏移至柑橘物候。"
            "农事提示：保花保果需肥水平衡与控梢；注意花期蚜虫与炭疽病预防；入园观光勿擅摘果实。"
        )
    if flower_key == "油菜花":
        return (
            timing
            + "四川盆地冬油菜春季进入盛花，既是重要经济作物（油菜籽榨油、饲用），也是观光农业与摄影热点。"
            "推演与桃花模型同一基准，仅按油菜物候偏移；请文明赏花、爱护农田与沟渠，勿碾压作物。"
        )
    return timing + "花期信息由桃花预测模型推演偏移得到，仅供参考。"


def _build_peach_central_predictions(peach_peak_dt, now):
    """
    七种花均复用 predict.py 得到的桃花盛花日 peach_peak_dt，仅按物候差做 timedelta 偏移；
    不修改、不替换 predict.py 内模型结构。
    """
    rows = []
    for flower_key, flower_name, day_off in PEACH_MODEL_FLOWER_OFFSETS:
        peak = peach_peak_dt + timedelta(days=day_off)
        cd = int((peak - now).days)
        ph_key, stage = _phase_key_name_from_countdown(cd)
        open_pct = round(_open_degree(peak, now) * 100, 1)
        rows.append(
            {
                "flowerKey": flower_key,
                "flower_name": flower_name,
                "best_time": _viewing_period_str(peak),
                "open_percent": open_pct,
                "bloom_time": peak.strftime("%Y-%m-%d"),
                "days_to_bloom": cd,
                "stage": stage,
                "phaseKey": ph_key,
                "description": _flower_description_text(flower_key, peak, now),
            }
        )
    return rows


def _pack_prediction_result(peak_date, now, model_note, fallback=False):
    """由 predict.py 桃花盛花日 peak_date 组装七花种预测（同一模型逻辑 + 日历偏移）。"""
    countdown_days = int((peak_date - now).days)
    phase_key, phase_name = _phase_key_name_from_countdown(countdown_days)
    predictions = _build_peach_central_predictions(peak_date, now)
    peach_sel = next((p for p in predictions if p.get("flowerKey") == "桃花"), predictions[0] if predictions else None)
    out = {
        "predictions": predictions,
        "selected": peach_sel,
        "currentPhase": phase_name,
        "currentPhaseKey": phase_key,
        "primaryFlowerKey": "桃花",
        "modelNote": model_note,
        "updatedAt": now.isoformat() + "Z",
    }
    if fallback:
        out["fallback"] = True
    return out


def run_flower_prediction_model_fallback(reason: str):
    """
    不依赖 sklearn / 气象文件时的演示预测（保证小程序有数据可展示）。
    """
    now = datetime.now()
    out_year = now.year
    peak_date = datetime(out_year, 3, 25)
    note = "多花种花期预测（演示数据，仅供参考）。"
    return _pack_prediction_result(peak_date, now, note, fallback=True)


def _run_flower_prediction_model_from_files():
    """
    调用真实花期预测模型（backend/predict.py），并将结果整理成小程序可直接使用的字段。

    你需要保证：
    - 同目录下存在 flowering.csv 和 气象数据 Excel（predict.py 里配置的文件名）
    - 已安装 scikit-learn、pandas 等依赖
    """
    import sys
    import pandas as pd  # type: ignore

    base_dir = os.path.dirname(__file__)
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    import predict  # 自定义模型脚本（backend/predict.py）

    weather_path = os.environ.get(
        "FLOWER_WEATHER_XLSX",
        os.path.join(base_dir, "龙泉驿56286.xlsx"),
    )
    flowering_csv_path = os.environ.get(
        "FLOWER_FLOWERING_CSV",
        os.path.join(base_dir, "flowering.csv"),
    )
    flowering_xlsx_path = os.environ.get(
        "FLOWER_FLOWERING_XLSX",
        os.path.join(base_dir, "flowering.xlsx"),
    )

    if not os.path.exists(weather_path):
        raise FileNotFoundError(
            f"weather xlsx not found: {weather_path} (请把龙泉驿气象数据Excel放入backend目录或设置环境变量FLOWER_WEATHER_XLSX)"
        )
    if not os.path.exists(flowering_csv_path) and not os.path.exists(flowering_xlsx_path):
        raise FileNotFoundError(
            "flowering data not found: (请确保backend/flowering.csv 或 backend/flowering.xlsx存在；"
            "或设置环境变量 FLOWER_FLOWERING_CSV / FLOWER_FLOWERING_XLSX)"
        )

    weather_df = predict.load_weather_data(weather_path)
    weather_df = predict.add_time_features(weather_df)
    hou_df = predict.compute_hou_features(weather_df)
    cold_sum = predict.compute_cold_accumulation(weather_df)

    if os.path.exists(flowering_csv_path):
        flowering_df = pd.read_csv(flowering_csv_path)
    else:
        flowering_df = pd.read_excel(flowering_xlsx_path)
    target_col = "平坝山脚盛花期"

    X, y = predict.build_dataset(hou_df, cold_sum, flowering_df, target_col)
    model = predict.train_model(X, y)

    now = datetime.now()
    this_year = now.year

    available_years = []
    if "年份" in getattr(hou_df, "columns", []):
        available_years = [int(v) for v in hou_df["年份"].dropna().unique().tolist()]
    available_years = sorted(set(available_years))

    feature_year = this_year if this_year in available_years else (available_years[-1] if available_years else this_year)

    def calc_peak_date_str(out_year: int) -> str:
        return predict.predict_flowering(
            model,
            hou_df,
            cold_sum,
            feature_year=feature_year,
            out_year=out_year,
        )

    out_year = this_year
    peak_date_str = calc_peak_date_str(out_year)
    peak_date = datetime.strptime(peak_date_str, "%Y-%m-%d")

    note = "龙泉驿桃树盛花期由 predict.py 线性回归预测；其余花种同基准日物候偏移，供农事与观光参考。"
    return _pack_prediction_result(peak_date, now, note, fallback=False)


def run_flower_prediction_model():
    """
    优先调用真实模型；若缺少 sklearn、数据文件或推理异常，则自动返回演示预测（HTTP 仍为 200）。
    """
    try:
        return _run_flower_prediction_model_from_files()
    except Exception as e:
        return run_flower_prediction_model_fallback(str(e))
