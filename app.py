"""
Voice Ordering Application - Flask Backend
============================================
Processes voice text through GLM-5 / MiniMax M2.5 AI skills,
extracts order items, and manages the order cart.

Usage:
    python app.py
    Open http://localhost:5000
"""

import json
import os
import sys
import time
import uuid
from flask import Flask, render_template, request, jsonify

# Add AI skills to path
SKILLS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "openclaw", "skills", "ai-agent-skills", "scripts"
)
sys.path.insert(0, os.path.abspath(SKILLS_DIR))

from menu import MENU, OrderCart, get_menu_for_prompt, find_item_by_id, get_menu_json
from database import init_db, get_menu_from_db, save_order_to_db

# ---------------------------------------------------------------------------
# Flask App
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Store carts per session (simple in-memory for demo)
carts: dict[str, OrderCart] = {}
orders: list[dict] = []

# ---------------------------------------------------------------------------
# AI Processing
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an intelligent restaurant ordering assistant.
You help customers place orders by understanding their spoken requests.

{menu}

INSTRUCTIONS:
1. Extract ordered items and quantities from the customer's voice input.
2. Match items to the menu above using the item IDs.
3. If an item is not on the menu, politely suggest alternatives.
4. Respond in the SAME LANGUAGE the customer used (Chinese, English, or Malay).

You MUST return a JSON object in this EXACT format:
{{
  "items": [
    {{"id": "item_id", "quantity": number}},
    ...
  ],
  "message": "Your friendly response to the customer",
  "language": "zh", "en", or "ms",
  "action": "checkout" or null
}}

Examples:
- Input: "我要一杯拿铁和两个汉堡"
  Output: {{"items": [{{"id": "latte", "quantity": 1}}, {{"id": "hamburger", "quantity": 2}}], "message": "好的！一杯拿铁和两个汉堡，已经为您添加到订单中。", "language": "zh"}}

- Input: "I'd like a pizza and orange juice"
  Output: {{"items": [{{"id": "pizza", "quantity": 1}}, {{"id": "orange_juice", "quantity": 1}}], "message": "Sure! One pizza and an orange juice, added to your order.", "language": "en"}}

- Input: "给我来三份薯条"
  Output: {{"items": [{{"id": "fries", "quantity": 3}}], "message": "好的！三份薯条，已添加。", "language": "zh"}}

