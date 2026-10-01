import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from bs4 import BeautifulSoup
import os

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_document():
    doc = Document()

    # Page Margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Document Header Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("Executive Summary: Business Outcomes & Optimization Framework")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42) # #0f172a

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Comprehensive Breakdown of Business Outcomes, Target Features, SXI Metrics, and Multi-Horizon Goals across Demand Planning, Procurement, and Sales Forecasting")
    run_sub.font.name = 'Calibri'
    run_sub.font.size = Pt(11)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Overview Table Summary
    p_lead = doc.add_paragraph()
    r_lead = p_lead.add_run("1. Master Optimization Matrix")
    r_lead.font.name = 'Calibri'
    r_lead.font.size = Pt(14)
    r_lead.font.bold = True
    r_lead.font.color.rgb = RGBColor(30, 58, 138)

    # Master Table
    table = doc.add_table(rows=1, cols=6)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    headers = ["Sl. No.", "Module", "Business Outcome", "Target Feature", "Current Baseline", "Long-Term Goal"]
    col_widths = [Inches(0.6), Inches(1.2), Inches(1.8), Inches(1.5), Inches(1.0), Inches(1.0)]

    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "1E3A8A")
        set_cell_margins(hdr_cells[i], top=140, bottom=140, left=120, right=120)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(9.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

    matrix_data = [
        ("1", "Demand Planning", "Reduce Stockout Risk", "global_plan_demand_quantity (units)", "29.3% (12,915 u)", "5.8% (2,557 u)"),
        ("2", "Demand Planning", "Reduce Delivery Lead Time", "lead_time (days)", "9.0 Days", "4.0 Days"),
        ("3", "Demand Planning", "Reduce Margin Leakage", "margin_leakage ($)", "21.5% (8,600 orders)", "4.3% (1,720 orders)"),
        ("4", "Demand Planning", "Reduce Inbound Defect Risk", "is_high_defect_risk", "20.0% (3,200 orders)", "4.0% (640 orders)"),
        ("5", "Procurement", "Reduce Purchase Cost Variance", "purchase_cost ($)", "5.8% ($248,500)", "1.2% ($51,400)"),
        ("6", "Procurement", "Reduce Inventory Stockout Risk", "is_reorder_required", "24.2% (1,210 items)", "4.8% (242 items)"),
        ("7", "Procurement", "Reduce Single-Source Supply Risk", "is_preferred_supplier", "22.3% (111 SKUs)", "4.5% (22 SKUs)"),
        ("8", "Procurement", "Reduce Non-Compliant PO Risk Rate", "is_po_compliant", "17.8% (712 POs)", "3.6% (144 POs)"),
        ("9", "Sales Forecasting", "Increase Sales Volume Realization", "units_sold (units)", "68.8% Accuracy (1,069k u)", "96.1% Accuracy (1,494k u)"),
        ("10", "Sales Forecasting", "Reduce Forecast Variance", "sales_forecast_error (%)", "31.2% Variance (±485k $)", "5.8% Variance (±90k $)")
    ]

    for row_idx, data in enumerate(matrix_data):
        row = table.add_row()
        bg_color = "F8FAFC" if row_idx % 2 == 0 else "FFFFFF"
        for i, val in enumerate(data):
            cell = row.cells[i]
            cell.text = val
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
            p = cell.paragraphs[0]
            if i in [0, 4, 5]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Calibri'
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(15, 23, 42)
                if i == 0:
                    r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(16)

    # Detailed Sections
    p_det = doc.add_paragraph()
    r_det = p_det.add_run("2. Detailed Business Outcome & Goal Specifications")
    r_det.font.name = 'Calibri'
    r_det.font.size = Pt(14)
    r_det.font.bold = True
    r_det.font.color.rgb = RGBColor(30, 58, 138)

    detailed_items = [
        {
            "sl": "1",
            "module": "Demand Planning",
            "title": "Reduce Stockout Risk",
            "purpose": "Eliminate stockouts and buffer shortages across 4 Distribution Centers and 102 SKUs by dynamically balancing stock allocation and customer order fulfillment.",
            "target_feature": "global_plan_demand_quantity (units)",
            "current_sxi": "6.12",
            "current_num": "29.3% Stockout Rate (12,915 units out of 44,096 demand)",
            "short_goal": {
                "sxi": "6.72",
                "val": "23.4% Stockout Rate (10,332 units)",
                "delta": "↓ 20.0% reduction (-2,583 units)",
                "horizon": "Short-Term (30 Days)"
            },
            "mid_goal": {
                "sxi": "7.62",
                "val": "14.6% Stockout Rate (6,449 units)",
                "delta": "↓ 50.2% reduction (-6,483 units)",
                "horizon": "Mid-Term (90 Days)"
            },
            "long_goal": {
                "sxi": "8.52",
                "val": "5.8% Stockout Rate (2,557 units)",
                "delta": "↓ 80.2% reduction (-10,358 units)",
                "horizon": "Long-Term (180 Days)"
            }
        },
        {
            "sl": "2",
            "module": "Demand Planning",
            "title": "Reduce Delivery Lead Time",
            "purpose": "Compress supplier-to-warehouse transit and receiving cycle times by routing shipments through high-performing logistics carriers and verified suppliers.",
            "target_feature": "lead_time (days)",
            "current_sxi": "5.95",
            "current_num": "9.0 Days Average Lead Time",
            "short_goal": {
                "sxi": "6.65",
                "val": "7.0 Days Average Lead Time",
                "delta": "↓ 22.2% reduction (-2.0 Days)",
                "horizon": "Short-Term (30 Days)"
            },
            "mid_goal": {
                "sxi": "7.55",
                "val": "5.5 Days Average Lead Time",
                "delta": "↓ 38.9% reduction (-3.5 Days)",
                "horizon": "Mid-Term (90 Days)"
            },
            "long_goal": {
                "sxi": "8.45",
                "val": "4.0 Days Average Lead Time",
                "delta": "↓ 55.6% reduction (-5.0 Days)",
                "horizon": "Long-Term (180 Days)"
            }
        },
        {
            "sl": "3",
            "module": "Demand Planning",
            "title": "Reduce Margin Leakage",
            "purpose": "Prevent margin erosion from excessive wholesale promotional discounting, off-invoice allowances, and unbudgeted spot freight overrides.",
            "target_feature": "margin_leakage ($)",
            "current_sxi": "6.08",
            "current_num": "21.5% Margin Leakage Rate (8,600 orders / $175,800)",
            "short_goal": {
                "sxi": "6.68",
                "val": "17.2% Margin Leakage Rate (6,880 orders)",
                "delta": "↓ 20.0% reduction (-1,720 orders / -$35,160)",
                "horizon": "Short-Term (30 Days)"
            },
            "mid_goal": {
                "sxi": "7.58",
                "val": "10.8% Margin Leakage Rate (4,320 orders)",
                "delta": "↓ 49.8% reduction (-4,280 orders / -$87,540)",
                "horizon": "Mid-Term (90 Days)"
            },
            "long_goal": {
                "sxi": "8.48",
                "val": "4.3% Margin Leakage Rate (1,720 orders)",
                "delta": "↓ 80.0% reduction (-6,880 orders / -$140,640)",
                "horizon": "Long-Term (180 Days)"
            }
        },
        {
            "sl": "4",
            "module": "Demand Planning",
            "title": "Reduce Inbound Defect Risk",
            "purpose": "Identify and isolate high-risk supplier shipments before warehouse receiving to avoid line stoppages, product quarantine, and quality chargebacks.",
            "target_feature": "is_high_defect_risk (Binary Classification)",
            "current_sxi": "6.15",
            "current_num": "20.0% High Defect Risk Rate (3,200 orders out of 16,000)",
            "short_goal": {
                "sxi": "6.75",
                "val": "16.0% High Defect Risk Rate (2,560 orders)",
                "delta": "↓ 20.0% reduction (-640 defective orders)",
                "horizon": "Short-Term (30 Days)"
            },
            "mid_goal": {
                "sxi": "7.65",
                "val": "10.0% High Defect Risk Rate (1,600 orders)",
                "delta": "↓ 50.0% reduction (-1,600 defective orders)",
                "horizon": "Mid-Term (90 Days)"
            },
            "long_goal": {
                "sxi": "8.55",
                "val": "4.0% High Defect Risk Rate (640 orders)",
                "delta": "↓ 80.0% reduction (-2,560 defective orders)",
                "horizon": "Long-Term (180 Days)"
            }
        },
        {
            "sl": "5",
            "module": "Procurement",
            "title": "Reduce Purchase Cost Variance",
            "purpose": "Eliminate purchase price variance (PPV) between contracted purchase order prices and invoiced receipts by enforcing automated catalog tier pricing.",
            "target_feature": "purchase_cost ($)",
            "current_sxi": "6.10",
            "current_num": "5.8% Cost Variance Rate ($248,500 variance)",
            "short_goal": {
                "sxi": "6.70",
                "val": "4.6% Cost Variance Rate ($197,100 variance)",
                "delta": "↓ 20.7% reduction (-$51,400 saved)",
                "horizon": "Short-Term (30 Days)"
            },
            "mid_goal": {
                "sxi": "7.60",
                "val": "2.9% Cost Variance Rate ($124,250 variance)",
                "delta": "↓ 50.0% reduction (-$124,250 saved)",
                "horizon": "Mid-Term (90 Days)"
            },
            "long_goal": {
                "sxi": "8.50",
                "val": "1.2% Cost Variance Rate ($51,400 variance)",
                "delta": "↓ 79.3% reduction (-$197,100 saved)",
                "horizon": "Long-Term (180 Days)"
            }
        },
        {
            "sl": "6",
            "module": "Procurement",
            "title": "Reduce Inventory Stockout Risk",
            "purpose": "Trigger intelligent automated PO reorders based on real-time inventory burn rate and dynamic lead-time buffers to eliminate raw material stockouts.",
            "target_feature": "is_reorder_required (Binary Classification)",
            "current_sxi": "6.05",
            "current_num": "24.2% Reorder Stockout Risk Rate (1,210 items)",
            "short_goal": {
                "sxi": "6.65",
                "val": "19.4% Stockout Risk Rate (970 items)",
                "delta": "↓ 19.8% reduction (-240 at-risk SKUs)",
                "horizon": "Short-Term (30 Days)"
            },
            "mid_goal": {
                "sxi": "7.55",
                "val": "12.1% Stockout Risk Rate (605 items)",
                "delta": "↓ 50.0% reduction (-605 at-risk SKUs)",
                "horizon": "Mid-Term (90 Days)"
            },
            "long_goal": {
                "sxi": "8.45",
                "val": "4.8% Stockout Risk Rate (242 items)",
                "delta": "↓ 80.2% reduction (-968 at-risk SKUs)",
                "horizon": "Long-Term (180 Days)"
            }
        },
        {
            "sl": "7",
            "module": "Procurement",
            "title": "Reduce Single-Source Supply Risk",
            "purpose": "Qualify secondary and tertiary preferred suppliers for critical SKUs to eliminate single-source dependency and production disruption risks.",
            "target_feature": "is_preferred_supplier (Binary Classification)",
            "current_sxi": "6.18",
            "current_num": "22.3% Single-Source High Risk Rate (111 SKUs)",
            "short_goal": {
                "sxi": "6.78",
                "val": "17.8% Single-Source Risk Rate (89 SKUs)",
                "delta": "↓ 20.2% reduction (-22 single-source SKUs)",
                "horizon": "Short-Term (30 Days)"
            },
            "mid_goal": {
                "sxi": "7.68",
                "val": "11.1% Single-Source Risk Rate (55 SKUs)",
                "delta": "↓ 50.2% reduction (-56 single-source SKUs)",
                "horizon": "Mid-Term (90 Days)"
            },
            "long_goal": {
                "sxi": "8.58",
                "val": "4.5% Single-Source Risk Rate (22 SKUs)",
                "delta": "↓ 79.8% reduction (-89 single-source SKUs)",
                "horizon": "Long-Term (180 Days)"
            }
        },
        {
            "sl": "8",
            "module": "Procurement",
            "title": "Reduce Non-Compliant PO Risk Rate",
            "purpose": "Enforce mandatory contract pricing rules, approved vendor lists, and delivery window validation to prevent maverick purchasing and invoice disputes.",
            "target_feature": "is_po_compliant (Binary Classification)",
            "current_sxi": "6.14",
            "current_num": "17.8% Non-Compliant PO Risk Rate (712 POs out of 4,000)",
            "short_goal": {
                "sxi": "6.74",
                "val": "14.2% Non-Compliance Rate (568 POs)",
                "delta": "↓ 20.2% reduction (-144 non-compliant POs)",
                "horizon": "Short-Term (30 Days)"
            },
            "mid_goal": {
                "sxi": "7.64",
                "val": "8.9% Non-Compliance Rate (356 POs)",
                "delta": "↓ 50.0% reduction (-356 non-compliant POs)",
                "horizon": "Mid-Term (90 Days)"
            },
            "long_goal": {
                "sxi": "8.54",
                "val": "3.6% Non-Compliance Rate (144 POs)",
                "delta": "↓ 79.8% reduction (-568 non-compliant POs)",
                "horizon": "Long-Term (180 Days)"
            }
        },
        {
            "sl": "9",
            "module": "Sales Forecasting",
            "title": "Increase Sales Volume Realization",
            "purpose": "Forecast forward-looking consumer demand across 102 SKUs and 4 regional distribution centers using Meta Prophet and Auto-SARIMA time-series models to maximize on-time order fulfillment and capture unmet sales volume.",
            "target_feature": "units_sold (units) [Time-Series Horizon Projection]",
            "current_sxi": "N/A (Time-Series Horizon: Historical Moving Average)",
            "current_num": "68.8% Baseline Accuracy (1,069,000 units realized out of 1.55M demand)",
            "short_goal": {
                "sxi": "30-Day Operational Horizon (Base Prophet)",
                "val": "88.8% Forecast Accuracy (1,381,000 units)",
                "delta": "↑ +20.1% accuracy lift (+312,000 units captured)",
                "horizon": "Short-Term (30 Days)"
            },
            "mid_goal": {
                "sxi": "90-Day Tactical Horizon (Prophet + Seasonality)",
                "val": "92.4% Forecast Accuracy (1,437,000 units)",
                "delta": "↑ +23.6% accuracy lift (+368,000 units captured)",
                "horizon": "Mid-Term (90 Days)"
            },
            "long_goal": {
                "sxi": "180-Day Strategic Horizon (AI Hybrid Ensemble)",
                "val": "96.1% Forecast Accuracy (1,494,000 units)",
                "delta": "↑ +27.3% accuracy lift (+425,000 units captured)",
                "horizon": "Long-Term (180 Days)"
            }
        },
        {
            "sl": "10",
            "module": "Sales Forecasting",
            "title": "Reduce Forecast Variance",
            "purpose": "Minimize absolute prediction error and residual variance between actual point-of-sale (POS) register sales and forecasted demand to eliminate emergency safety buffer stocks and bullwhip distortion.",
            "target_feature": "sales_forecast_error (%) [MAPE & Residual Variance]",
            "current_sxi": "N/A (Time-Series Calibration: Spreadsheets & Naive Benchmarks)",
            "current_num": "31.2% Baseline Forecast Variance / Error (±$485,000 buffer waste)",
            "short_goal": {
                "sxi": "30-Day Parameter Smoothing (Auto-SARIMA Residual Tuning)",
                "val": "17.9% Forecast Variance",
                "delta": "↓ 42.6% error reduction (-13.3% points / $210k saved)",
                "horizon": "Short-Term (30 Days)"
            },
            "mid_goal": {
                "sxi": "90-Day Regressor Calibration (Prophet Changepoints)",
                "val": "11.2% Forecast Variance",
                "delta": "↓ 64.1% error reduction (-20.0% points / $485k saved)",
                "horizon": "Mid-Term (90 Days)"
            },
            "long_goal": {
                "sxi": "180-Day Automated Calibration (AI Hybrid Ensemble)",
                "val": "5.8% Forecast Variance",
                "delta": "↓ 81.4% error reduction (-25.4% points / $640k saved)",
                "horizon": "Long-Term (180 Days)"
            }
        }
    ]

    for item in detailed_items:
        # Card Header Container
        p_item_hdr = doc.add_paragraph()
        p_item_hdr.paragraph_format.space_before = Pt(14)
        p_item_hdr.paragraph_format.space_after = Pt(4)
        
        r_num = p_item_hdr.add_run(f"{item['sl']}. {item['title']} ")
        r_num.font.name = 'Calibri'
        r_num.font.size = Pt(13)
        r_num.font.bold = True
        r_num.font.color.rgb = RGBColor(15, 23, 42)

        r_mod = p_item_hdr.add_run(f"[{item['module']}]")
        r_mod.font.name = 'Calibri'
        r_mod.font.size = Pt(11)
        r_mod.font.bold = True
        r_mod.font.color.rgb = RGBColor(37, 99, 235)

        # Meta detail table
        d_table = doc.add_table(rows=3, cols=2)
        d_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        d_table.autofit = False

        # Widths
        d_table.columns[0].width = Inches(1.8)
        d_table.columns[1].width = Inches(5.3)

        fields = [
            ("Purpose", item["purpose"]),
            ("Target Feature", item["target_feature"]),
            ("Current Baseline", f"{item['current_num']}  |  Baseline Driver / SXI: {item['current_sxi']}")
        ]

        for r_idx, (f_name, f_val) in enumerate(fields):
            c0, c1 = d_table.rows[r_idx].cells
            c0.text = f_name
            c1.text = f_val
            set_cell_background(c0, "F1F5F9")
            set_cell_background(c1, "FFFFFF")
            set_cell_margins(c0, top=60, bottom=60, left=100, right=100)
            set_cell_margins(c1, top=60, bottom=60, left=100, right=100)
            
            p0 = c0.paragraphs[0]
            for r in p0.runs:
                r.font.name = 'Calibri'
                r.font.size = Pt(9.5)
                r.font.bold = True
                r.font.color.rgb = RGBColor(30, 41, 59)

            p1 = c1.paragraphs[0]
            for r in p1.runs:
                r.font.name = 'Calibri'
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(51, 65, 85)

        # Multi-Horizon Goal Sub-table
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
        g_table = doc.add_table(rows=1, cols=4)
        g_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        g_table.autofit = False

        g_headers = ["Planning Horizon", "Target Metric / Value", "Target SXI / Driver", "Improvement Delta"]
        for g_i, g_t in enumerate(g_headers):
            g_cell = g_table.rows[0].cells[g_i]
            g_cell.text = g_t
            set_cell_background(g_cell, "E2E8F0")
            set_cell_margins(g_cell, top=80, bottom=80, left=100, right=100)
            gp = g_cell.paragraphs[0]
            gp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for gr in gp.runs:
                gr.font.name = 'Calibri'
                gr.font.size = Pt(9)
                gr.font.bold = True
                gr.font.color.rgb = RGBColor(15, 23, 42)

        goals_list = [item["short_goal"], item["mid_goal"], item["long_goal"]]
        for g_obj in goals_list:
            g_row = g_table.add_row()
            g_data = [g_obj["horizon"], g_obj["val"], str(g_obj["sxi"]), g_obj["delta"]]
            for c_i, c_val in enumerate(g_data):
                gc = g_row.cells[c_i]
                gc.text = c_val
                set_cell_background(gc, "F8FAFC")
                set_cell_margins(gc, top=60, bottom=60, left=80, right=80)
                gp = gc.paragraphs[0]
                if c_i in [0, 2]:
                    gp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    gp.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for gr in gp.runs:
                    gr.font.name = 'Calibri'
                    gr.font.size = Pt(8.5)
                    if c_i == 3:
                        gr.font.bold = True
                        gr.font.color.rgb = RGBColor(16, 185, 129) # green
                    else:
                        gr.font.color.rgb = RGBColor(30, 41, 59)

        doc.add_paragraph().paragraph_format.space_after = Pt(8)

    output_path = "Business_Outcomes_and_Optimization_Matrix.docx"
    doc.save(output_path)
    print(f"Document successfully created at {output_path}")

if __name__ == "__main__":
    create_document()
