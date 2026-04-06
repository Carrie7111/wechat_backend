# -*- coding: utf-8 -*-
"""
蓉城赏花游客服务 — Flask REST API
运行: python app.py  默认 http://127.0.0.1:5000
小程序开发工具需勾选「不校验合法域名」以访问本机地址。
"""
import copy
import json
import os
import secrets
import ssl
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime

# 从 backend/.env 加载大模型等配置（override=True：.env 优先于系统里可能存在的空变量）
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_PATH = os.path.join(_BACKEND_DIR, ".env")
try:
    from dotenv import load_dotenv

    load_dotenv(_ENV_PATH, override=True)
except ImportError:
    pass


def _env_llm_config():
    """读取 LLM 配置并做常见清洗（Windows 记事本 BOM、首尾引号）。"""
    base = (os.environ.get("LLM_API_BASE") or "").strip().rstrip("/")
    key = (os.environ.get("LLM_API_KEY") or "").strip()
    if key.startswith("\ufeff"):
        key = key.lstrip("\ufeff")
    if len(key) >= 2 and ((key[0] == key[-1] == '"') or (key[0] == key[-1] == "'")):
        key = key[1:-1].strip()
    model = (os.environ.get("LLM_MODEL") or "gpt-4o-mini").strip()
    return base, key, model

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)

# ---------- 跨域（必须在所有 @app.route 与业务 import 之前注册）----------
# Python 正则中 "/api/*" 的 * 只重复前一个字符 "/"，无法匹配 /api/health 等路径，会导致预检失败。
# 使用 "/api/.*" 匹配所有以 /api/ 开头的路径；OPTIONS 由 flask-cors 自动处理。
_API_CORS = {
    "origins": "*",
    "methods": ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    "allow_headers": [
        "Content-Type",
        "Authorization",
        "X-Token",
        "X-Requested-With",
        "Accept",
        "Origin",
    ],
    "expose_headers": ["Content-Type"],
    "max_age": 86400,
}

CORS(
    app,
    resources={
        r"/api/.*": _API_CORS,
        r"/uploads/.*": {
            "origins": "*",
            "methods": ["GET", "HEAD", "OPTIONS"],
            "allow_headers": ["Content-Type", "Accept", "Origin"],
            "max_age": 86400,
        },
    },
    supports_credentials=False,
    automatic_options=True,
)

from mock_data import (
    ATTRACTIONS,
    ADOPTION_TREES,
    BANNERS,
    crowd_flow_payload,
    FLOWER_AI_HINTS,
    FLOWER_PHASES,
    FLOWER_SPECIES,
    MALL_CATEGORIES,
    PRODUCTS,
    REVIEWS_SEED,
    default_addresses,
    err,
    ok,
    run_flower_prediction_model,
)

# 上传图片目录（与 app.py 同级的 uploads/）
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_UPLOAD_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

# ---------- 内存存储（重启即清空）----------
SESSIONS = {}  # token -> user dict
USER_STORE = {}  # openId or synthetic id -> extended profile
ORDERS = {}  # userId -> list
ADDRESSES = {}  # userId -> list
ADOPTED = {}  # userId -> list of tree ids
TREE_STATE = {t["id"]: t["status"] for t in ADOPTION_TREES}
REVIEWS = copy.deepcopy(REVIEWS_SEED)
REVIEW_SEQ = max((r["id"] for r in REVIEWS), default=0) + 1
REVIEW_LIKERS = defaultdict(set)  # review_id -> set(openId)
ORDER_SEQ = 10001
NOTICE_TEXT = "欢迎使用蓉城赏花智慧导览：果树花与油菜花七类花期预测、按花种地图与AI路线讲解一键直达。"


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """访问已上传图片（完整 URL 形如 /uploads/xxx.jpg）。"""
    base = os.path.basename(filename)
    if not os.path.isfile(os.path.join(UPLOAD_DIR, base)):
        return jsonify(err("文件不存在", code=404)), 404
    return send_from_directory(UPLOAD_DIR, base)


