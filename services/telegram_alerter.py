import requests
import logging # Standard logging, LoggerSetup is for more complex setups within main app classes
from typing import Dict # For MinimalTokenMetrics

# Using the same placeholder strategy for TokenMetrics
class MinimalTokenMetrics:
    """A minimal placeholder for TokenMetrics for TelegramAlerter."""
    name: str
    symbol: str
    address: str
    price: float
    mcap: float
    liquidity: float
    volume_24h: float
    holders: int
    whale_holdings: Dict[str, float] # Dict[whale_address, percentage]
    volume_trend: str = "unknown"
    volume_acceleration: float = 0.0
    tx_count_trend: str = "unknown"
    risk_factors: list[str] = []

class TelegramAlerter:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        # Using standard logger for utility classes unless they need advanced features
        self.logger = logging.getLogger('TelegramAlerter') 

    def send_gem_alert(self, metrics: MinimalTokenMetrics, score: float, score_breakdown: Dict = None, enhanced_data: Dict = None):
        """ Sends a gem alert. score_breakdown and enhanced_data are optional for extensibility """
        message = (
            f"🚨 <b>Virtuoso Gem Found!</b>\n\n"
            f"Token: {metrics.name} ({metrics.symbol})\n"
            f"Address: <a href=\"https://solscan.io/token/{metrics.address}\">{metrics.address}</a>\n"
            f"💰 Price: ${metrics.price:,.6f}\n"
            f"📊 Market Cap: ${metrics.mcap:,.2f}\n"
            f"💧 Liquidity: ${metrics.liquidity:,.2f}\n"
            f"📈 24h Volume: ${metrics.volume_24h:,.2f}\n"
            f"👥 Holders: {metrics.holders}\n"
            f"⭐ Gem Score: {score:.1f}/100\n"
        )

        if hasattr(metrics, 'volume_trend') and metrics.volume_trend != "unknown":
            trend_emoji_map = {
                "strongly_increasing": "🔥🔥", "increasing": "🔥", "recently_increasing": "📈",
                "stable": "➡️", "decreasing": "📉", "insufficient_data": "❓", "error": "⚠️"
            }
            trend_emoji = trend_emoji_map.get(metrics.volume_trend, "")
            message += f"\n{trend_emoji} Volume Trend: {metrics.volume_trend.replace('_', ' ').title()}"
            if hasattr(metrics, 'volume_acceleration') and metrics.volume_acceleration > 0:
                message += f" (+{metrics.volume_acceleration:.1f}% acceleration)"
                
        if hasattr(metrics, 'tx_count_trend') and metrics.tx_count_trend != "unknown":
            tx_emoji_map = {
                "strongly_increasing": "⚡⚡", "increasing": "⚡", "recently_increasing": "📊",
                "stable": "➡️", "decreasing": "📉", "insufficient_data": "❓", "error": "⚠️"
            }
            tx_emoji = tx_emoji_map.get(metrics.tx_count_trend, "")
            message += f"\n{tx_emoji} Transaction Trend: {metrics.tx_count_trend.replace('_', ' ').title()}"

        if metrics.whale_holdings:
            message += "\n\n🐋 Significant Holders (Top %):\n"
            for whale, percentage in list(metrics.whale_holdings.items())[:3]: # Show top 3 whales
                message += f"• <a href=\"https://solscan.io/account/{whale}\">{whale[:6]}...{whale[-4:]}</a>: {percentage:.1%}\n"

        if score_breakdown: # Add score breakdown if provided
            message += "\n\n📋 Score Breakdown:"
            for component, comp_score in score_breakdown.items():
                if isinstance(comp_score, dict): # Handle nested dicts like enhanced_adjustments
                    message += f"\n  <b>{component.replace('_', ' ').title()}:</b>"
                    for sub_key, sub_value in comp_score.items():
                        message += f"\n    {sub_key.replace('_',' ').title()}: {sub_value:.1f}"
                else:
                    message += f"\n  {component.replace('_', ' ').title()}: {comp_score:.1f}"
        
        if enhanced_data: # Add enhanced analysis data if available
            message += "\n\n🧠 ENHANCED ANALYSIS:"
            if enhanced_data.get("smart_money_analysis"):
                sm = enhanced_data["smart_money_analysis"]
                sm_share = sm.get('smart_money_share', 0) * 100
                sm_holders_count = len(sm.get('smart_money_holders', []))
                message += f"\n🦊 Smart Money: {sm_share:.1f}% supply ({sm_holders_count} wallets)"
            
            if enhanced_data.get("wallet_analysis"):
                wa = enhanced_data["wallet_analysis"]
                dist = wa.get("holder_distribution", {})
                message += (f"\n👛 Wallets: 🐋{dist.get('whale_count',0)} "
                            f"🧠{dist.get('smart_money_count',0)} "
                            f"👥{dist.get('retail_count',0)}")
            
            if enhanced_data.get("behavioral_analysis"):
                bh = enhanced_data["behavioral_analysis"]
                comp_score = bh.get('composite_score', 0) * 100
                warnings = ", ".join(bh.get('warning_flags', []))
                message += f"\n🎯 Behavioral Score: {comp_score:.1f}%"
                if warnings: message += f" (⚠️ {warnings})"
            
            if enhanced_data.get("onchain_momentum_analysis"):
                mom = enhanced_data["onchain_momentum_analysis"]
                overall_mom_score = mom.get('overall_momentum_score', 0) * 100
                message += f"\n🚀 Momentum Score: {overall_mom_score:.1f}%"

        if hasattr(metrics, 'risk_factors') and metrics.risk_factors:
            message += "\n\n⚠️ Risk Factors:\n"
            for risk in metrics.risk_factors[:3]: # Show top 3 risks
                message += f"• {risk}\n"

        message += "\n\n<a href=\"https://dexscreener.com/solana/{metrics.address}\">DexScreener</a> | DYOR! NFA!"
        
        self._send_message_to_telegram(message)

    def send_message(self, message: str, parse_mode: str = 'HTML'): # Generic message sender
        """ Sends a raw message to Telegram. Used for reports or direct comms. """
        self._send_message_to_telegram(message, parse_mode)

    def _send_message_to_telegram(self, text: str, parse_mode: str = 'HTML'):
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Telegram API error ({response.status_code}): {response.text}")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Telegram message: {e}", exc_info=True)
            return False 