import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, SERVER_TYPES
from utils import init_database, register_user, get_user, get_server_status
from server_manager import ServerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize server manager
server_manager = ServerManager()


class BotUI:
    """Telegram bot UI class."""
    
    @staticmethod
    def main_menu() -> tuple:
        """Get main menu text and keyboard."""
        total_servers = server_manager.get_server_count()
        running_servers = server_manager.get_running_count()
        
        text = f'''⚙️ Minecraft Server Manager

Servers: {total_servers}
Running: {running_servers}'''
        
        keyboard = [
            [
                InlineKeyboardButton('Servers', callback_data='menu_servers'),
                InlineKeyboardButton('Create Server', callback_data='menu_create')
            ]
        ]
        
        return text, InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def servers_menu() -> tuple:
        """Get servers list menu."""
        servers = server_manager.get_servers()
        
        text = 'Servers\n\n'
        
        if not servers:
            text += '(No servers yet)'
            keyboard = [
                [InlineKeyboardButton('Back', callback_data='menu_main')]
            ]
        else:
            for name, server in servers.items():
                status_symbol = '▶️' if get_server_status(server) == 'running' else '⏹️'
                text += f'{status_symbol} {name}\n'
            
            keyboard = []
            for name in servers.keys():
                keyboard.append([InlineKeyboardButton(name, callback_data=f'server_{name}')])
            
            keyboard.append([InlineKeyboardButton('Back', callback_data='menu_main')])
        
        return text, InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def server_detail_menu(server_name: str) -> tuple:
        """Get server detail menu."""
        servers = server_manager.get_servers()
        
        if server_name not in servers:
            text = 'Server not found'
            keyboard = [
                [InlineKeyboardButton('Back', callback_data='menu_servers')]
            ]
            return text, InlineKeyboardMarkup(keyboard)
        
        server = servers[server_name]
        status = get_server_status(server)
        status_text = '▶️ running' if status == 'running' else '⏹️ stopped'
        
        text = f'''Server: {server_name}
Status: {status_text}
Port: {server.get('port', 'N/A')}
Type: {server.get('type', 'N/A').capitalize()}'''
        
        keyboard = []
        
        if status == 'running':
            keyboard.append([
                InlineKeyboardButton('Stop', callback_data=f'action_stop_{server_name}'),
                InlineKeyboardButton('Restart', callback_data=f'action_restart_{server_name}')
            ])
        else:
            keyboard.append([
                InlineKeyboardButton('Start', callback_data=f'action_start_{server_name}')
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton('Logs', callback_data=f'action_logs_{server_name}'),
                InlineKeyboardButton('Delete', callback_data=f'action_delete_{server_name}')
            ],
            [InlineKeyboardButton('Back', callback_data='menu_servers')]
        ])
        
        return text, InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_server_menu() -> tuple:
        """Get create server menu."""
        text = '''Create Server

Select server type:'''
        
        keyboard = []
        for key, name in SERVER_TYPES.items():
            keyboard.append([InlineKeyboardButton(name, callback_data=f'create_{key}')])
        
        keyboard.append([InlineKeyboardButton('Back', callback_data='menu_main')])
        
        return text, InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    try:
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name
        
        # Register user in database
        register_user(user_id, username)
        
        text, keyboard = BotUI.main_menu()
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = update.effective_user
        
        # Main menu navigation
        if data == 'menu_main':
            text, keyboard = BotUI.main_menu()
            await query.edit_message_text(text=text, reply_markup=keyboard)
        
        elif data == 'menu_servers':
            text, keyboard = BotUI.servers_menu()
            await query.edit_message_text(text=text, reply_markup=keyboard)
        
        elif data == 'menu_create':
            text, keyboard = BotUI.create_server_menu()
            await query.edit_message_text(text=text, reply_markup=keyboard)
        
        # Server selection
        elif data.startswith('server_'):
            server_name = data.replace('server_', '')
            text, keyboard = BotUI.server_detail_menu(server_name)
            await query.edit_message_text(text=text, reply_markup=keyboard)
        
        # Server actions
        elif data.startswith('action_'):
            parts = data.split('_', 2)
            action = parts[1]
            server_name = parts[2] if len(parts) > 2 else ''
            
            if action == 'start':
                if server_manager.start_server(server_name):
                    await query.answer('Server started', show_alert=False)
                else:
                    await query.answer('Failed to start server', show_alert=True)
            
            elif action == 'stop':
                if server_manager.stop_server(server_name):
                    await query.answer('Server stopped', show_alert=False)
                else:
                    await query.answer('Failed to stop server', show_alert=True)
            
            elif action == 'restart':
                await query.answer('Restarting server...', show_alert=False)
                if server_manager.restart_server(server_name):
                    await query.answer('Server restarted', show_alert=False)
                else:
                    await query.answer('Failed to restart server', show_alert=True)
            
            elif action == 'logs':
                logs = server_manager.get_server_logs(server_name, 20)
                log_text = f'📄 Logs for {server_name}:\n\n'
                log_text += f'```\n{logs[-2000:]}\n```'
                
                text, keyboard = BotUI.server_detail_menu(server_name)
                await query.edit_message_text(text=text, reply_markup=keyboard)
                
                await context.bot.send_message(
                    chat_id=user.id,
                    text=log_text,
                    parse_mode='Markdown'
                )
            
            elif action == 'delete':
                if server_manager.delete_server(server_name):
                    await query.answer('Server deleted', show_alert=False)
                    text, keyboard = BotUI.servers_menu()
                    await query.edit_message_text(text=text, reply_markup=keyboard)
                else:
                    await query.answer('Failed to delete server', show_alert=True)
            
            # Refresh server detail menu after action
            if action in ['start', 'stop', 'restart']:
                text, keyboard = BotUI.server_detail_menu(server_name)
                await query.edit_message_text(text=text, reply_markup=keyboard)
        
        # Create server actions
        elif data.startswith('create_'):
            server_type = data.replace('create_', '')
            
            # For simplicity, create a server with default name
            import time
            server_name = f'server_{int(time.time() % 10000)}'
            
            await query.answer('Creating server...', show_alert=False)
            
            server = server_manager.create_server(server_name, server_type)
            
            if server:
                # Get IP address
                ip = server_manager.get_available_ip()
                port = server.get('port', 25565)
                
                info_text = f'''✅ Server Created!

Name: {server_name}
Type: {server.get("type", "").capitalize()}
Address: {ip}:{port}
Port: {port}
Status: created

Starting server...'''
                
                text, keyboard = BotUI.main_menu()
                await query.edit_message_text(text=info_text)
                
                # Start the server
                if server_manager.start_server(server_name):
                    info_text += '\n✅ Server started!'
                    await context.bot.send_message(
                        chat_id=user.id,
                        text=info_text
                    )
                
                text, keyboard = BotUI.main_menu()
                await context.bot.send_message(
                    chat_id=user.id,
                    text=text,
                    reply_markup=keyboard
                )
            else:
                await query.answer('Failed to create server', show_alert=True)
    
    except Exception as e:
        logger.error(f"Error in button callback: {e}")
        await query.answer('Error occurred', show_alert=True)


def main():
    """Start the bot."""
    try:
        # Initialize database
        init_database()
        
        # Create application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CallbackQueryHandler(button_callback))
        
        logger.info("Bot started successfully")
        
        # Start the bot
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