@app.route("/api/upload", methods=["POST"])
def api_upload():
    user, resp = require_auth()
    if resp:
        return resp
    if "file" not in request.files:
        return jsonify(err("请选择图片文件", code=400))
    f = request.files["file"]
    if not f or not f.filename:
        return jsonify(err("无效文件", code=400))
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXT:
        return jsonify(err("仅支持 png/jpg/jpeg/gif/webp", code=400))
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    fn = secrets.token_hex(16) + ext
    f.save(os.path.join(UPLOAD_DIR, fn))
    base = request.url_root.rstrip("/")
    url = f"{base}/uploads/{fn}"
    return jsonify(ok({"url": url}))


def get_token_user():
    auth = request.headers.get("Authorization", "") or ""
    token = auth.replace("Bearer", "").strip()
    if not token:
        token = request.headers.get("X-Token", "")
    if not token or token not in SESSIONS:
        return None, None
    user = SESSIONS[token]
    return token, user


def require_auth():
    token, user = get_token_user()
    if not user:
        return None, jsonify(err("未登录或 token 失效", code=401))
    return user, None


def user_key(user):
    return user.get("openId") or user.get("id") or "guest"


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify(ok({"status": "ok", "time": datetime.now().isoformat()}))


# ---------- 登录（微信 code + 可选头像昵称）----------
@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    body = request.get_json(silent=True) or {}
    code = body.get("code", "")
    nick_name = body.get("nickName", "游客")
    avatar_url = body.get("avatarUrl", "")
    # 真实环境：用 code 换 openid/session_key
    open_id = "mock_" + secrets.token_hex(8)
    if code:
        open_id = "wx_" + str(abs(hash(code)) % 10**10)

    user = {
        "openId": open_id,
        "nickName": nick_name,
        "avatarUrl": avatar_url,
        "phone": USER_STORE.get(open_id, {}).get("phone", ""),
    }
    USER_STORE[open_id] = {**USER_STORE.get(open_id, {}), **user}

    token = secrets.token_hex(16)
    SESSIONS[token] = user
    if open_id not in ADDRESSES:
        ADDRESSES[open_id] = default_addresses()
    if open_id not in ORDERS:
        ORDERS[open_id] = []

    return jsonify(ok({"token": token, "user": user, "notice": NOTICE_TEXT}))


@app.route("/api/user/profile", methods=["GET"])
def user_profile():
    user, resp = require_auth()
    if resp:
        return resp
    uid = user_key(user)
    merged = {**user, **USER_STORE.get(uid, {})}
    return jsonify(ok(merged))


@app.route("/api/user/profile", methods=["PUT"])
def user_profile_put():
    user, resp = require_auth()
    if resp:
        return resp
    token, _ = get_token_user()
    uid = user_key(user)
    body = request.get_json(silent=True) or {}
    store = USER_STORE.get(uid, {})
    if "nickName" in body:
        store["nickName"] = body["nickName"]
    if "avatarUrl" in body:
        store["avatarUrl"] = body["avatarUrl"]
    if "phone" in body:
        store["phone"] = body["phone"]
    merged = {**user, **store}
    USER_STORE[uid] = merged
    if token:
        SESSIONS[token] = merged
    return jsonify(ok(merged))


# ---------- 首页 ----------
@app.route("/api/home/banners", methods=["GET"])
def home_banners():
    return jsonify(ok(BANNERS))


@app.route("/api/home/notice", methods=["GET"])
def home_notice():
    return jsonify(ok({"content": NOTICE_TEXT}))


# ---------- 花期（静态周期 + 模型预测接口）----------
@app.route("/api/flower/phases", methods=["GET"])
def flower_phases():
    """全周期展示数据；currentKey 可与预测接口联动。"""
    return jsonify(
        ok(
            {
                "phases": FLOWER_PHASES,
                "currentKey": "early_bloom",
                "highlight": "蓉城果树花与油菜花次第开放，可按花种查看预测与地图筛选景区。",
            }
        )
    )


@app.route("/api/flower/species", methods=["GET"])
def flower_species():
    return jsonify(ok(FLOWER_SPECIES))


@app.route("/api/flower-prediction", methods=["GET"])
def flower_prediction():
    """
    花期预测：严格使用 predict.py 桃花模型输出为基准，七花种见 predictions。
    查询参数 flower：桃花|梨花|樱桃花|李花|枇杷花|柑橘花|油菜花，用于返回 selected 当前选中项。
    """
    try:
        pred = run_flower_prediction_model()
        fk = (request.args.get("flower") or request.args.get("flowerKey") or "桃花").strip()
        preds = pred.get("predictions") or []
        sel = next((p for p in preds if p.get("flowerKey") == fk), None)
        if sel is None and preds:
            sel = preds[0]
        pred["selected"] = sel
        return jsonify(ok(pred))
    except Exception as e:
        return jsonify(err(f"prediction_failed: {e}", code=500))


