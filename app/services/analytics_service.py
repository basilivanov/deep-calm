"""
Сервис аналитики для расчета метрик кампаний
"""
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional, Dict, List
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.conversion import Conversion
from app.models.lead import Lead
from app.models.placement import Placement
from app.schemas.analytics import (
    CampaignMetrics,
    ChannelBreakdown,
    DashboardSummary,
    DashboardDailyPoint,
    ChannelPerformanceItem,
    ChannelSparklinePoint,
)

logger = structlog.get_logger()


class AnalyticsService:
    """Сервис для расчета метрик и аналитики"""

    def __init__(self, db: Session):
        self.db = db

    def get_campaign_metrics(
        self,
        campaign_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """
        Рассчитывает метрики для кампании

        Args:
            campaign_id: ID кампании
            start_date: Начальная дата фильтра
            end_date: Конечная дата фильтра

        Returns:
            dict с метриками и разбивкой по каналам
        """
        logger.info(
            "calculating_campaign_metrics",
            campaign_id=str(campaign_id),
            start_date=str(start_date) if start_date else None,
            end_date=str(end_date) if end_date else None
        )

        # Получаем кампанию
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Кампания {campaign_id} не найдена")

        # Базовые метрики кампании
        metrics = CampaignMetrics(
            campaign_id=campaign.id,
            campaign_title=campaign.title,
            sku=campaign.sku,
            budget_rub=campaign.budget_rub,
            target_cac_rub=campaign.target_cac_rub,
            target_roas=campaign.target_roas
        )

        # Получаем конверсии кампании
        conversions_query = self.db.query(Conversion).filter(Conversion.campaign_id == campaign_id)

        if start_date:
            conversions_query = conversions_query.filter(func.date(Conversion.created_at) >= start_date)

        if end_date:
            conversions_query = conversions_query.filter(func.date(Conversion.created_at) <= end_date)

        conversions = conversions_query.all()

        # Получаем лиды через конверсии
        leads = [c.lead for c in conversions if c.lead]

        metrics.leads_count = len(leads)
        metrics.conversions_count = len(conversions)

        # Расчет выручки
        metrics.revenue_rub = float(sum(c.revenue_rub for c in conversions))

        # Conversion Rate
        if metrics.leads_count > 0:
            metrics.conversion_rate = round(
                (metrics.conversions_count / metrics.leads_count) * 100,
                2
            )

        # Для MVP используем mock данные для показов/кликов
        # В реальности эти данные будут приходить из Яндекс.Метрики
        metrics.impressions = metrics.leads_count * 100  # mock: 1 лид = 100 показов
        metrics.clicks = metrics.leads_count  # mock: 1 клик = 1 лид

        if metrics.impressions > 0:
            metrics.ctr = round((metrics.clicks / metrics.impressions) * 100, 2)

        # Spent - mock (в реальности из API платформ)
        # Для MVP считаем что потратили пропорционально лидам
        if metrics.leads_count > 0:
            metrics.spent_rub = round(metrics.budget_rub * 0.5, 2)  # mock: 50% бюджета
        else:
            metrics.spent_rub = 0.0

        # CAC
        if metrics.conversions_count > 0:
            metrics.actual_cac_rub = round(metrics.spent_rub / metrics.conversions_count, 2)
        else:
            metrics.actual_cac_rub = None

        # ROAS
        if metrics.spent_rub > 0:
            metrics.actual_roas = round(metrics.revenue_rub / metrics.spent_rub, 2)
        else:
            metrics.actual_roas = None

        # Статус CAC
        if metrics.actual_cac_rub and campaign.target_cac_rub:
            target_cac = float(campaign.target_cac_rub)
            if metrics.actual_cac_rub <= target_cac:
                metrics.cac_status = "on_track"
            elif metrics.actual_cac_rub <= target_cac * 1.2:
                metrics.cac_status = "over_target"
            else:
                metrics.cac_status = "under_target"
        else:
            metrics.cac_status = "unknown"

        # Статус ROAS
        if metrics.actual_roas and campaign.target_roas:
            target_roas = float(campaign.target_roas)
            if metrics.actual_roas >= target_roas:
                metrics.roas_status = "on_track"
            elif metrics.actual_roas >= target_roas * 0.8:
                metrics.roas_status = "under_target"
            else:
                metrics.roas_status = "over_target"
        else:
            metrics.roas_status = "unknown"

        # Разбивка по каналам
        channels = self._get_channel_breakdown(campaign_id, start_date, end_date)

        logger.info(
            "campaign_metrics_calculated",
            campaign_id=str(campaign_id),
            leads=metrics.leads_count,
            conversions=metrics.conversions_count,
            revenue=metrics.revenue_rub
        )

        return {
            "metrics": metrics,
            "channels": channels
        }

    def _get_channel_breakdown(
        self,
        campaign_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[ChannelBreakdown]:
        """
        Рассчитывает метрики по каналам

        Args:
            campaign_id: ID кампании
            start_date: Начальная дата
            end_date: Конечная дата

        Returns:
            Список метрик по каналам
        """
        # Получаем placements кампании
        placements_query = (
            self.db.query(Placement)
            .filter(Placement.campaign_id == campaign_id)
        )

        if start_date:
            placements_query = placements_query.filter(
                func.date(Placement.published_at) >= start_date
            )

        if end_date:
            placements_query = placements_query.filter(
                func.date(Placement.published_at) <= end_date
            )

        placements = placements_query.all()

        # Группируем по каналам
        channels_data = {}
        for placement in placements:
            channel_code = placement.channel_code
            if channel_code not in channels_data:
                channels_data[channel_code] = {
                    "channel_code": channel_code,
                    "channel_name": self._get_channel_name(channel_code),
                    "placements_count": 0,
                    "active_placements": 0,
                    "spent_rub": 0.0,
                    "leads_count": 0,
                    "conversions_count": 0,
                    "revenue_rub": 0.0
                }

            channels_data[channel_code]["placements_count"] += 1
            if placement.status == "active":
                channels_data[channel_code]["active_placements"] += 1

        # Получаем конверсии по каналам
        conversions_query = self.db.query(Conversion).filter(Conversion.campaign_id == campaign_id)
        if start_date:
            conversions_query = conversions_query.filter(func.date(Conversion.created_at) >= start_date)
        if end_date:
            conversions_query = conversions_query.filter(func.date(Conversion.created_at) <= end_date)

        conversions = conversions_query.all()

        # Собираем статистику по конверсиям и лидам
        for conversion in conversions:
            # Находим канал через лид
            if conversion.lead:
                channel = self._extract_channel_from_utm(conversion.lead.utm_source)
                if channel and channel in channels_data:
                    channels_data[channel]["conversions_count"] += 1
                    channels_data[channel]["revenue_rub"] += float(conversion.revenue_rub)
                    channels_data[channel]["leads_count"] += 1  # каждый conversion имеет lead

        # Mock spent (в реальности из API)
        for channel_code, data in channels_data.items():
            if data["leads_count"] > 0:
                data["spent_rub"] = round(data["leads_count"] * 500.0, 2)  # mock: 500 руб на лид

        # Формируем ChannelBreakdown
        result = []
        for channel_code, data in channels_data.items():
            cac_rub = None
            roas = None

            if data["conversions_count"] > 0:
                cac_rub = round(data["spent_rub"] / data["conversions_count"], 2)

            if data["spent_rub"] > 0:
                roas = round(data["revenue_rub"] / data["spent_rub"], 2)

            result.append(
                ChannelBreakdown(
                    channel_code=channel_code,
                    channel_name=data["channel_name"],
                    placements_count=data["placements_count"],
                    active_placements=data["active_placements"],
                    spent_rub=data["spent_rub"],
                    leads_count=data["leads_count"],
                    conversions_count=data["conversions_count"],
                    revenue_rub=data["revenue_rub"],
                    cac_rub=cac_rub,
                    roas=roas
                )
            )

        return result

    def get_dashboard_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> DashboardSummary:
        """
        Получает сводку для дашборда

        Args:
            start_date: Начальная дата
            end_date: Конечная дата

        Returns:
            DashboardSummary
        """
        logger.info("calculating_dashboard_summary")

        campaigns = self.db.query(Campaign).all()

        total_campaigns = len(campaigns)
        active_campaigns = sum(1 for c in campaigns if c.status == "active")
        paused_campaigns = sum(1 for c in campaigns if c.status == "paused")

        total_budget_rub = float(sum(c.budget_rub for c in campaigns))

        # Расчет метрик по всем кампаниям
        total_spent_rub = 0.0
        total_leads = 0
        total_conversions = 0
        total_revenue_rub = 0.0

        campaign_roas_list = []

        for campaign in campaigns:
            try:
                metrics_data = self.get_campaign_metrics(campaign.id, start_date, end_date)
                metrics = metrics_data["metrics"]

                total_spent_rub += metrics.spent_rub
                total_leads += metrics.leads_count
                total_conversions += metrics.conversions_count
                total_revenue_rub += metrics.revenue_rub

                if metrics.actual_roas:
                    campaign_roas_list.append({
                        "campaign_id": str(campaign.id),
                        "campaign_title": campaign.title,
                        "roas": metrics.actual_roas
                    })
            except Exception as e:
                logger.error(
                    "dashboard_campaign_metrics_failed",
                    campaign_id=str(campaign.id),
                    error=str(e)
                )

        # Budget utilization
        budget_utilization = 0.0
        if total_budget_rub > 0:
            budget_utilization = round((total_spent_rub / total_budget_rub) * 100, 2)

        # Средние метрики
        avg_cac_rub = None
        if total_conversions > 0:
            avg_cac_rub = round(total_spent_rub / total_conversions, 2)

        avg_roas = None
        if total_spent_rub > 0:
            avg_roas = round(total_revenue_rub / total_spent_rub, 2)

        # Лучшая кампания
        top_performing_campaign = None
        if campaign_roas_list:
            top_performing_campaign = max(campaign_roas_list, key=lambda x: x["roas"])

        summary = DashboardSummary(
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            paused_campaigns=paused_campaigns,
            total_budget_rub=total_budget_rub,
            total_spent_rub=total_spent_rub,
            budget_utilization=budget_utilization,
            total_leads=total_leads,
            total_conversions=total_conversions,
            total_revenue_rub=total_revenue_rub,
            avg_cac_rub=avg_cac_rub,
            avg_roas=avg_roas,
            top_performing_campaign=top_performing_campaign
        )

        logger.info(
            "dashboard_summary_calculated",
            total_campaigns=total_campaigns,
            total_leads=total_leads,
            total_conversions=total_conversions
        )

        return summary

    def _get_channel_name(self, channel_code: str) -> str:
        """Получает название канала по коду"""
        channel_names = {
            "vk": "VK Ads",
            "direct": "Яндекс.Директ",
            "avito": "Avito"
        }
        return channel_names.get(channel_code, channel_code)

    def _extract_channel_from_utm(self, utm_source: Optional[str]) -> Optional[str]:
        """Извлекает канал из utm_source"""
        if not utm_source:
            return None

        utm_lower = utm_source.lower()
        if "vk" in utm_lower:
            return "vk"
        elif "direct" in utm_lower or "yandex" in utm_lower:
            return "direct"
        elif "avito" in utm_lower:
            return "avito"

        return None

    def get_dashboard_daily_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[DashboardDailyPoint]:
        """Возвращает ежедневные агрегированные метрики для дашборда."""

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=29)

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        campaigns = self.db.query(Campaign).all()
        campaign_targets: Dict[UUID, float] = {
            campaign.id: float(campaign.target_cac_rub or 0.0)
            for campaign in campaigns
        }

        daily_stats = defaultdict(lambda: {
            "conversions": 0,
            "revenue": 0.0,
            "spent": 0.0,
            "leads": 0,
        })

        conversion_rows = (
            self.db.query(
                func.date(Conversion.converted_at).label("day"),
                Conversion.campaign_id,
                func.count(Conversion.id).label("conversions"),
                func.sum(Conversion.revenue_rub).label("revenue"),
            )
            .filter(func.date(Conversion.converted_at) >= start_date)
            .filter(func.date(Conversion.converted_at) <= end_date)
            .group_by("day", Conversion.campaign_id)
            .all()
        )

        for row in conversion_rows:
            day = row.day
            conversions = int(row.conversions or 0)
            revenue = float(row.revenue or 0)
            target_cac = campaign_targets.get(row.campaign_id, 0.0)
            spent = conversions * target_cac

            stats = daily_stats[day]
            stats["conversions"] += conversions
            stats["revenue"] += revenue
            stats["spent"] += spent

        lead_rows = (
            self.db.query(
                func.date(Lead.created_at).label("day"),
                func.count(Lead.id).label("leads"),
            )
            .filter(Lead.created_at.isnot(None))
            .filter(func.date(Lead.created_at) >= start_date)
            .filter(func.date(Lead.created_at) <= end_date)
            .group_by("day")
            .all()
        )

        for row in lead_rows:
            day = row.day
            stats = daily_stats[day]
            stats["leads"] += int(row.leads or 0)

        results: List[DashboardDailyPoint] = []
        current_day = start_date
        while current_day <= end_date:
            stats = daily_stats[current_day]
            conversions = stats["conversions"]
            spent = stats["spent"]
            revenue = stats["revenue"]

            cac = round(spent / conversions, 2) if conversions > 0 and spent > 0 else None
            roas = round(revenue / spent, 2) if spent > 0 else None

            results.append(
                DashboardDailyPoint(
                    date=current_day,
                    conversions=conversions,
                    leads=stats["leads"],
                    revenue=round(revenue, 2),
                    spend=round(spent, 2),
                    cac=cac,
                    roas=roas,
                )
            )
            current_day += timedelta(days=1)

        return results

    def get_channel_performance(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[ChannelPerformanceItem]:
        """Возвращает агрегированные метрики по каналам."""

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=29)

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        campaigns = self.db.query(Campaign).all()
        campaign_targets: Dict[UUID, float] = {
            campaign.id: float(campaign.target_cac_rub or 0.0)
            for campaign in campaigns
        }

        channel_default_targets: Dict[str, List[float]] = defaultdict(list)
        for campaign in campaigns:
            for channel_code in campaign.channels or []:
                channel_default_targets[channel_code].append(float(campaign.target_cac_rub or 0.0))

        totals = defaultdict(lambda: {
            "leads": 0,
            "conversions": 0,
            "revenue": 0.0,
            "spent": 0.0,
            "sparkline": defaultdict(lambda: {"conversions": 0, "spent": 0.0}),
        })

        conversion_rows = (
            self.db.query(
                func.coalesce(Conversion.channel_code, Lead.utm_source).label("channel_raw"),
                Conversion.campaign_id,
                func.date(Conversion.converted_at).label("day"),
                func.count(Conversion.id).label("conversions"),
                func.sum(Conversion.revenue_rub).label("revenue"),
            )
            .outerjoin(Lead, Conversion.lead_id == Lead.id)
            .filter(func.date(Conversion.converted_at) >= start_date)
            .filter(func.date(Conversion.converted_at) <= end_date)
            .group_by("channel_raw", Conversion.campaign_id, "day")
            .all()
        )

        for row in conversion_rows:
            raw_code = row.channel_raw
            channel_code = None
            if raw_code:
                lower = raw_code.lower()
                if lower in {"vk", "direct", "avito"}:
                    channel_code = lower
                else:
                    channel_code = self._extract_channel_from_utm(raw_code)

            if not channel_code:
                continue

            conversions = int(row.conversions or 0)
            revenue = float(row.revenue or 0)
            target_cac = campaign_targets.get(row.campaign_id, 0.0)
            spent = conversions * target_cac

            channel_totals = totals[channel_code]
            channel_totals["conversions"] += conversions
            channel_totals["revenue"] += revenue
            channel_totals["spent"] += spent
            channel_totals["sparkline"][row.day]["conversions"] += conversions
            channel_totals["sparkline"][row.day]["spent"] += spent

        lead_rows = (
            self.db.query(
                func.coalesce(Lead.utm_source, '').label("source"),
                func.count(Lead.id).label("leads"),
            )
            .filter(Lead.created_at.isnot(None))
            .filter(func.date(Lead.created_at) >= start_date)
            .filter(func.date(Lead.created_at) <= end_date)
            .group_by("source")
            .all()
        )

        for row in lead_rows:
            channel_code = self._extract_channel_from_utm(row.source) if row.source else None
            if channel_code:
                totals[channel_code]["leads"] += int(row.leads or 0)

        results: List[ChannelPerformanceItem] = []
        for channel_code, stats in totals.items():
            conversions = stats["conversions"]
            spent = stats["spent"]
            revenue = stats["revenue"]
            cac = round(spent / conversions, 2) if conversions > 0 and spent > 0 else None
            roas = round(revenue / spent, 2) if spent > 0 else None

            target_values = channel_default_targets.get(channel_code, [])
            avg_target = None
            if target_values:
                avg_target = round(sum(target_values) / len(target_values), 2)

            sparkline_points: List[ChannelSparklinePoint] = []
            sparkline_source = stats["sparkline"]
            for day in sorted(sparkline_source.keys())[-7:]:
                day_stats = sparkline_source[day]
                day_conversions = day_stats["conversions"]
                day_spent = day_stats["spent"]
                value = round(day_spent / day_conversions, 2) if day_conversions > 0 and day_spent > 0 else 0.0
                sparkline_points.append(ChannelSparklinePoint(date=day, value=value))

            results.append(
                ChannelPerformanceItem(
                    channel=channel_code,
                    channelName=self._get_channel_name(channel_code),
                    spend=round(spent, 2),
                    leads=stats["leads"],
                    conversions=conversions,
                    revenue=round(revenue, 2),
                    cac=cac,
                    roas=roas,
                    targetCac=avg_target,
                    sparklineData=sparkline_points,
                )
            )

        return sorted(results, key=lambda item: item.revenue, reverse=True)
