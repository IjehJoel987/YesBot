"""
Modern E-Commerce Telegram Bot
Clean, professional, and easy to manage
"""

import os
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("shop_bot")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
# ============= CONFIGURATION =============
BOT_TOKEN = "7895888177:AAEYLZ9zHxovachLhTIfr7-zs3IYUmxzvng"
OWNER_ID = 5662429081  # Replace with owner's Telegram ID
ADMIN_IDS = {6340039582,7487465564}  # Add more admin IDs here
DATA_FILE = "shop_data.json"

# ============= DATA MODELS =============
@dataclass
class Product:
    id: str
    name: str
    category: str  # "pc", "laptop", "shoes"
    description: str
    price: int
    images: List[str]  # List of file_ids
    in_stock: bool = True

@dataclass
class Order:
    order_id: str
    user_id: int
    username: Optional[str]
    full_name: str
    phone: str
    product_id: str
    product_name: str
    quantity: int
    total_price: int
    delivery_address: str
    status: str  # pending, confirmed, shipped, delivered, cancelled
    timestamp: str

# ============= GLOBAL STORAGE =============
products: Dict[str, Product] = {}
orders: Dict[str, Order] = {}
user_states: Dict[int, Dict] = {}
user_ids_set: set = set()
# ============= DATA PERSISTENCE =============
def save_data():
    """Save all data to JSON file"""
    try:
        data = {
            "products": {pid: asdict(p) for pid, p in products.items()},
            "orders": {oid: asdict(o) for oid, o in orders.items()},
            "admin_ids": list(ADMIN_IDS),
            "user_ids": list(user_ids_set)  # Add this line
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def load_data():
    """Load data from JSON file"""
    global products, orders, ADMIN_IDS
    
    if not os.path.exists(DATA_FILE):
        logger.info("No data file found, starting fresh")
        return
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Load products
        for pid, pdata in data.get("products", {}).items():
            products[pid] = Product(**pdata)
        
        # Load orders
        for oid, odata in data.get("orders", {}).items():
            orders[oid] = Order(**odata)
        
        # Load admin IDs
        if "admin_ids" in data:
            ADMIN_IDS.update(data["admin_ids"])
        # Load user IDs
        if "user_ids" in data:
            user_ids_set.update(data["user_ids"])
        logger.info(f"Loaded {len(products)} products, {len(orders)} orders")
    except Exception as e:
        logger.error(f"Error loading data: {e}")

# ============= HELPER FUNCTIONS =============
def is_admin(user_id: int) -> bool:
    """Check if user is an admin"""
    return user_id in ADMIN_IDS

def generate_order_id() -> str:
    """Generate unique order ID"""
    import random
    return f"ORD{random.randint(10000, 99999)}"

def format_price(amount: int) -> str:
    """Format price in Naira"""
    return f"₦{amount:,}"

def get_timestamp() -> str:
    """Get current timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send notification to all admins"""
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

# ============= USER COMMANDS =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    user = update.effective_user
    
    # Track user
    user_ids_set.add(user.id)
    save_data()

    welcome_text = (
        f"🎉 Welcome {user.first_name}!\n\n"
        f"🛒 Your One-Stop Shop\n\n"
        f"Browse our collection:\n"
        f"Gagdets and Accessories💻⚡️\n"
        f"Your Customized Home🏡(Stickers, books etc.)🤭\n"
        f"Shoes & Jewelleries✨😎\n\n"
        f"Use the menu below to get started! 🚀"
    )
    
    keyboard = [
        [InlineKeyboardButton("Gagdets and Accessories💻⚡️", callback_data="browse_pc")],
        [InlineKeyboardButton("Your Customized Home🏡(Stickers, books etc.)🤭", callback_data="browse_laptop")],
        [InlineKeyboardButton("Shoes & Jewelleries✨😎", callback_data="browse_shoes")],
        [InlineKeyboardButton("📦 My Orders", callback_data="my_orders")],
    ]
    
    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_main_menu(query):
    """Show main menu inline"""
    user = query.from_user
    
    welcome_text = (
        f"🎉 Welcome back {user.first_name}!\n\n"
        f"🛒 <b>Your One-Stop Shop</b>\n\n"
        f"Browse our collection:\n"
        f"Gagdets and Accessories💻⚡️\n"
        f"Your Customized Home🏡(Stickers, books etc.)🤭\n"
        f"Shoes & Jewelleries✨😎\n\n"
        f"Use the menu below to get started! 🚀"
    )
    
    keyboard = [
        [InlineKeyboardButton("Gagdets and Accessories💻⚡️", callback_data="browse_pc")],
        [InlineKeyboardButton("Your Customized Home🏡(Stickers, books etc.)🤭", callback_data="browse_laptop")],
        [InlineKeyboardButton("Shoes & Jewelleries✨😎", callback_data="browse_shoes")],
        [InlineKeyboardButton("📦 My Orders", callback_data="my_orders")],
    ]
    
    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
    
    await query.edit_message_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = (
        "🆘 <b>Help & Commands</b>\n\n"
        "<b>Shopping:</b>\n"
        "/start - Main menu\n"
        "/cancel - Cancel current operation\n"
        "/orders - View your orders\n\n"
    )
    
    if is_admin(update.effective_user.id):
        help_text += (
            "<b>Admin Commands:</b>\n"
            "/admin - Admin panel\n"
            "/addproduct - Add new product\n"
            "/orders_admin - View all orders\n"
            "/broadcast &lt;message&gt; - Send to all users\n"
        )
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    user_id = update.effective_user.id
    if user_id in user_states:
        user_states.pop(user_id, None)
        await update.message.reply_text("❌ Operation cancelled.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
    else:
        await update.message.reply_text("No active operation to cancel.")

# ============= PRODUCT BROWSING =============
async def browse_category(query, category: str):
    """Show products in a category"""
    category_products = [p for p in products.values() if p.category == category and p.in_stock]
    
    if not category_products:
        await query.edit_message_text(
            f"😔 No {category}s available right now.\n\nCheck back soon!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Show product list
    category_names = {"pc": "Gagdets and Accessories💻⚡️", "laptop": "Your Customized Home🏡(Stickers, books etc.)🤭", "shoes": "Shoes & Jewelleries✨😎"}
    text = f"🛍️ <b>{category_names[category]}</b>\n\n"
    
    if category == "pc":
        text += "📝 <b>Note:</b> Every gadget comes with a free case, charger, screenguard & earpiece/earpods/stylus pen depending on the gadget purchase❤️\n\n"
    
    keyboard = []
    for product in category_products:
        if category == "pc":
            text += f"• {product.name} - {format_price(product.price)}\n"
        else:
            text += f"• {product.name}\n"
        keyboard.append([InlineKeyboardButton(
            f"👁️ {product.name}",
            callback_data=f"view_{product.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def view_product(query, product_id: str):
    """Show detailed product view with images"""
    if product_id not in products:
        await query.answer("Product not found!", show_alert=True)
        return
    
    product = products[product_id]
    
    # Prepare caption based on category
    if product.category == "pc":
        caption = (
            f"✨ <b>{product.name}</b>\n\n"
            f"📝 {product.description}\n\n"
            f"💰 <b>Price:</b> {format_price(product.price)}\n"
            f"📦 <b>Status:</b> {'✅ In Stock' if product.in_stock else '❌ Out of Stock'}"
        )
        keyboard = [
            [InlineKeyboardButton("🛒 Order Now", callback_data=f"order_{product_id}")],
            [InlineKeyboardButton("◀️ Back", callback_data=f"browse_{product.category}")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
    else:
        caption = (
            f"✨ <b>{product.name}</b>\n\n"
            f"📝 {product.description}\n\n"
            f"📞 <b>Contact seller for price and availability</b>\n"
            f"📱 Phone: +2349040164120\n"
            f"📢 Telegram: @Tobi_Edmund\n\n"
            f"📦 <b>Status:</b> {'✅ In Stock' if product.in_stock else '❌ Out of Stock'}"
        )
        keyboard = [
            [InlineKeyboardButton("◀️ Back", callback_data=f"browse_{product.category}")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
    
    # Send images
    if product.images:
        if len(product.images) == 1:
            # Single image
            await query.message.reply_photo(
                photo=product.images[0],
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Multiple images as media group
            media = [
                InputMediaPhoto(media=img, caption=caption if i == 0 else None, parse_mode=ParseMode.HTML)
                for i, img in enumerate(product.images[:10])  # Max 10 images
            ]
            await query.message.reply_media_group(media)
            await query.message.reply_text(
                "👆 Swipe to see more images",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        # No images, edit the message
        await query.edit_message_text(
            caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # Delete the original message only if we sent new messages
    if product.images:
        try:
            await query.message.delete()
        except:
            pass

# ============= ORDER FLOW =============
async def start_order(query, product_id: str):
    """Start the ordering process"""
    if product_id not in products:
        await query.answer("Product not found!", show_alert=True)
        return
    
    product = products[product_id]
    user_id = query.from_user.id
    
    # Initialize order state
    user_states[user_id] = {
        "action": "ordering",
        "product_id": product_id,
        "step": "quantity"
    }
    
    await query.edit_message_text(
        f"🛒 <b>Order: {product.name}</b>\n\n"
        f"💰 Price: {format_price(product.price)}\n\n"
        f"📦 How many do you want?\n"
        f"(Type a number, e.g., 1, 2, 3)",
        parse_mode=ParseMode.HTML
    )

async def handle_order_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user input during order process"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id not in user_states or user_states[user_id].get("action") != "ordering":
        return
    
    state = user_states[user_id]
    step = state.get("step")
    
    if step == "quantity":
        try:
            quantity = int(text)
            if quantity <= 0:
                raise ValueError
            state["quantity"] = quantity
            state["step"] = "phone"
            
            product = products[state["product_id"]]
            total = product.price * quantity
            
            await update.message.reply_text(
                f"📦 Quantity: {quantity}\n"
                f"💰 Total: {format_price(total)}\n\n"
                f"📱 Please enter your phone number:",
                parse_mode=ParseMode.HTML
            )
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number (e.g., 1, 2, 3)")
    
    elif step == "phone":
        if not (text.startswith('+') and len(text) >= 10 and text[1:].isdigit()):
            await update.message.reply_text("❌ Please enter a valid phone number (e.g., +2349040164120)")
            return
        state["phone"] = text
        state["step"] = "address"
        await update.message.reply_text(
            "🏠 Great! Now enter your Hall and room number\n"
            "(Include Hall and room number for delivery):"
        )
    
    elif step == "address":
        state["address"] = text
        
        # Create order
        product = products[state["product_id"]]
        quantity = state["quantity"]
        total = product.price * quantity
        
        order_id = generate_order_id()
        order = Order(
            order_id=order_id,
            user_id=user_id,
            username=update.effective_user.username,
            full_name=update.effective_user.full_name,
            phone=state["phone"],
            product_id=state["product_id"],
            product_name=product.name,
            quantity=quantity,
            total_price=total,
            delivery_address=state["address"],
            status="pending",
            timestamp=get_timestamp()
        )
        
        orders[order_id] = order
        save_data()
        
        # Confirmation to user
        await update.message.reply_text(
            f"✅ <b>Order Confirmed!</b>\n\n"
            f"📋 Order ID: `{order_id}`\n"
            f"🛍️ Product: {product.name}\n"
            f"📦 Quantity: {quantity}\n"
            f"💰 Total: {format_price(total)}\n"
            f"📱 Phone: {state['phone']}\n"
            f"🏠 Delivery Address: {state['address']}\n\n"
            f"⏳ Status: Pending confirmation\n\n"
            f"We'll contact you shortly! 🙏",
            parse_mode=ParseMode.HTML
        )
        
        admin_message = (
            f"🚨 <b>NEW ORDER</b>\n\n"
            f"📋 Order ID: `{order_id}`\n"
            f"👤 Customer: {order.full_name}"
            f"{f' (@{order.username})' if order.username else ''}\n"
            f"📱 Phone: {order.phone}\n"
            f"🛍️ Product: {product.name}\n"
            f"📦 Quantity: {quantity}\n"
            f"💰 Total: {format_price(total)}\n"
            f"🏠 Delivery Address: {state['address']}\n"
            f"🕐 Time: {order.timestamp}\n\n"
            
        )
        
        await notify_admins(context, admin_message)
        
        # Clear state
        user_states.pop(user_id, None)

# ============= ORDER MANAGEMENT =============
async def my_orders(query):
    """Show user's orders"""
    user_id = query.from_user.id
    user_orders = [o for o in orders.values() if o.user_id == user_id]
    
    if not user_orders:
        await query.edit_message_text(
            "📭 You haven't placed any orders yet.\n\nStart shopping!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🛍️ Browse Products", callback_data="main_menu")
            ]])
        )
        return
    
    # Sort by timestamp (newest first)
    user_orders.sort(key=lambda x: x.timestamp, reverse=True)
    
    text = "📦 <b>Your Orders</b>\n\n"
    keyboard = []
    
    for order in user_orders[:10]:  # Show last 10 orders
        status_emoji = {
            "pending": "⏳",
            "confirmed": "✅",
            "shipped": "🚚",
            "delivered": "📦",
            "cancelled": "❌"
        }.get(order.status, "⏳")
        
        text += (
            f"{status_emoji} <b>{order.order_id}</b>\n"
            f"   {order.product_name} x{order.quantity}\n"
            f"   {format_price(order.total_price)} - {order.status.title()}\n\n"
        )
        
        keyboard.append([InlineKeyboardButton(
            f"📋 {order.order_id}",
            callback_data=f"order_details_{order.order_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============= ADMIN FUNCTIONS =============
async def admin_panel(query):
    """Show admin panel"""
    if not is_admin(query.from_user.id):
        await query.answer("Access denied!", show_alert=True)
        return
    
    pending_orders = len([o for o in orders.values() if o.status == "pending"])
    total_orders = len(orders)
    total_products = len(products)
    
    text = (
        f"⚙️ <b>Admin Panel</b>\n\n"
        f"📊 <b>Statistics:</b>\n"
        f"• Products: {total_products}\n"
        f"• Total Orders: {total_orders}\n"
        f"• Pending Orders: {pending_orders}\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Product", callback_data="add_product")],
        [InlineKeyboardButton("📦 Manage Orders", callback_data="admin_orders")],
        [InlineKeyboardButton("🛍️ Manage Products", callback_data="manage_products")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_product_start(query):
    """Start add product flow"""
    if not is_admin(query.from_user.id):
        return
    
    user_id = query.from_user.id
    user_states[user_id] = {
        "action": "add_product",
        "step": "category"
    }
    
    keyboard = [
        [InlineKeyboardButton("💻 Laptop(PCs)", callback_data="category_pc")],
        [InlineKeyboardButton("Laptop Stickers", callback_data="category_laptop")],
        [InlineKeyboardButton("👟 Shoes", callback_data="category_shoes")],
    ]
    
    await query.edit_message_text(
        "➕ <b>Add New Product</b>\n\nSelect category:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product addition input"""
    user_id = update.effective_user.id
    
    if user_id not in user_states or user_states[user_id].get("action") != "add_product":
        return
    
    state = user_states[user_id]
    step = state.get("step")
    
    if step == "name":
        state["name"] = update.message.text.strip()
        state["step"] = "description"
        await update.message.reply_text("📝 Enter product description:")
    
    elif step == "description":
        state["description"] = update.message.text.strip()
        state["step"] = "price"
        await update.message.reply_text("💰 Enter price (numbers only, e.g., 50000):")
    
    elif step == "price":
        try:
            price = int(update.message.text.strip())
            if price <= 0:
                raise ValueError
            state["price"] = price
            state["step"] = "images"
            state["images"] = []
            await update.message.reply_text(
                "📸 Send product images (up to 10)\n\n"
                "Type 'done' when finished"
            )
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid price (e.g., 50000)")
    
    elif step == "images":
        if update.message.text and update.message.text.lower() == "done":
            # Save product
            product_id = f"PRD{len(products) + 1:04d}"
            product = Product(
                id=product_id,
                name=state["name"],
                category=state["category"],
                description=state["description"],
                price=state["price"],
                images=state["images"]
            )
            
            products[product_id] = product
            save_data()
            
            await update.message.reply_text(
                f"✅ <b>Product Added!</b>\n\n"
                f"📦 {product.name}\n"
                f"💰 {format_price(product.price)}\n"
                f"📸 {len(product.images)} images\n\n"
                f"<b>Product is now live!</b>",
                parse_mode=ParseMode.HTML
            )
            
            user_states.pop(user_id, None)
        elif update.message.photo:
            # Add photo
            photo = update.message.photo[-1].file_id
            state["images"].append(photo)
            await update.message.reply_text(
                f"✅ Image {len(state['images'])} added!\n\n"
                f"Send more or type 'done' to finish"
            )

async def admin_orders(query):
    """Show all orders to admin"""
    if not is_admin(query.from_user.id):
        return
    
    if not orders:
        await query.edit_message_text(
            "📭 No orders yet.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_panel")
            ]])
        )
        return
    
    # Group by status
    pending = [o for o in orders.values() if o.status == "pending"]
    confirmed = [o for o in orders.values() if o.status == "confirmed"]
    shipped = [o for o in orders.values() if o.status == "shipped"]
    
    text = (
        f"📦 <b>Order Management</b>\n\n"
        f"⏳ Pending: {len(pending)}\n"
        f"✅ Confirmed: {len(confirmed)}\n"
        f"🚚 Shipped: {len(shipped)}\n\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("⏳ Pending Orders", callback_data="orders_pending")],
        [InlineKeyboardButton("✅ Confirmed Orders", callback_data="orders_confirmed")],
        [InlineKeyboardButton("🚚 Shipped Orders", callback_data="orders_shipped")],
        [InlineKeyboardButton("📋 All Orders", callback_data="orders_all")],
        [InlineKeyboardButton("◀️ Back", callback_data="admin_panel")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============= CALLBACK HANDLER =============
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # Main menu
    if data == "main_menu":
        await show_main_menu(query)
        return
    
    # Browse categories
    if data.startswith("browse_"):
        category = data.replace("browse_", "")
        await browse_category(query, category)
        return
    
    # View product
    if data.startswith("view_"):
        product_id = data.replace("view_", "")
        await view_product(query, product_id)
        return
    
    # Start order
    if data.startswith("order_"):
        product_id = data.replace("order_", "")
        await start_order(query, product_id)
        return
    
    # My orders
    if data == "my_orders":
        await my_orders(query)
        return
    
    # Admin panel
    if data == "admin_panel":
        await admin_panel(query)
        return
    
    # Add product
    if data == "add_product":
        await add_product_start(query)
        return
    
    # Product category selection
    if data.startswith("category_"):
        category = data.replace("category_", "")
        user_id = query.from_user.id
        if user_id in user_states and user_states[user_id].get("action") == "add_product":
            user_states[user_id]["category"] = category
            user_states[user_id]["step"] = "name"
            await query.edit_message_text("📝 Enter product name:")
        return
    
    # Admin orders
    if data == "admin_orders":
        await admin_orders(query)
        return

# ============= MESSAGE HANDLER =============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_id = update.effective_user.id
    
    # Check if user is in a flow
    if user_id in user_states:
        action = user_states[user_id].get("action")
        
        if action == "ordering":
            await handle_order_input(update, context)
            return
        elif action == "add_product":
            await handle_add_product(update, context)
            return

# ============= ADMIN COMMANDS =============
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only command")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /broadcast <message>\n\n"
            "Example: /broadcast Hello everyone! New products available!"
        )
        return
    
    message = " ".join(context.args)
    
    # Use tracked user IDs instead of just order users
    total_users = len(user_ids_set)
    sent = 0
    failed = 0
    
    await update.message.reply_text(f"📤 Broadcasting to {total_users} users...")
    
    for user_id in user_ids_set:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>Announcement</b>\n\n{message}",
                parse_mode=ParseMode.HTML
            )
            sent += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send to {user_id}: {e}")
    
    await update.message.reply_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {total_users}"
    )

# ============= ERROR HANDLER =============
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error: {context.error}")

# ============= MAIN =============
def main():
    """Start the bot"""
    load_data()
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your BOT_TOKEN in the code")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_add_product))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    logger.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