If the customer wants to pay, checkout, or confirm the order (e.g. "买单", "结账", "Confirm order"), return "action": "checkout".
If the customer asks about the menu or has questions, return items as empty array and answer in message.
ALWAYS return valid JSON. No markdown code blocks, just pure JSON.
"""


def _process_with_ai(voice_text: str) -> dict:
    """Process voice text with AI skills to extract order items."""
    menu_text = get_menu_for_prompt()
    system = SYSTEM_PROMPT.format(menu=menu_text)

    # Try GLM-5 first, fall back to MiniMax
    result = None
    model_used = "none"

    # Try GLM-5
    if os.environ.get("ZHIPU_API_KEY"):
        try:
            import glm5_agent
            result = glm5_agent.mode_chat(
                voice_text,
                system=system,
                temperature=0.3,
                max_tokens=1024,
            )
            model_used = "glm-5"
        except Exception as e:
            print(f"GLM-5 error: {e}", file=sys.stderr)

    # Try MiniMax as fallback
    if result is None and os.environ.get("MINIMAX_API_KEY"):
        try:
            import minimax_agent
            result = minimax_agent.mode_chat(
                voice_text,
                system=system,
                temperature=0.3,
                max_tokens=1024,
            )
            model_used = "minimax-m2.5"
        except Exception as e:
            print(f"MiniMax error: {e}", file=sys.stderr)

    # Demo mode - simulate AI response
    if result is None:
        return _demo_process(voice_text)

    # Parse AI response
    try:
        content = result.get("content", "")
        # Strip markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        parsed = json.loads(content)
        parsed["model"] = model_used
        parsed["elapsed"] = result.get("elapsed_seconds", 0)
        return parsed
    except (json.JSONDecodeError, KeyError) as e:
        return {
            "items": [],
            "message": result.get("content", str(e)),
            "language": "zh",
            "model": model_used,
            "parse_error": True,
        }


def _demo_process(voice_text: str) -> dict:
    """Demo mode processing without API keys using keyword matching."""
    text = voice_text.lower()
    items = []
    action = None
    msg = ""

    # Detect checkout intent
    checkout_keywords = ["bill", "check", "confirm", "pay", "checkout", "买单", "结账", "确认", "bayar", "bil", "sahkan"]
    if any(k in text for k in checkout_keywords):
        is_zh = any('\u4e00' <= c <= '\u9fff' for c in text)
        is_ms = any(k in text for k in ["bayar", "bil", "sahkan"])
        
        msg = "好的，正在为您办理结账。" if is_zh else ("Baiklah, sedang memproses bayaran anda." if is_ms else "Sure, processing your checkout now.")
        lang = "zh" if is_zh else ("ms" if is_ms else "en")
        
        return {
            "items": [],
            "message": msg,
            "language": lang,
            "model": "demo-mode",
            "action": "checkout"
        }

    # Simple keyword matching for demo
    keyword_map = {
        # Chinese keywords
        "拿铁": "latte", "美式": "americano", "卡布奇诺": "cappuccino",
        "摩卡": "mocha", "绿茶": "green_tea", "奶茶": "milk_tea",
        "橙汁": "orange_juice", "可乐": "cola",
        "汉堡": "hamburger", "鸡肉卷": "chicken_wrap",
        "意大利面": "pasta", "意面": "pasta",
        "披萨": "pizza", "炒饭": "fried_rice",
        "面条": "noodles", "三明治": "sandwich", "沙拉": "salad",
        "蛋糕": "cake", "冰淇淋": "ice_cream", "甜甜圈": "donut",
        "布朗尼": "brownie", "布丁": "pudding",
        "薯条": "fries", "鸡翅": "chicken_wings",
        "鸡块": "nuggets", "春卷": "spring_rolls",
        # English keywords
        "latte": "latte", "americano": "americano", "cappuccino": "cappuccino",
        "mocha": "mocha", "green tea": "green_tea", "milk tea": "milk_tea",
        "orange juice": "orange_juice", "cola": "cola", "coke": "cola",
        "hamburger": "hamburger", "burger": "hamburger",
        "chicken wrap": "chicken_wrap", "pasta": "pasta",
        "pizza": "pizza", "fried rice": "fried_rice",
        "noodle": "noodles", "sandwich": "sandwich", "salad": "salad",
        "cake": "cake", "ice cream": "ice_cream", "donut": "donut",
        "brownie": "brownie", "pudding": "pudding",
        "fries": "fries", "french fries": "fries",
        "chicken wing": "chicken_wings", "wings": "chicken_wings",
        "nugget": "nuggets", "spring roll": "spring_rolls",
    }

    # Detect quantity patterns
    quantity_map_cn = {
        "一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    }

    found_ids = set()
    for keyword, item_id in keyword_map.items():
        if keyword in text and item_id not in found_ids:
            qty = 1
            # Try to find quantity before keyword
            idx = text.find(keyword)
            before = text[max(0, idx-5):idx]
            for cn_num, val in quantity_map_cn.items():
                if cn_num in before:
                    qty = val
                    break
            # Check for digit quantity
            for ch in before:
                if ch.isdigit():
                    qty = int(ch)
                    break
            items.append({"id": item_id, "quantity": qty})
            found_ids.add(item_id)

    # Determine language
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in voice_text)
    # Common Malay keywords for detection
    malay_keywords = ["saya", "nak", "satu", "dua", "tiga", "makan", "minum", "bayar", "bil", "sahkan"]
    has_malay = any(k in text for k in malay_keywords)
    
    lang = "zh" if has_chinese else ("ms" if has_malay else "en")

    if items:
        if lang == "zh":
            parts = []
            for it in items:
                info = find_item_by_id(it["id"])
                if info: parts.append(f"{info['name_cn']}{it['quantity']}份")
            msg = f"好的！{'、'.join(parts)}，已为您添加到订单中。"
        elif lang == "ms":
            parts = []
            for it in items:
                info = find_item_by_id(it["id"])
                if info: parts.append(f"{it['quantity']}x {info['name_ms']}")
            msg = f"Baiklah! {', '.join(parts)} telah ditambahkan ke pesanan anda."
        else:
            parts = []
            for it in items:
                info = find_item_by_id(it["id"])
                if info: parts.append(f"{it['quantity']}x {info['name_en']}")
            msg = f"Got it! {', '.join(parts)} added to your order."
    else:
        if lang == "zh":
            msg = "抱歉，没听清您要点什么，请再说一次，或者看看我们的菜单。"
        elif lang == "ms":
            msg = "Maaf, saya tidak faham. Sila cuba lagi atau lihat menu."
        else:
            msg = "Sorry, I didn't catch that. Please try again or check our menu."

    return {
        "items": items,
        "message": msg,
        "language": lang,
        "model": "demo-mode",
        "action": None,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/menu")
def api_menu():
    try:
        menu = get_menu_from_db()
        return jsonify(menu)
    except Exception as e:
        print(f"Error fetching menu: {e}")
        return jsonify(MENU) # Fallback to static menu


@app.route("/api/process-voice", methods=["POST"])
def api_process_voice():
    data = request.get_json()
    voice_text = data.get("text", "").strip()
    session_id = data.get("session_id", "default")

    if not voice_text:
        return jsonify({"error": "No text provided"}), 400

    # Get or create cart
    if session_id not in carts:
        carts[session_id] = OrderCart()
    cart = carts[session_id]

    # Process with AI
    ai_result = _process_with_ai(voice_text)

    # Add items to cart
    added_items = []
    for item_data in ai_result.get("items", []):
        item = cart.add_item(item_data["id"], item_data.get("quantity", 1))
        if item:
            added_items.append({
                **item_data,
                "name_cn": item["name_cn"],
                "name_en": item["name_en"],
                "price": item["price"],
                "emoji": item["emoji"],
            })

    return jsonify({
        "voice_text": voice_text,
        "ai_message": ai_result.get("message", ""),
        "language": ai_result.get("language", "zh"),
        "model": ai_result.get("model", "unknown"),
        "added_items": added_items,
        "cart": cart.to_dict(),
        "cart_summary_cn": cart.get_summary_cn(),
        "action": ai_result.get("action"),
    })


@app.route("/api/cart", methods=["GET"])
def api_get_cart():
    session_id = request.args.get("session_id", "default")
    cart = carts.get(session_id, OrderCart())
    return jsonify(cart.to_dict())


@app.route("/api/cart/remove", methods=["POST"])
def api_remove_item():
    data = request.get_json()
    session_id = data.get("session_id", "default")
    item_id = data.get("item_id", "")

    if session_id in carts:
        carts[session_id].remove_item(item_id)
    cart = carts.get(session_id, OrderCart())
    return jsonify(cart.to_dict())


@app.route("/api/cart/clear", methods=["POST"])
def api_clear_cart():
    data = request.get_json()
    session_id = data.get("session_id", "default")
    if session_id in carts:
        carts[session_id].clear()
    return jsonify({"status": "cleared"})


@app.route("/api/confirm-order", methods=["POST"])
def api_confirm_order():
    data = request.get_json()
    session_id = data.get("session_id", "default")

    cart = carts.get(session_id)
    if not cart or not cart.items:
        return jsonify({"error": "Cart is empty"}), 400

    order = {
        "order_id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "items": cart.to_dict()["items"],
        "total": cart.get_total(),
        "item_count": cart.get_item_count(),
    }
    # Save to SQLite Database
    try:
        db_id = save_order_to_db(order["total"], order["items"])
        order["db_id"] = db_id
    except Exception as e:
        print(f"Error saving to DB: {e}")

    cart.clear()

    return jsonify({
        "status": "confirmed",
        "order": order,
        "message_cn": f"订单 {order['order_id']} 已确认！总价 {order['total']:.0f} 元。感谢您的光临！",
        "message_en": f"Order {order['order_id']} confirmed! Total: {order['total']:.0f} yuan. Thank you!",
    })


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    has_glm = bool(os.environ.get("ZHIPU_API_KEY"))
    has_mm = bool(os.environ.get("MINIMAX_API_KEY"))
    mode = "AI" if (has_glm or has_mm) else "DEMO"
    models = []
    if has_glm:
        models.append("GLM-5")
    if has_mm:
        models.append("MiniMax M2.5")

    print("=" * 50)
    print("  Voice Ordering System")
    print("=" * 50)
    print(f"  Mode: {mode}")
    if models:
        print(f"  Models: {', '.join(models)}")
    else:
        print("  (No API keys set - using demo keyword matching)")
        print("  Set ZHIPU_API_KEY or MINIMAX_API_KEY for AI mode")
    print(f"  URL: http://localhost:5000")
    print("=" * 50)

    # Initialize Database
    init_db()

    app.run(debug=True, port=5000)