@app.route("/api/crowd/flow", methods=["GET"])
def crowd_flow():
    """按花种分组，每组含多个景区的人流量（果树花+油菜花）。"""
    now = datetime.now()
    date_text = f"{now.year}年{now.month:02d}月{now.day:02d}日"
    return jsonify(
        ok(
            {
                "flowers": crowd_flow_payload(),
                "dateText": date_text,
                "updatedAt": now.isoformat(),
            }
        )
    )


# ---------- 景点 & AI ----------
@app.route("/api/attractions", methods=["GET"])
def attractions_list():
    fk = (request.args.get("flowerKey") or "").strip()
    rows = ATTRACTIONS
    if fk:
        rows = [a for a in ATTRACTIONS if a.get("flowerKey") == fk]
    return jsonify(ok(rows))


@app.route("/api/attractions/<int:spot_id>", methods=["GET"])
def attraction_detail(spot_id):
    one = next((a for a in ATTRACTIONS if a["id"] == spot_id), None)
    if not one:
        return jsonify(err("景点不存在", code=404))
    return jsonify(ok(one))


@app.route("/api/ai/introduction", methods=["POST"])
def ai_introduction():
    body = request.get_json(silent=True) or {}
    spot_id = body.get("spotId")
    flower_key = (body.get("flowerKey") or "").strip()
    one = next((a for a in ATTRACTIONS if a["id"] == int(spot_id)), None) if spot_id else None
    fk = flower_key or (one.get("flowerKey") if one else "") or "桃花"
    name = one["name"] if one else "成都赏花景区"
    species_name = next((s["name"] for s in FLOWER_SPECIES if s["key"] == fk), fk or "花卉")
    hint = FLOWER_AI_HINTS.get(fk, "建议错峰出行，注意防晒与补水。")
    text = (
        f"【{species_name}·AI讲解】{name}：建议安排35-50分钟慢游，结合园区开放时间规划。"
        f"{hint} 若需串联多景点，可使用同花种的「AI路线」功能。"
    )
    return jsonify(
        ok(
            {
                "spotId": spot_id,
                "flowerKey": fk,
                "introduction": text,
                "provider": "template_llm",
            }
        )
    )


@app.route("/api/ai/route", methods=["POST"])
def ai_route():
    body = request.get_json(silent=True) or {}
    prefer = body.get("preferences", "轻松")
    flower_key = (body.get("flowerKey") or "").strip() or "桃花"
    species_name = next((s["name"] for s in FLOWER_SPECIES if s["key"] == flower_key), flower_key or "花卉")
    pool = [a for a in ATTRACTIONS if a.get("flowerKey") == flower_key]
    if not pool:
        pool = list(ATTRACTIONS)[:6]

    order = list(range(min(4, len(pool))))
    if prefer == "摄影" and len(pool) >= 3:
        order = [0, min(2, len(pool) - 1), min(1, len(pool) - 1)]
    elif prefer == "亲子" and len(pool) >= 3:
        order = [min(1, len(pool) - 1), 0, min(2, len(pool) - 1)]

    steps = []
    for i, idx in enumerate(order):
        sp = pool[idx]
        tip = "适合慢游取景，注意步道安全" if prefer != "摄影" else "早晚柔光更出片，可带长焦压缩层次"
        steps.append(
            {
                "step": i + 1,
                "spotId": sp["id"],
                "name": sp["name"],
                "flowerKey": sp.get("flowerKey"),
                "stayMinutes": 28 if prefer != "摄影" else 42,
                "tip": tip,
            }
        )
    lats = [p["lat"] for p in pool]
    lngs = [p["lng"] for p in pool]
    center_lat = sum(lats) / len(lats)
    center_lng = sum(lngs) / len(lngs)
    summary = f"【{species_name}主题路线】已按「{prefer}」偏好串联 {len(steps)} 处赏花点（演示规划）。"
    return jsonify(
        ok(
            {
                "summary": summary,
                "steps": steps,
                "flowerKey": flower_key,
                "mapCenter": {"lat": round(center_lat, 5), "lng": round(center_lng, 5)},
            }
        )
    )


