"""
Menu Data & Order Management
=============================
Restaurant menu with categories, prices, and order cart logic.
Supports Chinese and English item names.
"""

# ---------------------------------------------------------------------------
# Menu Data
# ---------------------------------------------------------------------------

MENU = {
    "drinks": {
        "name_cn": "饮品",
        "name_en": "Drinks",
        "name_ms": "Minuman",
        "items": [
            {"id": "latte",       "name_cn": "拿铁咖啡",   "name_en": "Latte",           "name_ms": "Kopi Latte",      "price": 28.0, "emoji": "☕"},
            {"id": "americano",   "name_cn": "美式咖啡",   "name_en": "Americano",       "name_ms": "Kopi Americano",  "price": 22.0, "emoji": "☕"},
            {"id": "cappuccino",  "name_cn": "卡布奇诺",   "name_en": "Cappuccino",      "name_ms": "Kapucino",        "price": 30.0, "emoji": "☕"},
            {"id": "mocha",       "name_cn": "摩卡咖啡",   "name_en": "Mocha",           "name_ms": "Kopi Mocha",      "price": 32.0, "emoji": "☕"},
            {"id": "green_tea",   "name_cn": "绿茶",       "name_en": "Green Tea",       "name_ms": "Teh Hijau",       "price": 18.0, "emoji": "🍵"},
            {"id": "milk_tea",    "name_cn": "奶茶",       "name_en": "Milk Tea",        "name_ms": "Teh Susu",        "price": 20.0, "emoji": "🧋"},
            {"id": "orange_juice","name_cn": "橙汁",       "name_en": "Orange Juice",    "name_ms": "Jus Oren",        "price": 22.0, "emoji": "🧃"},
            {"id": "cola",        "name_cn": "可乐",       "name_en": "Cola",            "name_ms": "Kola",            "price": 10.0, "emoji": "🥤"},
        ]
    },
    "food": {
        "name_cn": "主食",
        "name_en": "Main Courses",
        "name_ms": "Hidangan Utama",
        "items": [
            {"id": "hamburger",    "name_cn": "汉堡",       "name_en": "Hamburger",       "name_ms": "Burger",          "price": 35.0, "emoji": "🍔"},
            {"id": "chicken_wrap", "name_cn": "鸡肉卷",     "name_en": "Chicken Wrap",    "name_ms": "Wrap Ayam",       "price": 28.0, "emoji": "🌯"},
            {"id": "pasta",        "name_cn": "意大利面",   "name_en": "Pasta",           "name_ms": "Pasta",           "price": 38.0, "emoji": "🍝"},
            {"id": "pizza",        "name_cn": "披萨",       "name_en": "Pizza",           "name_ms": "Piza",            "price": 45.0, "emoji": "🍕"},
            {"id": "fried_rice",   "name_cn": "炒饭",       "name_en": "Fried Rice",      "name_ms": "Nasi Goreng",     "price": 25.0, "emoji": "🍚"},
            {"id": "noodles",      "name_cn": "面条",       "name_en": "Noodles",         "name_ms": "Mi",              "price": 22.0, "emoji": "🍜"},
            {"id": "sandwich",     "name_cn": "三明治",     "name_en": "Sandwich",        "name_ms": "Sandwic",         "price": 26.0, "emoji": "🥪"},
            {"id": "salad",        "name_cn": "沙拉",       "name_en": "Salad",           "name_ms": "Salad",           "price": 30.0, "emoji": "🥗"},
        ]
    },
    "desserts": {
        "name_cn": "甜品",
        "name_en": "Desserts",
        "name_ms": "Pencuci Mulut",
        "items": [
            {"id": "cake",         "name_cn": "蛋糕",       "name_en": "Cake",            "name_ms": "Kek",             "price": 28.0, "emoji": "🍰"},
            {"id": "ice_cream",    "name_cn": "冰淇淋",     "name_en": "Ice Cream",       "name_ms": "Aiskrim",         "price": 18.0, "emoji": "🍦"},
            {"id": "donut",        "name_cn": "甜甜圈",     "name_en": "Donut",           "name_ms": "Donat",           "price": 12.0, "emoji": "🍩"},
            {"id": "brownie",      "name_cn": "布朗尼",     "name_en": "Brownie",         "name_ms": "Brownie",         "price": 22.0, "emoji": "🍫"},
            {"id": "pudding",      "name_cn": "布丁",       "name_en": "Pudding",         "name_ms": "Puding",          "price": 16.0, "emoji": "🍮"},
        ]
    },
    "sides": {
        "name_cn": "小食",
        "name_en": "Sides",
        "name_ms": "Makanan Sampingan",
        "items": [
            {"id": "fries",        "name_cn": "薯条",       "name_en": "French Fries",    "name_ms": "Kentang Goreng",  "price": 15.0, "emoji": "🍟"},
            {"id": "chicken_wings","name_cn": "鸡翅",       "name_en": "Chicken Wings",   "name_ms": "Kepak Ayam",      "price": 25.0, "emoji": "🍗"},
            {"id": "nuggets",      "name_cn": "鸡块",       "name_en": "Chicken Nuggets", "name_ms": "Nuget Ayam",      "price": 20.0, "emoji": "🍗"},
            {"id": "spring_rolls", "name_cn": "春卷",       "name_en": "Spring Rolls",    "name_ms": "Popia",           "price": 18.0, "emoji": "🥟"},
        ]
    }
}


