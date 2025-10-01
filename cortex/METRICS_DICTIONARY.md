# Метрики DeepCalm (MANDATORY)
- **CAC** = spend / leads_paid
- **ДРР (DRR)** = spend / revenue
- **TTP (days)** = floor(purchase_at − first_touch_at)  (purchase_at ≥ first_touch_at)
- **Conv_D7/14/30/60** — конверсия когорты Landing→Purchase
- **Payback_D** — первый день, когда LTV_D ≥ CAC
- **Оперативная запись**: lead_time_days ∈ {0,1}
Краевые случаи: TZ, отмены/переносы, 0/1-day окна — покрываются тестами.