# ---------- 认养 ----------
@app.route("/api/adoption/trees", methods=["GET"])
def adoption_trees():
    _, user = get_token_user()
    uid = user_key(user) if user else None
    mine = set(ADOPTED.get(uid, [])) if uid else set()
    rows = []
    for t in ADOPTION_TREES:
        row = dict(t)
        row["status"] = TREE_STATE.get(t["id"], row["status"])
        row["isMine"] = t["id"] in mine
        rows.append(row)
    return jsonify(ok(rows))


@app.route("/api/adoption/mine", methods=["GET"])
def adoption_mine():
    user, resp = require_auth()
    if resp:
        return resp
    uid = user_key(user)
    ids = ADOPTED.get(uid, [])
    rows = [dict(t) for t in ADOPTION_TREES if t["id"] in ids]
    return jsonify(ok(rows))


@app.route("/api/adoption/adopt", methods=["POST"])
def adoption_adopt():
    user, resp = require_auth()
    if resp:
        return resp
    body = request.get_json(silent=True) or {}
    tree_id = body.get("treeId")
    tree = next((t for t in ADOPTION_TREES if t["id"] == tree_id), None)
    if not tree:
        return jsonify(err("认养对象不存在", code=404))
    if TREE_STATE.get(tree_id) == "已认养":
        return jsonify(err("该树已被认养", code=409))
    uid = user_key(user)
    TREE_STATE[tree_id] = "已认养"
    ADOPTED.setdefault(uid, []).append(tree_id)
    out = dict(tree)
    out["status"] = "已认养"
    return jsonify(ok({"tree": out, "message": "认养成功（模拟）"}))


# ---------- 评价晒图 ----------
def _viewer_open_id():
    _, user = get_token_user()
    return user_key(user) if user else None


def _enrich_review(r, viewer_oid):
    rid = r["id"]
    likes = REVIEW_LIKERS[rid]
    return {
        **r,
        "likeCount": len(likes),
        "likedByMe": bool(viewer_oid and viewer_oid in likes),
    }


@app.route("/api/reviews", methods=["GET"])
def reviews_list():
    viewer_oid = _viewer_open_id()
    rows = [_enrich_review(r, viewer_oid) for r in reversed(REVIEWS)]
    return jsonify(ok(rows))


