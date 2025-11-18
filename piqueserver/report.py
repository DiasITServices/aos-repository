"""

Author: @SouDanielDias
Description: Report system with Discord Webhook support
Version: v1.0.0

Please add this section to Your config.toml piqueserver file

# reports script section
[reports]
discord_webhook_url = "YOUR_DISCORD_WEBHOOK_URL_HERE"

"""

from twisted.internet.defer import Deferred
from twisted.logger import Logger
import aiohttp

from piqueserver.commands import command, player_only, admin, get_player, CommandError
from piqueserver.config import config
from piqueserver.utils import as_deferred

log = Logger()

config_section = config.section("reports")
discord_webhook_url_option = config_section.option("discord_webhook_url", default="")

async def send_discord_webhook(webhook_url, content, embeds=None):
  if not webhook_url:
    log.warn("Missing Discord Webhook URL section in config")
    return False

  payload = {
    "content": content
  }
  
  if embeds:
    payload["embeds"] = embeds

  try:
    async with aiohttp.ClientSession() as session:
      async with session.post(webhook_url, json=payload) as response:
        if response.status in (200, 204):
          log.info("Message sent to Discord successfully")
          return True
        else:
          response_text = await response.text()
          log.warn("Failed to send to Discord: status {status}, response: {resp}", 
            status=response.status, resp=response_text)
          return False

  except Exception as e:
    log.error("Error sending message to Discord: {error}", error=e)
    return False

def send_discord_message(webhook_url, content, embeds=None):
    deferred = Deferred()
    
    async def _send():
        result = await send_discord_webhook(webhook_url, content, embeds)
        deferred.callback(result)
    
    as_deferred(_send()).addErrback(deferred.errback)
    return deferred

@command('report')
@player_only
def report(connection, *args):
  if len(args) < 2:
    return "Use: /report <#id or Nickname> <Report message>"

  target_name = args[0]
  reason = ' '.join(args[1:])

  try:
    target_player = get_player(connection.protocol, target_name)

  except CommandError:
    return f"Player '{target_name}' not found"

  webhook_url = discord_webhook_url_option.get()

  if not webhook_url:
    return "Report system not ready. Please contact a server Admin."

  embed = {
    "title": "🚨 New Report",
    "color": 15158332,
    "fields": [
      {
        "name": "👤 Reported Player",
        "value": f"{target_player.name} (#{target_player.player_id})",
        "inline": True
      },
      {
        "name": "📝 Reporter",
        "value": f"{connection.name} (#{connection.player_id})",
        "inline": True
      },
      {
        "name": "🌐 Reported Player IP",
        "value": target_player.address[0],
        "inline": False
      },
      {
        "name": "🌐 Reporter IP",
        "value": connection.address[0],
        "inline": False
      },
      {
        "name": "📋 Reason",
        "value": reason,
        "inline": False
      },
      {
        "name": "🎮 Server",
        "value": connection.protocol.name,
        "inline": True
      },
      {
        "name": "🗺️ Map",
        "value": connection.protocol.map_info.name,
        "inline": True
      }
    ],
    "timestamp": None
  }

  def on_success(result):
        if result:
            connection.send_chat("✅ Report successfully submitted.")
        else:
            connection.send_chat("❌ Error sendind report. Try again later.")
    
  def on_error(error):
    log.error("Error sending a report for Discord: {error}", error=error)
    connection.send_chat("❌ Error sendind report. Try again later.")
    
  deferred = send_discord_message(webhook_url, "", [embed])
  deferred.addCallback(on_success)
  deferred.addErrback(on_error)

  return f"Sending report for player {target_player.name}."

def apply_script(protocol, connection, config):
  return protocol, connection
