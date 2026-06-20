import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import config
import database
import engine

# Enable Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Active Match Tracking Dictionary
# Structure: { group_chat_id: { "lobby": [], "engine": MatchEngine, "batter": id, "bowler": id, "status": str } }
ACTIVE_MATCHES = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command for both Groups and DMs."""
    chat = update.effective_chat
    user = update.effective_user
    
    # Register user in database if they don't exist
    database.get_user(user.id, user.username or user.first_name)

    if chat.type in ["group", "supergroup"]:
        # Group Start Presentation
        text = (
            "🏏 **INFERNO LEGACY**\n\n"
            "The Ultimate Hand Cricket Platform.\n\n"
            "⚡ Create Solo Battles\n"
            "👥 Build Teams\n"
            "📊 Track Stats\n"
            "🏆 Build Your Legacy"
        )
        keyboard = [
            [InlineKeyboardButton("🏏 Solo Mode", callback_data="init_solo")],
            [InlineKeyboardButton("👥 Team Mode", callback_data="init_team")],
            [InlineKeyboardButton("🏟️ Inferno Playzone", callback_data="playzone")]
        ]
    else:
        # DM Start Presentation
        text = (
            "🏏 **INFERNO LEGACY**\n\n"
            "The Ultimate Hand Cricket Experience.\n\n"
            "📊 Career Statistics\n"
            "🏆 Global Rankings\n"
            "🎖️ Achievements & Badges\n"
            "🔥 Become An Inferno Legend"
        )
        keyboard = [
            [InlineKeyboardButton("🏟️ Inferno Playzone", callback_data="playzone")],
            [InlineKeyboardButton("👤 Profile", callback_data="view_profile")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="view_leaderboard")],
            [InlineKeyboardButton("➕ Add To Group", url=f"https://t.me/{(await context.bot.get_me()).username}?startgroup=true")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await chat.send_message(text, reply_markup=reply_markup, parse_mode="Markdown")

async def join_solo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows players to join a solo lobby via /joinsolo."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if chat_id not in ACTIVE_MATCHES:
        ACTIVE_MATCHES[chat_id] = {"lobby": [], "status": "LOBBY", "engine": None}
        
    match = ACTIVE_MATCHES[chat_id]
    
    if match["status"] != "LOBBY":
        await update.message.reply_text("❌ A match is already in progress in this group!")
        return

    if user.id not in match["lobby"]:
        match["lobby"].append(user.id)
        # Register user dynamically
        database.get_user(user.id, user.username or user.first_name)
        await update.message.reply_text(f"✅ {user.mention_markdown_v2()} joined the solo lobby! ({len(match['lobby'])} players)")
    else:
        await update.message.reply_text("⚠️ You are already in this lobby.")

async def force_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows an admin to manually jumpstart the game loop via /forcestart."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized. Admin access required.")
        return

    if chat_id not in ACTIVE_MATCHES or len(ACTIVE_MATCHES[chat_id]["lobby"]) < 2:
        await update.message.reply_text("❌ Cannot start. Need at least 2 players in the lobby.")
        return

    match = ACTIVE_MATCHES[chat_id]
    match["status"] = "PLAYING"
    match["engine"] = engine.MatchEngine(max_overs=2) # Initialize a standard 2-over quick match
    
    # Assign Initial Roles based on join order sequencing
    match["batter"] = match["lobby"][0]
    match["bowler"] = match["lobby"][1]
    
    await update.message.reply_text("🔥 **MATCH STARTED!**\n\nSetting up Hidden DM Bowling interface...")
    await prompt_bowler(context, chat_id)

async def prompt_bowler(context: ContextTypes.DEFAULT_TYPE, group_id: int):
    """Sends a private message to the bowler to input their secret play number."""
    match = ACTIVE_MATCHES[group_id]
    bowler_id = match["bowler"]
    
    # Update group chat regarding status delivery
    await context.bot.send_message(
        chat_id=group_id,
        text=f"🏟️ **DELIVERY**\n🎯 Bowler: User [{bowler_id}]\n🏏 Batter: User [{match['batter']}]\n\n📩 Bowler, check your DM."
    )
    
    # Setup interactive numbers 1-6
    keyboard = [[InlineKeyboardButton(str(i), callback_data=f"bowl_{group_id}_{i}") for i in range(1, 4)],
                [InlineKeyboardButton(str(i), callback_data=f"bowl_{group_id}_{i}") for i in range(4, 7)]]
    
    try:
        await context.bot.send_message(
            chat_id=bowler_id,
            text="🏏 **YOUR TURN TO BOWL**\n\nChoose your delivery number secretly:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        await context.bot.send_message(
            chat_id=group_id,
            text=f"❌ Error: Bowler [{bowler_id}] needs to initiate a DM conversation with this bot first!"
        )

async def handle_bowler_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Catches the secret delivery data value from the DM callback."""
    query = update.callback_query
    await query.answer()
    
    # Parse data string formatting: bowl_{group_id}_{number}
    _, group_id_str, target_num = query.data.split("_")
    group_id = int(group_id_str)
    
    if group_id not in ACTIVE_MATCHES:
        await query.edit_message_text("❌ This match instance has expired or completed.")
        return

    match = ACTIVE_MATCHES[group_id]
    match["current_delivery"] = int(target_num)
    
    await query.edit_message_text(f"🎯 Delivery locked on value: **{target_num}**! Awaiting batter action...")
    
    # Now alert the group and show the interactive batting prompt buttons inside the group channel
    keyboard = [[InlineKeyboardButton(str(i), callback_data=f"bat_{group_id}_{i}") for i in range(0, 4)],
                [InlineKeyboardButton(str(i), callback_data=f"bat_{group_id}_{i}") for i in range(4, 7)]]
                
    await context.bot.send_message(
        chat_id=group_id,
        text=f"⚾ **BALL DELIVERED**\n🏏 Batter Player [{match['batter']}], send your shot choice:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_batter_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes the public batting selection and resolves the delivery collision context."""
    query = update.callback_query
    user_id = query.from_user.id
    
    _, group_id_str, target_num = query.data.split("_")
    group_id = int(group_id_str)
    
    if group_id not in ACTIVE_MATCHES:
        await query.answer("Match not found.", show_alert=True)
        return
        
    match = ACTIVE_MATCHES[group_id]
    
    if user_id != match["batter"]:
        await query.answer("⚠️ You are not the active batter!", show_alert=True)
        return
        
    await query.answer()
    
    batter_shot = int(target_num)
    bowler_delivery = match["current_delivery"]
    
    # Execute structural collision calculations using MatchEngine instance
    result = match["engine"].delivery(batter_shot, bowler_delivery)
    
    # Evaluate event state tree structures
    if result["event"] == "wicket":
        text_announcement = f"💀 **WICKET!** Batter picked {batter_shot} and Bowler delivered {bowler_delivery}. Out!"
        # Clean up lobby metadata context elements for next round sequences
        ACTIVE_MATCHES.pop(group_id, None)
        await query.edit_message_text(f"{text_announcement}\n\n🏆 Match Ended. Resetting lobby settings.")
    else:
        text_announcement = (
            f"🏏 **RUNS SCORED!**\n\n"
            f"Batter chose: {batter_shot}\n"
            f"Bowler chose: {bowler_delivery}\n"
            f"Runs awarded: +{result['runs_scored']}\n\n"
            f"📊 **Score:** {result['total_runs']}/{result['total_wickets']} ({result['overs']} Overs)"
        )
        
        # Check condition states for next delivery execution steps
        if match["engine"].balls >= match["engine"].max_balls:
            await query.edit_message_text(f"{text_announcement}\n\n🏁 **Innings completed over maximum delivery boundaries!**")
            ACTIVE_MATCHES.pop(group_id, None)
        else:
            await query.edit_message_text(text_announcement)
            # Route logic flow backwards smoothly into standard operational looping states
            await prompt_bowler(context, group_id)

def main():
    """Initializes the operational interface loop framework bindings configuration structures."""
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Commands Hook Rules Layout Routing Definitions
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("joinsolo", join_solo))
    application.add_handler(CommandHandler("forcestart", force_start))
    
    # Callback Query Direct Match Routing Operations
    application.add_handler(CallbackQueryHandler(handle_bowler_input, pattern=r"^bowl_"))
    application.add_handler(CallbackQueryHandler(handle_batter_input, pattern=r"^bat_"))

    print("🔥 INFERNO LEGACY ENGINE INITIALIZED AND RUNNING...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    