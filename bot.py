import os
import discord
from discord.ext import commands, tasks

from database import get_previous_sale_status, update_sale_status, get_bot_state, set_bot_state
from main import getSteamPrice, getFdevStorePrice, anydealAPIget
from dotenv import load_dotenv
import logging

logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.WARNING)  # Or DEBUG if you want a lot of info

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
# Create a new bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
last_message_id = False
ROLE_ID = os.getenv('ROLE_ID')
last_message_was_sale = False


# Event: Bot is ready and connected
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    logging.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    check_sale.start()


@bot.command(name='sale')
async def sale(channel):
    price_data_backup = False
    data = anydealAPIget()
    embed = discord.Embed(title="Is Elite on sale?")

    if data:
        try:
            for item in data['data']['elitedangerous']['list']:
                if item['shop']['id'] == 'steam':
                    steam_price = item['price_new']
                elif item['shop']['id'] == 'epic':
                    epic_price = item['price_new']
                elif item['shop']['id'] == 'humblestore':
                    humble_price = item['price_new']

            epic_field_value = f'**On sale**: ${epic_price} USD' if epic_price < 29.99 else f'Not on sale: ${epic_price} USD'
            steam_field_value = f'**On sale**: ${steam_price} USD' if steam_price < 29.99 else f'Not on sale: ${steam_price} USD'
            humble_field_value = f'**On sale**: ${humble_price} USD' if humble_price < 29.99 else f'Not on sale: ${humble_price} USD'

            embed.add_field(name="Epic Game Store (https://store.epicgames.com/en-US/p/elite-dangerous)",
                            value=epic_field_value, inline=False)
            embed.add_field(name="Steam (https://store.steampowered.com/app/359320/Elite_Dangerous/)",
                            value=steam_field_value, inline=False)
            embed.add_field(name="Humble Store (https://www.humblebundle.com/store/elite-dangerous)",
                            value=humble_field_value, inline=False)
        except Exception as e:
            print(f'API failure: {e}, running backup...')
            logging.error(f'API failure: {e}, running backup...')
            price_data_backup = True

    if price_data_backup:
        steam_price = getSteamPrice()
        steam_field_value = f'Not on sale: {steam_price}'
        if steam_price != '$29.99':
            steam_field_value = f"**On sale**: {steam_price}"
        embed.add_field(name="Steam (https://store.steampowered.com/app/359320/Elite_Dangerous/)",
                        value=steam_field_value, inline=False)

    fdev_price = getFdevStorePrice()
    fdev_field_value = f'Not on sale: {fdev_price} USD'

    # Convert the fdev_price to a float for comparison
    try:
        fdev_price_float = float(fdev_price.strip('$'))
    except ValueError:
        fdev_price_float = 29.99  # Default value if conversion fails

    if fdev_price_float < 29.99:
        fdev_field_value = f'**On sale**: {fdev_price} USD'

    embed.add_field(name="Frontier Store (https://www.frontierstore.net/usd/)", value=fdev_field_value, inline=False)

    # Role fetching
    role = discord.utils.get(channel.guild.roles, id=int(ROLE_ID))
    if not role:
        print("Sale Watchers role not found!")
        logging.error("Sale Watchers role not found!")
        return

    ping_role = False
    sale_message = ""

    # Loop through all website prices and update the database
    website_prices = [('Steam', steam_price), ('Epic', epic_price), ('Humble', humble_price),
                      ('Fdev', fdev_price_float)]
    for website, price in website_prices:
        prev_status = get_previous_sale_status(website)
        current_status = 1 if price < 29.99 else 0  # 1 for sale, 0 for not on sale

        # Check if the status changed to "on sale"
        if prev_status is not None and current_status == 1 and prev_status == 0:
            ping_role = True
            sale_message += f"{website} is now on sale!\n"

        update_sale_status(website, current_status)

    last_message_id = get_bot_state('last_message_id')
    if last_message_id:
        last_message_id = int(last_message_id)

    last_message_was_sale = get_bot_state('last_message_was_sale') == 'True'

    # Check if a message exists
    if last_message_id:
        try:
            msg = await channel.fetch_message(last_message_id)
            if not ping_role and last_message_was_sale:  # No sale & the last message was a sale ping
                await msg.delete()
                last_message_id = None
                last_message_was_sale = False
            else:
                await msg.edit(embed=embed)
        except discord.NotFound:
            last_message_id = None

    if not last_message_id:
        content_msg = None
        if ping_role:
            content_msg = f"{role.mention} {sale_message}"
            last_message_was_sale = True
        else:
            last_message_was_sale = False

        msg = await channel.send(content=content_msg, embed=embed)
        last_message_id = msg.id

    # Update bot state in the database
    set_bot_state('last_message_id', str(last_message_id))
    set_bot_state('last_message_was_sale', 'True' if last_message_was_sale else 'False')


@tasks.loop(hours=8)
async def check_sale():
    channel = bot.get_channel(int(CHANNEL_ID))
    await sale(channel)


# Run the bot
bot.run(BOT_TOKEN)