@app.route("/api/reviews", methods=["POST"])
def reviews_post():
    user, resp = require_auth()
    if resp:
        return resp
    global REVIEW_SEQ
    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    images = body.get("images") or []
    if isinstance(images, str):
        images = [images] if images else []
    if not content and not images:
        return jsonify(err("请填写文字或上传图片", code=400))
    reply_to = body.get("replyToReviewId")
    reply_nick = (body.get("replyToNick") or "").strip() or None
    item = {
        "id": REVIEW_SEQ,
        "userNick": user.get("nickName", "游客"),
        "avatar": user.get("avatarUrl", ""),
        "rating": int(body.get("rating", 5)),
        "content": content,
        "images": images if isinstance(images, list) else [],
        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    if reply_to is not None:
        try:
            item["replyToReviewId"] = int(reply_to)
            item["replyToNick"] = reply_nick
        except (TypeError, ValueError):
            pass
    REVIEW_SEQ += 1
    REVIEWS.append(item)
    return jsonify(ok(_enrich_review(item, user_key(user))))


@app.route("/api/reviews/<int:rid>/like", methods=["POST"])
def reviews_like(rid):
    user, resp = require_auth()
    if resp:
        return resp
    one = next((r for r in REVIEWS if r["id"] == rid), None)
    if not one:
        return jsonify(err("评价不存在", code=404))
    uid = user_key(user)
    s = REVIEW_LIKERS[rid]
    if uid in s:
        s.remove(uid)
        liked = False
    else:
        s.add(uid)
        liked = True
    return jsonify(ok({"liked": liked, "likeCount": len(s)}))


def _fallback_chat_reply(user_text):
    t = (user_text or "").strip()[:500]
    return (
        "【蓉城赏花助手】关于「"
        + t
        + "」：春季可关注桃花、梨花、樱桃花、李花、枇杷花、柑橘花与油菜花等果树与经济作物花期。"
        "首页提供七花种花期预测，地图可按花种筛选景区，「AI路线」可按同花种串联赏花点。"
    )


def _call_openai_compatible(messages):
    """
    调用 OpenAI 兼容 Chat Completions。
    返回 (reply_text_or_None, error_detail_or_None)。error 仅在请求已发出但失败时返回，便于排查。
    """
    base, key, model = _env_llm_config()
    if not base or not key:
        return None, None
    url = base + "/chat/completions"
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 1024,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        choices = data.get("choices") or []
        if not choices:
            return None, "接口返回无 choices，请检查模型名与账户权限"
        text = (choices[0].get("message") or {}).get("content")
        return (text if text else None), None
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")[:600]
        except Exception:
            err_body = str(e.reason)
        return None, f"HTTP {e.code} {e.reason}: {err_body}"
    except urllib.error.URLError as e:
        return None, f"网络错误: {e.reason}"
    except (json.JSONDecodeError, TimeoutError, OSError) as e:
        return None, str(e)


@app.route("/api/ai/llm-status", methods=["GET"])
def ai_llm_status():
    """供调试：是否已配置 OpenAI 兼容接口（不返回密钥）。"""
    base, key, model = _env_llm_config()
    env_exists = os.path.isfile(_ENV_PATH)
    return jsonify(
        ok(
            {
                "configured": bool(base and key),
                "envFileExists": env_exists,
                "envFilePath": _ENV_PATH,
                "model": model,
                "baseUrlSet": bool(base),
                "keySet": bool(key),
                "hint": "若 envFileExists 为 false：请在 backend 文件夹新建 .env（可复制 .env.example）。"
                "若 keySet 为 false：在 .env 中填写 LLM_API_KEY=你的密钥。LLM_API_BASE 须带 /v1。",
            }
        )
    )


@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    body = request.get_json(silent=True) or {}
    user_msg = (body.get("message") or "").strip()
    if not user_msg:
        return jsonify(err("请输入内容", code=400))
    history = body.get("history") or []
    messages = [
        {
            "role": "system",
            "content": "你是「蓉城赏花」微信小程序的智能助手，熟悉成都及周边赏花、花期、景点路线与摄影建议。回答简洁、实用、友好，可适当分段。",
        }
    ]
    for h in history[-10:]:
        role = h.get("role")
        content = (h.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_msg})
    reply, api_err = _call_openai_compatible(messages)
    base, key, _model = _env_llm_config()
    if reply:
        return jsonify(ok({"reply": reply, "provider": "openai_compatible"}))
    if base and key and api_err:
        return jsonify(
            ok(
                {
                    "reply": _fallback_chat_reply(user_msg)
                    + "\n\n（智能回复暂不可用，已为您展示本地参考；请稍后再试。）",
                    "provider": "openai_error",
                    "detail": api_err,
                }
            )
        )
    return jsonify(ok({"reply": _fallback_chat_reply(user_msg), "provider": "local_fallback"}))


# ---------- 商城 ----------
@app.route("/api/mall/categories", methods=["GET"])
def mall_categories():
    return jsonify(ok(MALL_CATEGORIES))


@app.route("/api/mall/products", methods=["GET"])
def mall_products():
    cid = request.args.get("categoryId")
    rows = PRODUCTS if not cid else [p for p in PRODUCTS if p["categoryId"] == cid]
    return jsonify(ok(rows))


@app.route("/api/mall/products/<int:pid>", methods=["GET"])
def mall_product_detail(pid):
    one = next((p for p in PRODUCTS if p["id"] == pid), None)
    if not one:
        return jsonify(err("商品不存在", code=404))
    return jsonify(ok(one))


# ---------- 订单 ----------
@app.route("/api/orders", methods=["GET"])
def orders_list():
    user, resp = require_auth()
    if resp:
        return resp
    uid = user_key(user)
    return jsonify(ok(list(reversed(ORDERS.get(uid, [])))))


