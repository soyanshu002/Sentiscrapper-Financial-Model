import io
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from typing import Dict, Any

class ExcelReportGenerator:
    @staticmethod
    def generate_workbook(data: Dict[str, Any]) -> io.BytesIO:
        """
        Generates a professional, multi-tab Excel financial modeling workbook (.xlsx)
        containing executive KPIs, 5-day ML forecasts, technical indicators, and sentiment feed.
        """
        wb = openpyxl.Workbook()
        
        # Color Palette - Corporate Navy & Slate
        NAVY_FILL = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        TITLE_FONT = Font(name="Calibri", size=16, bold=True, color="0F172A")
        SUBTITLE_FONT = Font(name="Calibri", size=10, italic=True, color="64748B")
        SECTION_FONT = Font(name="Calibri", size=13, bold=True, color="1E3A8A")
        BOLD_FONT = Font(name="Calibri", size=10, bold=True, color="0F172A")
        REGULAR_FONT = Font(name="Calibri", size=10, color="334155")
        
        KPI_HEADER_FILL = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        BULLISH_FILL = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        BEARISH_FILL = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        NEUTRAL_FILL = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid")

        THIN_BORDER = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        ticker = data.get("ticker", "UNKNOWN")
        model_type = data.get("model_type", "Random Forest")
        avg_sentiment = data.get("average_sentiment", 0.0)
        rec_text = data.get("recommendation", "")
        metrics = data.get("metrics", {})

        # Extract recommendation parsing
        rec_signal = "HOLD"
        for signal in ["BUY", "ACCUMULATE / WEAK BUY", "SELL", "REDUCE / WEAK SELL", "HOLD / NEUTRAL"]:
            if f"`{signal}`" in rec_text or f"advice: {signal}" in rec_text.lower():
                rec_signal = signal
                break

        # -------------------------------------------------------------
        # TAB 1: EXECUTIVE KPI DASHBOARD
        # -------------------------------------------------------------
        ws1 = wb.active
        ws1.title = "Executive Dashboard"
        ws1.views.sheetView[0].showGridLines = True

        # Title Block
        ws1["A1"] = f"SentiScrapper Financial Model & Executive Valuation Dashboard"
        ws1["A1"].font = TITLE_FONT
        ws1["A2"] = f"Automated Multi-Agent Financial Analysis for Ticker: {ticker} | Generated via SentiScrapper AI Engine"
        ws1["A2"].font = SUBTITLE_FONT

        # Key Financial KPIs Table
        ws1["A4"] = "KEY PERFORMANCE INDICATORS (KPIs)"
        ws1["A4"].font = SECTION_FONT

        kpi_headers = ["Metric Parameter", "Value / Output", "Benchmark / Context"]
        for col_num, h_text in enumerate(kpi_headers, 1):
            cell = ws1.cell(row=5, column=col_num, value=h_text)
            cell.fill = NAVY_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")

        kpi_rows = [
            ("Target Stock Ticker", ticker, "NSE / BSE / US Equity"),
            ("Machine Learning Engine", model_type, "Quant Analyst Pipeline"),
            ("Final Advisory Signal", rec_signal, "Portfolio Manager Synthesis"),
            ("Average Social Sentiment Polarity", f"{avg_sentiment:+.4f}", "-1.0 (Bearish) to +1.0 (Bullish)"),
            ("Model Directional Accuracy", f"{metrics.get('directional_accuracy', 0.0)*100:.2f}%", "Backtest Test Window"),
            ("Model Mean Squared Error (MSE)", f"{metrics.get('mse', 0.0):.4f}", "Rupee/Dollar Squared Metric"),
            ("Model R² Coefficient", f"{metrics.get('r2', 0.0):.4f}", "Variance Explained (0.0 to 1.0)")
        ]

        for row_idx, (param, val, bench) in enumerate(kpi_rows, 6):
            c1 = ws1.cell(row=row_idx, column=1, value=param)
            c2 = ws1.cell(row=row_idx, column=2, value=val)
            c3 = ws1.cell(row=row_idx, column=3, value=bench)

            c1.font, c2.font, c3.font = REGULAR_FONT, BOLD_FONT, REGULAR_FONT
            c1.border, c2.border, c3.border = THIN_BORDER, THIN_BORDER, THIN_BORDER

            if param == "Final Advisory Signal":
                if "BUY" in val:
                    c2.fill = BULLISH_FILL
                elif "SELL" in val:
                    c2.fill = BEARISH_FILL
                else:
                    c2.fill = NEUTRAL_FILL

        # Add Full Recommendation Report Section
        ws1["A15"] = "PORTFOLIO MANAGER ADVISORY REPORT & SCORING BREAKDOWN"
        ws1["A15"].font = SECTION_FONT

        rec_lines = [line for line in rec_text.split('\n') if line.strip()]
        start_r = 16
        for line in rec_lines:
            ws1.cell(row=start_r, column=1, value=line).font = REGULAR_FONT
            start_r += 1

        # -------------------------------------------------------------
        # TAB 2: 5-DAY ML PRICE FORECASTS & METRICS
        # -------------------------------------------------------------
        ws2 = wb.create_sheet(title="ML Forecasts & Metrics")
        ws2.views.sheetView[0].showGridLines = True

        ws2["A1"] = f"{ticker} - 5-Day Machine Learning Price Projections"
        ws2["A1"].font = TITLE_FONT

        ws2["A3"] = "MODEL VALIDATION METRICS"
        ws2["A3"].font = SECTION_FONT

        met_headers = ["Metric", "Score", "Description"]
        for col_num, h_text in enumerate(met_headers, 1):
            cell = ws2.cell(row=4, column=col_num, value=h_text)
            cell.fill = NAVY_FILL
            cell.font = HEADER_FONT

        met_data = [
            ("Mean Squared Error (MSE)", metrics.get("mse", 0.0), "Average squared forecast variance"),
            ("Mean Absolute Error (MAE)", metrics.get("mae", 0.0), "Average absolute error magnitude"),
            ("R-Squared (R²)", metrics.get("r2", 0.0), "Percentage of return variance explained"),
            ("Directional Accuracy", f"{metrics.get('directional_accuracy', 0.0)*100:.2f}%", "Correct return sign predictions")
        ]

        for r_i, (m_name, m_val, m_desc) in enumerate(met_data, 5):
            ws2.cell(row=r_i, column=1, value=m_name).font = BOLD_FONT
            ws2.cell(row=r_i, column=2, value=m_val).font = BOLD_FONT
            ws2.cell(row=r_i, column=3, value=m_desc).font = REGULAR_FONT
            for col in range(1, 4):
                ws2.cell(row=r_i, column=col).border = THIN_BORDER

        # Forecast Table
        ws2["A11"] = "5-DAY PROJECTED CLOSE PRICES"
        ws2["A11"].font = SECTION_FONT

        fc_headers = ["Forecast Date", "Predicted Close Price", "Daily Return %", "Cumulative Growth %"]
        for col_num, h_text in enumerate(fc_headers, 1):
            cell = ws2.cell(row=12, column=col_num, value=h_text)
            cell.fill = NAVY_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center")

        forecast_list = data.get("forecast_data", [])
        hist_list = data.get("historical_data", [])
        last_close = hist_list[-1]["Close"] if hist_list and "Close" in hist_list[-1] else 100.0

        prev_p = last_close
        for idx, fc_item in enumerate(forecast_list, 13):
            d_val = fc_item.get("Date", "")
            p_val = fc_item.get("Predicted_Close", 0.0)
            daily_ret = ((p_val - prev_p) / prev_p) * 100 if prev_p else 0.0
            cum_ret = ((p_val - last_close) / last_close) * 100 if last_close else 0.0

            ws2.cell(row=idx, column=1, value=d_val).font = REGULAR_FONT
            ws2.cell(row=idx, column=2, value=round(p_val, 2)).font = BOLD_FONT
            ws2.cell(row=idx, column=3, value=f"{daily_ret:+.2f}%").font = REGULAR_FONT
            ws2.cell(row=idx, column=4, value=f"{cum_ret:+.2f}%").font = BOLD_FONT

            for col in range(1, 5):
                c = ws2.cell(row=idx, column=col)
                c.border = THIN_BORDER
                c.alignment = Alignment(horizontal="center")
            prev_p = p_val

        # -------------------------------------------------------------
        # TAB 3: TECHNICAL INDICATORS & PRICE HISTORY
        # -------------------------------------------------------------
        ws3 = wb.create_sheet(title="Technicals & Historical Data")
        ws3.views.sheetView[0].showGridLines = True

        ws3["A1"] = f"{ticker} - Historical Prices & Technical Indicators"
        ws3["A1"].font = TITLE_FONT

        tech_headers = ["Date", "Open", "High", "Low", "Close", "RSI (14)", "MACD", "Weighted Sentiment"]
        for col_num, h_text in enumerate(tech_headers, 1):
            cell = ws3.cell(row=3, column=col_num, value=h_text)
            cell.fill = NAVY_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center")

        for idx, row_item in enumerate(hist_list, 4):
            ws3.cell(row=idx, column=1, value=row_item.get("Date", "")).font = REGULAR_FONT
            ws3.cell(row=idx, column=2, value=round(row_item.get("Open", 0.0), 2)).font = REGULAR_FONT
            ws3.cell(row=idx, column=3, value=round(row_item.get("High", 0.0), 2)).font = REGULAR_FONT
            ws3.cell(row=idx, column=4, value=round(row_item.get("Low", 0.0), 2)).font = REGULAR_FONT
            ws3.cell(row=idx, column=5, value=round(row_item.get("Close", 0.0), 2)).font = BOLD_FONT
            ws3.cell(row=idx, column=6, value=round(row_item.get("RSI", 0.0), 2)).font = REGULAR_FONT
            ws3.cell(row=idx, column=7, value=round(row_item.get("MACD", 0.0), 2)).font = REGULAR_FONT
            ws3.cell(row=idx, column=8, value=round(row_item.get("Weighted_Sentiment", 0.0), 4)).font = REGULAR_FONT

            for col in range(1, 9):
                c = ws3.cell(row=idx, column=col)
                c.border = THIN_BORDER
                c.alignment = Alignment(horizontal="center")

        # -------------------------------------------------------------
        # TAB 4: SOCIAL & NEWS SENTIMENT CORPUS
        # -------------------------------------------------------------
        ws4 = wb.create_sheet(title="Social Sentiment Corpus")
        ws4.views.sheetView[0].showGridLines = True

        ws4["A1"] = f"{ticker} - Harvested Social & News Feed Sentiment"
        ws4["A1"].font = TITLE_FONT

        sent_headers = ["Platform Source", "Post / Headline Text", "Polarity Compound Score", "Sentiment Classification"]
        for col_num, h_text in enumerate(sent_headers, 1):
            cell = ws4.cell(row=3, column=col_num, value=h_text)
            cell.fill = NAVY_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center")

        sentiment_details = data.get("sentiment_details", [])
        for idx, s_item in enumerate(sentiment_details, 4):
            src = s_item.get("source", "News")
            txt = s_item.get("text", "")
            sc = s_item.get("compound", 0.0)

            if sc >= 0.05:
                rating = "Bullish"
                rating_fill = BULLISH_FILL
            elif sc <= -0.05:
                rating = "Bearish"
                rating_fill = BEARISH_FILL
            else:
                rating = "Neutral"
                rating_fill = NEUTRAL_FILL

            ws4.cell(row=idx, column=1, value=src).font = BOLD_FONT
            ws4.cell(row=idx, column=2, value=txt).font = REGULAR_FONT
            ws4.cell(row=idx, column=3, value=round(sc, 4)).font = BOLD_FONT
            
            c4 = ws4.cell(row=idx, column=4, value=rating)
            c4.font = BOLD_FONT
            c4.fill = rating_fill

            for col in range(1, 5):
                c = ws4.cell(row=idx, column=col)
                c.border = THIN_BORDER
                if col in [1, 3, 4]:
                    c.alignment = Alignment(horizontal="center")

        # Auto-adjust column widths across all sheets
        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                sheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 80)

        # Save to memory buffer
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output
