import requests
import logging # Standard logging, LoggerSetup is for more complex setups within main app classes
from typing import Dict, Optional, List # For MinimalTokenMetrics
from dataclasses import dataclass, field
from services.logger_setup import LoggerSetup # Added import
from utils.structured_logger import get_structured_logger
import time
import html
import json
from pathlib import Path

# Convert to proper dataclass with constructor
@dataclass
class MinimalTokenMetrics:
    """A minimal dataclass for TokenMetrics for TelegramAlerter."""
    symbol: str
    address: str
    price: float
    name: str = ""
    mcap: float = 0.0
    liquidity: float = 0.0
    volume_24h: float = 0.0
    holders: int = 0
    price_change_24h: float = 0.0
    market_cap: float = 0.0
    score: float = 0.0
    whale_holdings: Dict[str, float] = field(default_factory=dict) # Dict[whale_address, percentage]
    volume_trend: str = "unknown"
    volume_acceleration: float = 0.0
    tx_count_trend: str = "unknown"
    risk_factors: List[str] = field(default_factory=list)

class TelegramAlerter:
    def __init__(self, bot_token: str, chat_id: str, config: Optional[Dict] = None, logger_setup: Optional[LoggerSetup] = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.config = config if config is not None else {}
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Retry configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 2.0)
        self.timeout = self.config.get('timeout', 15)
        
        if logger_setup:
            self.logger = logger_setup.logger # Use logger from passed setup
        else:
            # Fallback if no logger_setup is provided (though VGF passes one)
            # For consistency, use LoggerSetup if available, otherwise standard logging
            try:
                from services.logger_setup import LoggerSetup # Local import for fallback
                self.logger = LoggerSetup('TelegramAlerter').logger
            except ImportError:
                self.logger = logging.getLogger('TelegramAlerter')
        
        self.structured_logger = get_structured_logger('AlertingService')
        
        # Alert tracking
        self.failed_alerts_log = Path("data/failed_alerts.json")
        Path("data").mkdir(exist_ok=True)

    def send_gem_alert(self, metrics: MinimalTokenMetrics, score: float, score_breakdown: Optional[dict] = None, enhanced_data: Optional[dict] = None, pair_address: Optional[str] = None, scan_id: Optional[str] = None):
        """Send optimized gem alert designed for Telegram's HTML parser and visual appeal"""
        try:
            self.structured_logger.info({"event": "alert_send_attempt", "alert_type": "telegram", "scan_id": scan_id, "recipient": self.chat_id, "token": metrics.address, "alert_content": str(metrics), "timestamp": int(time.time())})
            # Build message in sections to stay under Telegram's 4096 character limit
            sections = []
            
            # 🎯 HEADER SECTION - Visually striking with score-based styling
            header = self._build_header_section(metrics, score)
            sections.append(header)
            
            # 💎 CORE METRICS - Key financial data
            core_metrics = self._build_core_metrics_section(metrics, enhanced_data)
            sections.append(core_metrics)
            
            # 🔢 SCORING BREAKDOWN - Enhanced with detailed scoring analysis
            scoring_breakdown_section = self._build_scoring_breakdown_section(enhanced_data, score_breakdown)
            if scoring_breakdown_section:
                sections.append(scoring_breakdown_section)
            
            # 🔍 DISCOVERY DETAILS - How the token was found
            discovery_details = self._build_discovery_details_section(enhanced_data)
            if discovery_details:
                sections.append(discovery_details)
            
            # 🔍 PUMP/DUMP ANALYSIS - Our enhanced trading analysis
            pump_dump_analysis = enhanced_data.get('enhanced_pump_dump_analysis') if enhanced_data else None
            if pump_dump_analysis:
                trading_analysis = self._build_trading_analysis_section(pump_dump_analysis)
                sections.append(trading_analysis)
            
            # 🌐 ENHANCED METADATA ANALYSIS - Social media and community insights
            enhanced_metadata = enhanced_data.get('enhanced_metadata_analysis') if enhanced_data else None
            if enhanced_metadata:
                metadata_section = self._build_enhanced_metadata_section(enhanced_metadata)
                sections.append(metadata_section)
            
            # 🔒 SECURITY & RISK
            security_section = self._build_security_section(metrics, enhanced_data)
            sections.append(security_section)
            
            # 🔗 QUICK ACTIONS - Trading and exploration links
            actions_section = self._build_actions_section(metrics.address)
            sections.append(actions_section)
            
            # Combine sections with clean separators
            full_message = "\n\n".join(filter(None, sections))
            
            # Ensure message is under Telegram's limit
            if len(full_message) > 4000:  # Leave buffer for safety
                self.logger.warning(f"Message too long ({len(full_message)} chars), using compact format")
                full_message = self._build_compact_alert(metrics, score, pump_dump_analysis)
            
            # Send with retry logic
            success = self._send_message_with_retry(full_message, scan_id, metrics)
            if success:
                self.structured_logger.info({"event": "alert_send_result", "alert_type": "telegram", "scan_id": scan_id, "recipient": self.chat_id, "token": metrics.address, "result": "success", "timestamp": int(time.time())})
                self.logger.info(f"Successfully sent gem alert for {metrics.symbol}")
                return True
            else:
                self.structured_logger.error({"event": "alert_send_result", "alert_type": "telegram", "scan_id": scan_id, "recipient": self.chat_id, "token": metrics.address, "result": "failure", "timestamp": int(time.time())})
                self.logger.error(f"Failed to send gem alert for {metrics.symbol}")
                return False
                
        except Exception as e:
            self.structured_logger.error({"event": "alert_send_result", "alert_type": "telegram", "scan_id": scan_id, "recipient": self.chat_id, "token": metrics.address, "result": "error", "error": str(e), "timestamp": int(time.time())})
            self.logger.error(f"Error building gem alert for {metrics.symbol}: {e}")
            # Send basic fallback alert
            self._send_basic_fallback_alert(metrics, score)

    def _build_header_section(self, metrics: MinimalTokenMetrics, score: float) -> str:
        """Build visually striking header section"""
        # Score-based emoji and styling with intelligent classification
        if score >= 90:
            emoji = "🚀🔥💎"
            status = "PREMIUM GEM"
        elif score >= 80:
            emoji = "🚀🔥"
            status = "HIGH POTENTIAL"
        elif score >= 70:
            emoji = "🚀"
            status = "PROMISING"
        elif score >= 50:
            emoji = "📈💎"
            status = "SOLID OPPORTUNITY"
        elif score >= 30:  # Lowered threshold from 35 to 30
            emoji = "📊💎"
            status = "HIGH CONVICTION"
        elif score >= 20:  # Lowered threshold from 25 to 20
            emoji = "📊"
            status = "WATCH LIST"
        else:
            emoji = "🔍"
            status = "INVESTIGATION"
        
        # Clean HTML-safe formatting
        symbol = html.escape(str(metrics.symbol))
        name = html.escape(str(metrics.name))
        
        header = f"{emoji} <b>VIRTUOSO GEM DETECTED</b> {emoji}\n"
        header += f"<b>{status}</b>\n"
        header += f"<b>Token:</b> {name} ({symbol})\n"
        header += f"<b>Score:</b> {score if isinstance(score, (int, float)) else 0:.1f}/100"
        
        return header

    def _build_core_metrics_section(self, metrics: MinimalTokenMetrics, enhanced_data: Optional[dict]) -> str:
        """Build core financial metrics section with enhanced details"""
        lines = ["💎 <b>CORE METRICS</b>"]
        
        # Price with smart formatting
        if metrics.price < 0.000001:
            price_str = f"${metrics.price:.8f}"
        elif metrics.price < 0.01:
            price_str = f"${metrics.price:.6f}"
        elif metrics.price < 1:
            price_str = f"${metrics.price:.4f}"
        else:
            price_str = f"${metrics.price if isinstance(metrics.price, (int, float)) else 0:.2f}"
        
        lines.append(f"💰 <b>Price:</b> {price_str}")
        
        # Market data with safe formatting
        if metrics.market_cap > 0:
            lines.append(f"📊 <b>Market Cap:</b> ${metrics.market_cap:,.0f}")
        
        if metrics.liquidity > 0:
            lines.append(f"🌊 <b>Liquidity:</b> ${metrics.liquidity:,.0f}")
        
        if metrics.volume_24h > 0:
            lines.append(f"📈 <b>24h Volume:</b> ${metrics.volume_24h:,.0f}")
        
        if metrics.holders > 0:
            lines.append(f"👥 <b>Holders:</b> {metrics.holders:,}")
        
        # Add cross-platform analysis if available
        if enhanced_data and 'cross_platform_analysis' in enhanced_data:
            cross_platform = enhanced_data['cross_platform_analysis']
            platforms = cross_platform.get('platforms', [])
            cross_platform_score = cross_platform.get('cross_platform_score', 0)
            
            if platforms:
                platform_str = ', '.join(platforms)
                lines.append(f"🌐 <b>Platforms:</b> {platform_str}")
            
            if cross_platform_score > 0:
                lines.append(f"🎯 <b>Cross-Platform Score:</b> {cross_platform_score if isinstance(cross_platform_score, (int, float)) else 0:.1f}")
        
        # Add volume and price trend indicators
        if hasattr(metrics, 'volume_trend') and metrics.volume_trend != 'unknown':
            trend_emoji = {
                'increasing': '📈',
                'decreasing': '📉',
                'stable': '➡️',
                'bullish': '🟢',
                'bearish': '🔴'
            }.get(metrics.volume_trend, '📊')
            lines.append(f"{trend_emoji} <b>Volume Trend:</b> {metrics.volume_trend}")
        
        # Add price change if available
        if metrics.price_change_24h != 0:
            change_emoji = "🟢" if metrics.price_change_24h > 0 else "🔴"
            lines.append(f"{change_emoji} <b>24h Change:</b> {metrics.price_change_24h:+.2f}%")
        
        return "\n".join(lines)

    def _build_trading_analysis_section(self, pump_dump_analysis: Dict) -> str:
        """Build enhanced trading analysis section"""
        try:
            current_phase = pump_dump_analysis.get('current_phase', 'UNKNOWN')
            overall_risk = pump_dump_analysis.get('overall_risk', 'UNKNOWN')
            trading_opportunities = pump_dump_analysis.get('trading_opportunities', [])
            phase_confidence = pump_dump_analysis.get('phase_confidence', 0)
            
            # Phase with emoji
            phase_emoji = {
                'EARLY_PUMP': '🟢',
                'MOMENTUM_PUMP': '🟡', 
                'EXTREME_PUMP': '🔥',
                'DUMP_START': '🔴',
                'DUMP_CONTINUATION': '⬇️',
                'CRASH': '💥',
                'CONSOLIDATION': '⚖️',
                'NEUTRAL': '⚪'
            }.get(current_phase, '❓')
            
            # Risk emoji
            risk_emoji = {
                'LOW': '✅',
                'MEDIUM': '⚠️', 
                'HIGH': '🚨',
                'CRITICAL': '💀'
            }.get(overall_risk, '❓')
            
            lines = [
                "🔍 <b>TRADING ANALYSIS</b>",
                f"{phase_emoji} <b>Phase:</b> {current_phase}",
                f"🎯 <b>Confidence:</b> {phase_confidence if isinstance(phase_confidence, (int, float)) else 0:.0%}",
                f"{risk_emoji} <b>Risk Level:</b> {overall_risk}"
            ]
            
            # Add primary trading opportunity
            if trading_opportunities:
                primary_opp = trading_opportunities[0]
                action = primary_opp.get('action', 'UNKNOWN')
                confidence = primary_opp.get('confidence', 0)
                
                if action == 'ENTER':
                    profit_target = primary_opp.get('estimated_profit_potential', 0)
                    max_hold = primary_opp.get('max_hold_time_minutes', 0)
                    lines.extend([
                        "",
                        "🎯 <b>ENTRY OPPORTUNITY</b>",
                        f"📈 <b>Target:</b> {profit_target if isinstance(profit_target, (int, float)) else 0:.0f}%",
                        f"⏰ <b>Hold Time:</b> {max_hold} min",
                        f"⚡ <b>Confidence:</b> {confidence if isinstance(confidence, (int, float)) else 0:.0%}"
                    ])
                    
                elif action == 'ENTER_HIGH_RISK':
                    profit_target = primary_opp.get('estimated_profit_potential', 0)
                    max_hold = primary_opp.get('max_hold_time_minutes', 0)
                    lines.extend([
                        "",
                        "🔥 <b>HIGH-RISK SCALP</b>",
                        "⚠️ <b>EXPERIENCED TRADERS ONLY</b>",
                        f"📈 <b>Quick Target:</b> {profit_target if isinstance(profit_target, (int, float)) else 0:.0f}%",
                        f"⏰ <b>Max Hold:</b> {max_hold} min",
                        f"⚡ <b>Confidence:</b> {confidence if isinstance(confidence, (int, float)) else 0:.0%}",
                        "🚨 <b>EXTREME RISK - TIGHT STOPS</b>"
                    ])
                    
                elif action == 'EXIT':
                    expected_loss = primary_opp.get('estimated_profit_potential', 0)
                    lines.extend([
                        "",
                        "🚨 <b>EXIT SIGNAL</b>",
                        f"⚠️ <b>Expected Loss:</b> {expected_loss if isinstance(expected_loss, (int, float)) else 0:.0f}%",
                        "<b>EXIT IMMEDIATELY</b>"
                    ])
                    
                elif action == 'MONITOR':
                    lines.extend([
                        "",
                        "👀 <b>MONITOR CLOSELY</b>",
                        f"⚡ <b>Confidence:</b> {confidence if isinstance(confidence, (int, float)) else 0:.0%}"
                    ])
            
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.warning(f"Error building trading analysis: {e}")
            return "🔍 <b>TRADING ANALYSIS</b>\n❓ Analysis unavailable"

    def _build_enhanced_metadata_section(self, enhanced_metadata: Dict) -> str:
        """Build enhanced metadata analysis section with social media presence"""
        try:
            lines = ["🌐 <b>COMMUNITY & METADATA</b>"]
            
            # Social Media Analysis
            social_analysis = enhanced_metadata.get('social_analysis', {})
            if social_analysis:
                social_score = social_analysis.get('social_score', 0)
                community_strength = social_analysis.get('community_strength', 'Unknown')
                social_channels = social_analysis.get('social_channels', [])
                
                # Social presence with emoji
                strength_emoji = {
                    'Strong': '🟢',
                    'Moderate': '🟡', 
                    'Weak': '🟠',
                    'Very Weak': '🔴',
                    'Unknown': '❓'
                }.get(community_strength, '❓')
                
                lines.append(f"{strength_emoji} <b>Community:</b> {community_strength} ({social_score}/100)")
                
                if social_channels:
                    # Format social channels with emojis
                    channel_emojis = {
                        'website': '🌐',
                        'twitter': '🐦',
                        'telegram': '📱',
                        'discord': '💬',
                        'medium': '📝',
                        'reddit': '🤖',
                        'github': '💻'
                    }
                    
                    channel_list = []
                    for channel in social_channels[:4]:  # Limit to 4 to save space
                        emoji = channel_emojis.get(channel, '🔗')
                        channel_list.append(f"{emoji}{channel.title()}")
                    
                    if len(social_channels) > 4:
                        channel_list.append(f"+{len(social_channels) - 4} more")
                    
                    lines.append(f"📱 <b>Channels:</b> {' '.join(channel_list)}")
            
            # Trading Momentum from metadata
            trading_analysis = enhanced_metadata.get('trading_analysis', {})
            if trading_analysis:
                trading_momentum = trading_analysis.get('trading_momentum', 'Neutral')
                volume_acceleration = trading_analysis.get('volume_acceleration', 0)
                
                momentum_emoji = {
                    'Very Strong': '🚀🚀',
                    'Strong': '🚀',
                    'Moderate': '📈',
                    'Weak': '📉',
                    'Very Weak': '⬇️',
                    'Neutral': '➡️'
                }.get(trading_momentum, '➡️')
                
                lines.append(f"{momentum_emoji} <b>Momentum:</b> {trading_momentum}")
                
                if volume_acceleration > 0:
                    lines.append(f"⚡ <b>Volume Accel:</b> {{volume_acceleration if isinstance(volume_acceleration, (int, float)) else 0:.0f}}/100")
            
            # Key strengths and risks from metadata
            metadata_score = enhanced_metadata.get('metadata_score', {})
            if metadata_score:
                key_strengths = metadata_score.get('key_strengths', [])
                key_risks = metadata_score.get('key_risks', [])
                
                # Add top strength
                if key_strengths:
                    lines.append(f"✅ <b>Top Strength:</b> {key_strengths[0]}")
                
                # Add critical risk if any
                if key_risks:
                    critical_risks = [risk for risk in key_risks if 'critical' in risk.lower() or 'high risk' in risk.lower()]
                    if critical_risks:
                        lines.append(f"⚠️ <b>Risk:</b> {critical_risks[0]}")
                    elif key_risks:
                        lines.append(f"⚠️ <b>Note:</b> {key_risks[0]}")
            
            return "\n".join(lines)
        
        except Exception as e:
            self.logger.error(f"Error building enhanced metadata section: {e}")
            return "🌐 <b>COMMUNITY & METADATA</b>\n❓ Analysis unavailable"

    def _build_security_section(self, metrics: MinimalTokenMetrics, enhanced_data: Optional[dict]) -> str:
        """Build security and risk section"""
        lines = ["🔒 <b>SECURITY STATUS</b>"]
        
        # Security status
        if enhanced_data and 'security_info' in enhanced_data:
            sec = enhanced_data['security_info']
            if sec.get('is_scam'):
                lines.append("🚨 <b>WARNING: Flagged as potential scam</b>")
            elif sec.get('is_risky'):
                lines.append("⚠️ <b>CAUTION: Flagged as risky</b>")
            else:
                lines.append("✅ <b>Clean - No major security flags</b>")
        else:
            lines.append("✅ <b>No immediate security concerns</b>")
        
        # Add risk factors if available
        if hasattr(metrics, 'risk_factors') and metrics.risk_factors:
            lines.append("")
            lines.append("⚠️ <b>Risk Factors:</b>")
            for risk in metrics.risk_factors[:2]:  # Limit to 2 risks
                lines.append(f"• {self._html_escape(str(risk))}")
        
        return "\n".join(lines)

    def _build_actions_section(self, address: str) -> str:
        """Build quick action links section"""
        lines = [
            "🔗 <b>QUICK ACTIONS</b>",
            f"📊 <a href='https://birdeye.so/token/{address}?chain=solana'>View Chart</a>",
            f"📈 <a href='https://dexscreener.com/solana/{address}'>Dexscreener</a>",
            f"🚀 <a href='https://raydium.io/swap/?inputCurrency=sol&outputCurrency={address}'>Trade Now</a>",
            "",
            f"<code>{address}</code>"
        ]
        return "\n".join(lines)

    def _build_scoring_breakdown_section(self, enhanced_data: Optional[dict] = None, score_breakdown: Optional[dict] = None) -> str:
        """Build comprehensive scoring breakdown section with detailed 115-point analysis"""
        lines = ["🔢 <b>SCORING BREAKDOWN</b>"]
        
        # ENHANCEMENT: Display detailed 115-point scoring breakdown if available
        if score_breakdown:
            lines.append(f"📊 <b>DETAILED SCORING ANALYSIS (115-Point System)</b>")
            
            # Base score
            base_score = score_breakdown.get('base_score', 0)
            lines.append(f"  🏗️ <b>Base Score:</b> {base_score:.1f}")
            
            # Component scores with detailed breakdown
            components = [
                ('overview_analysis', '📊 Overview Analysis', 20),
                ('whale_analysis', '🐋 Whale Analysis', 15),
                ('volume_price_analysis', '📈 Volume/Price Analysis', 15),
                ('community_analysis', '👥 Community Analysis', 10),
                ('security_analysis', '🔒 Security Analysis', 10),
                ('trading_activity', '💹 Trading Activity', 10),
                ('dex_analysis', '🏪 DEX Analysis', 10),
                ('vlr_analysis', '💎 VLR Intelligence', 15)
            ]
            
            total_component_score = 0
            for component_key, component_name, max_score in components:
                if component_key in score_breakdown:
                    component_data = score_breakdown[component_key]
                    component_score = component_data.get('score', 0)
                    total_component_score += component_score
                    
                    lines.append(f"  {component_name}: {component_score:.1f}/{max_score}")
                    
                    # Add specific details for key components
                    if component_key == 'overview_analysis' and component_score > 0:
                        market_cap = component_data.get('market_cap', 0)
                        liquidity = component_data.get('liquidity', 0)
                        if market_cap > 0:
                            lines.append(f"    💰 Market Cap: ${market_cap:,.0f}")
                        if liquidity > 0:
                            lines.append(f"    🌊 Liquidity: ${liquidity:,.0f}")
                    
                    elif component_key == 'whale_analysis' and component_score > 0:
                        whale_concentration = component_data.get('whale_concentration', 0)
                        smart_money = component_data.get('smart_money_detected', False)
                        if whale_concentration > 0:
                            lines.append(f"    🐋 Whale Concentration: {whale_concentration:.1f}%")
                        if smart_money:
                            lines.append(f"    🧠 Smart Money: ✅")
                    
                    elif component_key == 'vlr_analysis' and component_score > 0:
                        vlr = component_data.get('vlr', 0)
                        gem_potential = component_data.get('gem_potential', 'LOW')
                        if vlr > 0:
                            lines.append(f"    💎 VLR: {vlr:.2f}")
                        lines.append(f"    🎯 Gem Potential: {gem_potential}")
            
            # Final score calculation
            final_calculated = base_score + total_component_score
            lines.append(f"  <b>🎯 FINAL SCORE: {final_calculated:.1f}/115</b>")
            
            # Score interpretation
            if final_calculated >= 90:
                interpretation = "🚀 PREMIUM GEM - Exceptional opportunity"
            elif final_calculated >= 80:
                interpretation = "🔥 HIGH POTENTIAL - Strong investment candidate"
            elif final_calculated >= 70:
                interpretation = "📈 PROMISING - Good opportunity with solid fundamentals"
            elif final_calculated >= 60:
                interpretation = "💎 SOLID OPPORTUNITY - Worth monitoring"
            elif final_calculated >= 50:
                interpretation = "📊 HIGH CONVICTION - Meets threshold requirements"
            else:
                interpretation = "🔍 INVESTIGATION - Below conviction threshold"
            
            lines.append(f"  📝 <b>Interpretation:</b> {interpretation}")
            
            # 🔍 FACTOR INTERACTION ANALYSIS - CONCISE FORMAT
            interaction_analysis = score_breakdown.get('interaction_analysis', {})
            if interaction_analysis:
                lines.append("")  # Spacing
                lines.append("🔍 <b>FACTOR INTERACTION ANALYSIS</b>")
                
                # Create a single concise line with key findings
                analysis_parts = []
                
                # Danger Detection (most critical - show first)
                danger_interactions = interaction_analysis.get('danger_interactions', [])
                if danger_interactions:
                    top_danger = danger_interactions[0]  # Show only the most critical
                    explanation = top_danger.get('explanation', 'Danger detected')
                    # Shorten common explanations
                    short_explanation = explanation.replace('High VLR + Low Liquidity = Manipulation', 'VLR/Liquidity Risk')
                    short_explanation = short_explanation.replace('Whale Dominance + Poor Security', 'Whale/Security Risk')
                    short_explanation = short_explanation.replace(' + ', '+')
                    analysis_parts.append(f"🚨 {short_explanation}")
                else:
                    analysis_parts.append("🚨 No Dangers ✅")
                
                # Signal Amplification (positive signals)
                amplification_interactions = interaction_analysis.get('amplification_interactions', [])
                if amplification_interactions:
                    top_amp = amplification_interactions[0]  # Show only the strongest
                    explanation = top_amp.get('explanation', 'Signal amplified')
                    impact = top_amp.get('impact', 0)
                    # Shorten common explanations
                    short_explanation = explanation.replace('Smart Money + Volume Surge', 'Smart Money+Volume')
                    short_explanation = short_explanation.replace('Multi-Platform + Security', 'Multi-Platform+Security')
                    short_explanation = short_explanation.replace(' + ', '+')
                    analysis_parts.append(f"🚀 {short_explanation} (+{impact:.0f}%)")
                
                # Contradictions (if significant)
                contradiction_interactions = interaction_analysis.get('contradiction_interactions', [])
                if contradiction_interactions:
                    top_contradiction = contradiction_interactions[0]
                    impact = top_contradiction.get('impact', 0)
                    if abs(impact) > 5:  # Only show if significant
                        explanation = top_contradiction.get('explanation', 'Mixed signals')
                        short_explanation = explanation.replace('High Volume vs Limited Platforms', 'Volume/Platform Mismatch')
                        short_explanation = short_explanation.replace(' vs ', '/')
                        analysis_parts.append(f"⚖️ {short_explanation} ({impact:+.0f}%)")
                
                # Risk Assessment
                risk_assessment = score_breakdown.get('risk_assessment', {})
                if risk_assessment:
                    risk_level = risk_assessment.get('risk_level', 'UNKNOWN')
                    confidence_level = risk_assessment.get('confidence_level', 0)
                    confidence_pct = confidence_level * 100 if isinstance(confidence_level, float) else confidence_level
                    analysis_parts.append(f"🎯 {risk_level} ({confidence_pct:.0f}%)")
                
                # Combine all parts into one concise line
                if analysis_parts:
                    lines.append(f"  {' | '.join(analysis_parts)}")
                
                # Mathematical improvement (only if very significant)
                score_comparison = score_breakdown.get('score_comparison', {})
                if score_comparison:
                    improvement = score_comparison.get('mathematical_improvement', 0)
                    if abs(improvement) > 15:  # Only show if very significant improvement
                        linear_score = score_comparison.get('linear_score_flawed', 0)
                        interaction_score = score_comparison.get('interaction_score_corrected', 0)
                        lines.append(f"  🧠 <b>AI Enhancement:</b> {linear_score:.0f}→{interaction_score:.0f} ({improvement:+.0f}%)")
        
        # Fallback to enhanced_data if no detailed breakdown available
        elif enhanced_data:
            # Cross-platform analysis breakdown
            if 'cross_platform_analysis' in enhanced_data:
                cross_platform = enhanced_data['cross_platform_analysis']
                cross_platform_score = cross_platform.get('cross_platform_score', 0)
                
                # Safe float conversion
                try:
                    score_val = float(cross_platform_score) if cross_platform_score else 0
                    lines.append(f"📊 <b>Cross-Platform:</b> {score_val if isinstance(score_val, (int, float)) else 0:.1f}/100")
                except (ValueError, TypeError):
                    lines.append(f"📊 <b>Cross-Platform:</b> {cross_platform_score}/100")
                
                # Platform-specific details
                platforms = cross_platform.get('platforms', [])
                if platforms:
                    lines.append(f"  🌐 Found on: {', '.join(platforms)}")
                
                # Boost data if available
                boost_data = cross_platform.get('boost_data', {})
                if boost_data and boost_data.get('amount', 0) > 0:
                    try:
                        amount = float(boost_data.get('amount', 0))
                        lines.append(f"  🚀 DexScreener Boost: ${amount:,.0f}")
                    except (ValueError, TypeError):
                        lines.append(f"  🚀 DexScreener Boost: ${boost_data.get('amount', 0)}")
                
                # Community data
                community_data = cross_platform.get('community_data', {})
                if community_data and community_data.get('vote_count', 0) > 0:
                    try:
                        sentiment = float(community_data.get('sentiment_score', 0))
                        votes = int(community_data.get('vote_count', 0))
                        lines.append(f"  👥 Community: {sentiment if isinstance(sentiment, (int, float)) else 0:.1%} positive ({votes} votes)")
                    except (ValueError, TypeError):
                        sentiment = community_data.get('sentiment_score', 0)
                        votes = community_data.get('vote_count', 0)
                        lines.append(f"  👥 Community: {sentiment} positive ({votes} votes)")
            
            # Detailed analysis breakdown
            analysis_sections = [
                ('whale_analysis', '🐋 Whale Analysis'),
                ('volume_price_analysis', '📈 Volume/Price'),
                ('community_boost_analysis', '🚀 Community Boost'),
                ('security_analysis', '🔒 Security'),
                ('trading_activity', '💹 Trading Activity')
            ]
            
            for section_key, section_name in analysis_sections:
                if section_key in enhanced_data:
                    section_data = enhanced_data[section_key]
                    if isinstance(section_data, dict):
                        # Try to extract meaningful metrics with safe formatting
                        if section_key == 'whale_analysis':
                            whale_count = section_data.get('whale_holder_count', 0)
                            whale_percentage = section_data.get('whale_holdings_percentage', 0)
                            if whale_count > 0:
                                try:
                                    count = int(whale_count)
                                    percentage = float(whale_percentage)
                                    lines.append(f"  🐋 Whales: {count} holders ({percentage if isinstance(percentage, (int, float)) else 0:.1f}%)")
                                except (ValueError, TypeError):
                                    lines.append(f"  🐋 Whales: {whale_count} holders ({whale_percentage}%)")
                        
                        elif section_key == 'volume_price_analysis':
                            volume_trend = section_data.get('volume_trend', 'unknown')
                            price_momentum = section_data.get('price_momentum', 0)
                            if volume_trend != 'unknown':
                                lines.append(f"  📊 Volume Trend: {volume_trend}")
                            if price_momentum != 0:
                                try:
                                    momentum = float(price_momentum)
                                    lines.append(f"  💹 Price Momentum: {momentum if isinstance(momentum, (int, float)) else 0:.2f}")
                                except (ValueError, TypeError):
                                    lines.append(f"  💹 Price Momentum: {price_momentum}")
                        
                        elif section_key == 'security_analysis':
                            risk_score = section_data.get('risk_score', 0)
                            security_flags = section_data.get('security_flags', [])
                            if risk_score > 0:
                                try:
                                    score = float(risk_score)
                                    lines.append(f"  🔒 Risk Score: {score if isinstance(score, (int, float)) else 0:.1f}/10")
                                except (ValueError, TypeError):
                                    lines.append(f"  🔒 Risk Score: {risk_score}/10")
                            if security_flags:
                                lines.append(f"  ⚠️ Flags: {', '.join(security_flags)}")
        
        return "\n".join(lines) if len(lines) > 1 else ""

    def _build_discovery_details_section(self, enhanced_data: Optional[dict]) -> str:
        """Build section showing how the token was discovered"""
        if not enhanced_data or 'cross_platform_analysis' not in enhanced_data:
            return ""
        
        lines = ["🔍 <b>DISCOVERY DETAILS</b>"]
        
        cross_platform = enhanced_data['cross_platform_analysis']
        platforms = cross_platform.get('platforms', [])
        
        # Platform-specific discovery info
        platform_details = []
        if 'DexScreener' in platforms:
            platform_details.append("📱 DexScreener trending")
        if 'Birdeye' in platforms:
            platform_details.append("🐦 Birdeye analytics")
        if 'RugCheck' in platforms:
            platform_details.append("🛡️ RugCheck community")
        
        if platform_details:
            lines.append(f"  📊 Sources: {', '.join(platform_details)}")
        
        # Boost information
        boost_data = cross_platform.get('boost_data', {})
        if boost_data:
            amount = boost_data.get('amount', 0)
            total_amount = boost_data.get('totalAmount', 0)
            description = boost_data.get('description', '')
            
            if amount > 0:
                lines.append(f"  🚀 Boost Amount: ${amount:,}")
                if total_amount > amount:
                    lines.append(f"  💰 Total Boost Pool: ${total_amount:,}")
                if description:
                    # Truncate description to keep alert readable
                    desc_short = description[:100] + "..." if len(description) > 100 else description
                    lines.append(f"  📝 Description: {self._html_escape(desc_short)}")
        
        return "\n".join(lines) if len(lines) > 1 else ""

    def _build_compact_alert(self, metrics: MinimalTokenMetrics, score: float, pump_dump_analysis: Optional[Dict]) -> str:
        """Build compact alert for when full message is too long"""
        symbol = self._html_escape(metrics.symbol)
        name = self._html_escape(metrics.name)
        
        # Score-based emoji
        emoji = "🚀🔥" if score >= 80 else "🚀" if score >= 70 else "📈"
        
        lines = [
            f"{emoji} <b>GEM ALERT</b> {emoji}",
            f"<b>{name} ({symbol})</b>",
            f"<b>Score:</b> {score if isinstance(score, (int, float)) else 0:.1f}/100",
            "",
            f"💰 <b>Price:</b> ${metrics.price:.6f}",
            f"🌊 <b>Liquidity:</b> ${metrics.liquidity:,.0f}",
            f"📈 <b>Volume:</b> ${metrics.volume_24h:,.0f}",
        ]
        
        # Add trading phase if available
        if pump_dump_analysis:
            phase = pump_dump_analysis.get('current_phase', 'UNKNOWN')
            confidence = pump_dump_analysis.get('phase_confidence', 0)
            lines.extend([
                "",
                f"🔍 <b>Phase:</b> {phase}",
                f"🎯 <b>Confidence:</b> {confidence if isinstance(confidence, (int, float)) else 0:.0%}"
            ])
        
        lines.extend([
            "",
            f"<a href='https://birdeye.so/token/{metrics.address}?chain=solana'>📊 View Chart</a>",
            f"<code>{metrics.address[:8]}...{metrics.address[-6:]}</code>"
        ])
        
        return "\n".join(lines)

    def _send_basic_fallback_alert(self, metrics: MinimalTokenMetrics, score: float):
        """Send basic fallback alert in case of errors"""
        try:
            symbol = self._html_escape(metrics.symbol)
            emoji = "🚀" if score >= 70 else "📈"
            
            message = f"{emoji} <b>GEM ALERT</b>\n"
            message += f"<b>{symbol}</b>\n"
            message += f"<b>Score:</b> {score if isinstance(score, (int, float)) else 0:.1f}/100\n"
            message += f"<b>Price:</b> ${metrics.price:.6f}\n"
            message += f"<code>{metrics.address[:8]}...{metrics.address[-6:]}</code>"
            
            self._send_message_to_telegram(message)
            self.logger.info(f"Sent fallback alert for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Failed to send fallback alert: {e}")

    def _html_escape(self, text: str) -> str:
        """Escape HTML special characters for Telegram"""
        if not isinstance(text, str):
            text = str(text)
        
        # Escape HTML entities that could cause parsing issues
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        
        return text

    def _safe_format_number(self, value, format_spec: str, default_value=0):
        """Safely format a number with the given format specification"""
        try:
            if value is None:
                return str(default_value)
            if isinstance(value, str):
                # Try to convert string to number
                if '.' in value or 'e' in value.lower():
                    num_value = float(value)
                else:
                    num_value = int(value)
            else:
                num_value = float(value)
            return format(num_value, format_spec)
        except (ValueError, TypeError):
            # If conversion fails, return the value as string
            return str(value)

    def send_message(self, message: str, parse_mode: str = 'HTML'): # Generic message sender
        """ Sends a raw message to Telegram. Used for reports or direct comms. """
        return self._send_message_to_telegram(message, parse_mode)

    def _send_message_with_retry(self, text: str, scan_id: str = None, metrics = None) -> bool:
        """Send message with retry logic and proper error handling"""
        alert_id = f"{scan_id or 'unknown'}_{int(time.time())}"
        attempts = []
        delay = self.retry_delay
        
        for attempt_num in range(1, self.max_retries + 1):
            try:
                success = self._send_message_to_telegram(text)
                
                if success:
                    self.logger.debug(f"✅ Message sent successfully on attempt {attempt_num}")
                    return True
                
                # Check if we should retry
                if attempt_num < self.max_retries:
                    self.logger.info(f"🔄 Retrying in {delay:.1f}s (attempt {attempt_num + 1}/{self.max_retries})")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                
            except Exception as e:
                self.logger.error(f"❌ Exception on attempt {attempt_num}: {e}")
                if attempt_num < self.max_retries:
                    time.sleep(delay)
                    delay *= 2
        
        # Log failed alert
        if metrics:
            self._log_failed_alert(alert_id, metrics, attempts)
        
        return False
    
    def _send_message_to_telegram(self, text: str, parse_mode: str = 'HTML'):
        """Send message to Telegram with enhanced error handling and validation"""
        if not text or len(text.strip()) == 0:
            self.logger.warning("Attempted to send empty message")
            return False
        
        # Validate message length
        if len(text) > 4096:
            self.logger.warning(f"Message too long ({len(text)} chars), truncating")
            text = text[:4090] + "..."
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                self.logger.debug("Message sent successfully")
                return True
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {'description': response.text}
                error_desc = error_data.get('description', 'Unknown error')
                
                # Handle specific error cases
                if 'parse entities' in error_desc.lower():
                    self.logger.warning(f"HTML parsing error, attempting plain text fallback: {error_desc}")
                    # Retry with plain text
                    return self._send_plain_text_fallback(text)
                elif 'message is too long' in error_desc.lower():
                    self.logger.warning("Message too long, using compact format")
                    return False  # Let caller handle compact format
                elif response.status_code == 429:
                    retry_after = error_data.get('parameters', {}).get('retry_after', 30)
                    self.logger.warning(f"Rate limited, should retry after {retry_after}s")
                    return False
                else:
                    self.logger.error(f"Telegram API error ({response.status_code}): {error_desc}")
                    return False
                    
        except requests.exceptions.Timeout:
            self.logger.error(f"Telegram request timed out after {self.timeout}s")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending message: {e}")
            return False

    def _send_plain_text_fallback(self, html_text: str) -> bool:
        """Send plain text version as fallback when HTML parsing fails"""
        try:
            # Strip HTML tags for plain text version
            import re
            plain_text = re.sub('<[^<]+?>', '', html_text)
            plain_text = plain_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
            
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': plain_text,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                self.logger.info("Sent plain text fallback message successfully")
                return True
            else:
                self.logger.error(f"Plain text fallback also failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Plain text fallback error: {e}")
            return False
    
    def _log_failed_alert(self, alert_id: str, metrics, attempts: list):
        """Log failed alert for debugging"""
        try:
            failed_alert = {
                "alert_id": alert_id,
                "timestamp": time.time(),
                "token_address": metrics.address,
                "token_symbol": metrics.symbol,
                "attempts": len(attempts),
                "error": "Failed after all retry attempts"
            }
            
            # Load existing failed alerts
            if self.failed_alerts_log.exists():
                with open(self.failed_alerts_log, 'r') as f:
                    failed_alerts = json.load(f)
            else:
                failed_alerts = []
            
            failed_alerts.append(failed_alert)
            
            # Keep only last 50 failed alerts
            failed_alerts = failed_alerts[-50:]
            
            with open(self.failed_alerts_log, 'w') as f:
                json.dump(failed_alerts, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to log failed alert: {e}")
    
    def send_test_message(self, message: str = "🎤 Test message from Telegram Alerter") -> bool:
        """Send a test message to verify connectivity with retry logic"""
        return self._send_message_with_retry(message)

    def send_photo(self, photo, caption: str = None):
        """Send a photo/image to Telegram chat. Accepts a file-like object or file path."""
        url = f"{self.base_url}/sendPhoto"
        data = {'chat_id': self.chat_id}
        if caption:
            data['caption'] = caption
            data['parse_mode'] = 'HTML'
        files = {'photo': photo} if hasattr(photo, 'read') else {'photo': open(photo, 'rb')}
        try:
            response = requests.post(url, data=data, files=files, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Telegram API error (sendPhoto {response.status_code}): {response.text}")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Telegram photo: {e}", exc_info=True)
            return False

    async def close(self):
        """
        Cleanup method for TelegramAlerter.
        Currently no async resources to clean up, but method exists for consistency.
        """
        self.logger.debug("TelegramAlerter cleanup completed")
        
    def __del__(self):
        """Cleanup in destructor as safety net"""
        pass 