@app.route("/api/orders", methods=["POST"])
def orders_create():
    user, resp = require_auth()
    if resp:
        return resp
    global ORDER_SEQ
    body = request.get_json(silent=True) or {}
    items = body.get("items") or []
    address_id = body.get("addressId")
    if not items:
        return jsonify(err("订单商品不能为空", code=400))
    uid = user_key(user)
    addr_list = ADDRESSES.get(uid, [])
    addr = next((a for a in addr_list if a["id"] == int(address_id)), addr_list[0] if addr_list else None)
    if not addr:
        return jsonify(err("请先添加收货地址", code=400))
    lines = []
    total = 0.0
    for it in items:
        pid = int(it.get("productId"))
        qty = int(it.get("quantity", 1))
        p = next((x for x in PRODUCTS if x["id"] == pid), None)
        if not p:
            continue
        line_total = round(float(p["price"]) * qty, 2)
        total += line_total
        lines.append(
            {
                "productId": p["id"],
                "name": p["name"],
                "price": p["price"],
                "quantity": qty,
                "cover": p["cover"],
                "subtotal": line_total,
            }
        )
    if not lines:
        return jsonify(err("有效商品为空", code=400))
    order = {
        "id": ORDER_SEQ,
        "status": "待发货",
        "total": round(total, 2),
        "items": lines,
        "address": addr,
        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    ORDER_SEQ += 1
    ORDERS.setdefault(uid, []).append(order)
    return jsonify(ok(order))


@app.route("/api/orders/<int:oid>", methods=["GET"])
def order_detail(oid):
    user, resp = require_auth()
    if resp:
        return resp
    uid = user_key(user)
    for o in ORDERS.get(uid, []):
        if o["id"] == oid:
            return jsonify(ok(o))
    return jsonify(err("订单不存在", code=404))


# ---------- 地址 ----------
@app.route("/api/addresses", methods=["GET"])
def addresses_list():
    user, resp = require_auth()
    if resp:
        return resp
    uid = user_key(user)
    return jsonify(ok(ADDRESSES.get(uid, [])))


@app.route("/api/addresses", methods=["POST"])
def addresses_post():
    user, resp = require_auth()
    if resp:
        return resp
    body = request.get_json(silent=True) or {}
    uid = user_key(user)
    lst = ADDRESSES.setdefault(uid, [])
    new_id = max((a["id"] for a in lst), default=0) + 1
    if body.get("isDefault"):
        for a in lst:
            a["isDefault"] = False
    row = {
        "id": new_id,
        "name": body.get("name", ""),
        "phone": body.get("phone", ""),
        "region": body.get("region", ""),
        "detail": body.get("detail", ""),
        "isDefault": bool(body.get("isDefault")),
    }
    lst.append(row)
    return jsonify(ok(row))


@app.route("/api/addresses/<int:aid>", methods=["PUT"])
def addresses_put(aid):
    user, resp = require_auth()
    if resp:
        return resp
    body = request.get_json(silent=True) or {}
    uid = user_key(user)
    lst = ADDRESSES.get(uid, [])
    for a in lst:
        if a["id"] == aid:
            if body.get("isDefault"):
                for x in lst:
                    x["isDefault"] = False
            a.update(
                {
                    "name": body.get("name", a["name"]),
                    "phone": body.get("phone", a["phone"]),
                    "region": body.get("region", a["region"]),
                    "detail": body.get("detail", a["detail"]),
                    "isDefault": bool(body.get("isDefault", a["isDefault"])),
                }
            )
            return jsonify(ok(a))
    return jsonify(err("地址不存在", code=404))


@app.route("/api/addresses/<int:aid>", methods=["DELETE"])
def addresses_delete(aid):
    user, resp = require_auth()
    if resp:
        return resp
    uid = user_key(user)
    lst = ADDRESSES.get(uid, [])
    ADDRESSES[uid] = [a for a in lst if a["id"] != aid]
    return jsonify(ok({"deleted": aid}))


# ---------- 分享海报 ----------
@app.route("/api/share/poster", methods=["GET"])
def share_poster():
    scene = request.args.get("scene", "index")
    return jsonify(
        ok(
            {
                "title": "蓉城赏花邀您来",
                "subtitle": "七花种预测 · AI路线 · 果树认养",
                "bgImage": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=800&q=80",
                "qrHint": "长按识别小程序码（示意）",
                "scene": scene,
            }
        )
    )


if __name__ == "__main__":
    # Railway 注入 PORT；本地开发未设置时回退到 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