def get_all_items() -> list[dict]:
    """Return a flat list of all menu items."""
    items = []
    for cat_data in MENU.values():
        items.extend(cat_data["items"])
    return items


def get_menu_for_prompt() -> str:
    """Generate a text description of the menu for the AI prompt."""
    lines = ["Available Menu:"]
    for cat_key, cat_data in MENU.items():
        lines.append(f"\n## {cat_data['name_cn']} ({cat_data['name_en']} / {cat_data['name_ms']})")
        for item in cat_data["items"]:
            lines.append(
                f"  - {item['name_cn']} ({item['name_en']} / {item['name_ms']}) "
                f"- {item['price']} yuan - ID: {item['id']}"
            )
    return "\n".join(lines)


def find_item_by_id(item_id: str) -> dict | None:
    """Look up a menu item by its ID."""
    for cat_data in MENU.values():
        for item in cat_data["items"]:
            if item["id"] == item_id:
                return item
    return None


def get_menu_json() -> dict:
    """Return menu as JSON-serializable dict for the frontend."""
    return MENU


# ---------------------------------------------------------------------------
# Order Cart
# ---------------------------------------------------------------------------

class OrderCart:
    """Simple order cart for managing items."""

    def __init__(self):
        self.items: list[dict] = []  # [{"item": {...}, "quantity": N}]
        self.order_id: str | None = None

    def add_item(self, item_id: str, quantity: int = 1) -> dict | None:
        """Add item to cart. Returns the item if found, None otherwise."""
        item = find_item_by_id(item_id)
        if not item:
            return None
        # Check if already in cart
        for entry in self.items:
            if entry["item"]["id"] == item_id:
                entry["quantity"] += quantity
                return item
        self.items.append({"item": item, "quantity": quantity})
        return item

    def remove_item(self, item_id: str) -> bool:
        """Remove item from cart."""
        for i, entry in enumerate(self.items):
            if entry["item"]["id"] == item_id:
                self.items.pop(i)
                return True
        return False

    def clear(self):
        """Clear the cart."""
        self.items = []

    def get_total(self) -> float:
        """Calculate total price."""
        return sum(e["item"]["price"] * e["quantity"] for e in self.items)

    def get_item_count(self) -> int:
        """Total number of items."""
        return sum(e["quantity"] for e in self.items)

    def to_dict(self) -> dict:
        """Serialize cart for JSON response."""
        return {
            "items": [
                {
                    "id": e["item"]["id"],
                    "name_cn": e["item"]["name_cn"],
                    "name_en": e["item"]["name_en"],
                    "emoji": e["item"]["emoji"],
                    "price": e["item"]["price"],
                    "quantity": e["quantity"],
                    "subtotal": e["item"]["price"] * e["quantity"],
                }
                for e in self.items
            ],
            "total": self.get_total(),
            "item_count": self.get_item_count(),
        }

    def get_summary_cn(self) -> str:
        """Chinese summary for voice readback."""
        if not self.items:
            return "购物车是空的。"
        parts = []
        for e in self.items:
            parts.append(f"{e['item']['name_cn']}{e['quantity']}份")
        return (
            f"您的订单包含：{'、'.join(parts)}。"
            f"共{self.get_item_count()}件商品，"
            f"总价{self.get_total():.0f}元。"
        )
