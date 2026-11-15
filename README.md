# VoltRelay_EV_Analytics_Hackathon_2026
VoltRelay: EV Battery Swapping Network – Data Analytics Hackathon | Project Presentation
# ⚡ VoltRelay – EV Battery Swapping Network Analytics

### Data Analytics Hackathon Project | Gradient Learnings | 2026

**Analyzing EV battery-swapping operations to improve network performance, customer experience, battery health and business profitability.**

---

## 🎥 Project Presentation

Watch my 3-minute project presentation to understand the business problem, analytical approach, key findings and business recommendations.

▶️ **[Watch VoltRelay Project Presentation](PASTE_YOUR_GOOGLE_DRIVE_OR_YOUTUBE_VIDEO_LINK_HERE)**

---

## 📌 1. Project Overview

VoltRelay is a synthetic electric vehicle (EV) battery-swapping network operating across multiple cities.

The business handles thousands of battery-swapping events involving riders, stations, batteries and fleet partners.

As the network grows, the company needs to understand its operational performance, identify service problems, monitor battery health, evaluate pricing strategies and improve customer retention.

This project uses data analytics to investigate these business challenges and convert raw operational data into meaningful business insights.

**Project Objective:**

To analyze VoltRelay's operational and business data using Python and identify opportunities to improve:

- Network performance
- Station reliability
- Customer experience
- Battery utilization and health
- Pricing and partner economics
- New-rider retention

---

## 🎯 2. Business Problems

The analysis focuses on six major business questions.

| No. | Business Question | Business Objective |
|---|---|---|
| Q1 | How is the network performing? | Understand swaps, revenue and contribution trends. |
| Q2 | Where are service failures occurring? | Identify unsuccessful attempts and customer experience issues. |
| Q3 | Which stations and cities are underperforming? | Compare geographic and station-level performance. |
| Q4 | How does battery health affect performance? | Analyze battery health, range and equipment differences. |
| Q5 | How are pricing and partner contracts affecting economics? | Evaluate revenue per swap and pricing differences. |
| Q6 | Are new riders returning after their first swap? | Understand 30-day customer retention. |

---

## 🗂️ 3. Dataset Overview

The project uses synthetic operational datasets covering:

**January 2024 – June 2025**

The event dataset contains approximately **3.8 million business events**.

### Datasets Used

| Dataset | Description |
|---|---|
| `swap_events_cleaned` | Battery-swapping events, transaction details and outcomes. |
| `stations_cleaned` | Station information and station attributes. |
| `riders_cleaned` | Rider-related information. |
| `batteries_cleaned` | Battery information and health-related attributes. |
| `station_hourly_status_cleaned` | Hourly station status and operational telemetry. |
| `support_tickets_cleaned` | Customer support and service-related information. |
| `city_daily_context_cleaned` | City-level daily contextual information. |
| `fleet_partners_cleaned` | Fleet partner and contract information. |

**Note:** The dataset is synthetic and is used for analytical learning and business problem-solving. The findings should not be interpreted as actual results from a real EV company.

---

## 🛠️ 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data analysis and processing |
| Pandas | Data cleaning, transformation and analysis |
| NumPy | Numerical operations |
| Matplotlib | Data visualization |
| Jupyter Notebook / Google Colab | Analysis environment |
| CSV | Structured data storage |

The current project focuses on Python-based data analysis. SQL, Excel and Power BI are not included as completed components.

---

## 🔄 5. Data Analytics Workflow

The project follows a structured data analytics workflow.

### Step 1: Data Understanding

- Examined the available datasets.
- Understood the structure and purpose of each table.
- Identified important business variables.
- Reviewed data types and relationships.

### Step 2: Data Cleaning

- Handled missing and inconsistent values.
- Checked duplicate records.
- Standardized relevant data fields.
- Prepared datasets for analysis.
- Applied the provided timestamp correction where required.
- Excluded test stations from relevant analysis.

### Step 3: Data Transformation

- Prepared analytical columns.
- Created relevant KPIs.
- Calculated unsuccessful attempt rates.
- Calculated revenue and contribution metrics.
- Prepared battery health and rider retention segments.

### Step 4: Exploratory Data Analysis (EDA)

- Examined operational trends.
- Compared stations and cities.
- Analyzed vehicle categories.
- Evaluated battery health patterns.
- Investigated pricing and partner economics.
- Examined rider return behavior.

### Step 5: Business Analysis

Analyzed the six business questions and identified important findings.

### Step 6: Recommendations

Converted the analytical findings into practical business recommendations.

---

# 📊 6. Key Business Analysis & Findings

## Q1 – Network Performance

**Business Question:** How is the VoltRelay network performing over time?

The analysis examined completed swaps, revenue, estimated contribution per swap and unsuccessful attempt rates.

### Key Findings

- Completed swaps increased from **103,508 in January 2024** to **303,196 in June 2025**.
- Revenue increased from approximately **₹61.99 lakh** to **₹1.97 crore**.
- Contribution per swap increased from **₹17.51** to **₹36.24**.
- The unsuccessful attempt rate was **8.60% in June 2025**, compared with 9.97% in the preceding month.
- The unsuccessful attempt rate reached 12.39% in May 2024.

### Business Insight

The network experienced substantial growth in completed swaps, revenue and estimated contribution. However, unsuccessful attempts remain an operational issue that requires attention.

---

## Q2 – Service & Customer Experience

**Business Question:** Where are service failures occurring, and what factors are associated with them?

The analysis examined unsuccessful swaps, vehicle categories, seasonal patterns and station performance.

### Key Findings

- The top 10 stations by unsuccessful attempts account for **17.2% of all non-completed events**.
- Station `STN-DEL-043` recorded the highest volume of unsuccessful attempts.
- Three-wheelers had an unsuccessful attempt rate of **10.39%**.
- Two-wheelers had an unsuccessful attempt rate of **5.45%**.
- Summer unsuccessful attempt rate: **7.33%**.
- Winter unsuccessful attempt rate: **4.34%**.

### Business Insight

Three-wheelers show a higher unsuccessful attempt rate than two-wheelers. A focused investigation of high-failure stations and vehicle-specific operational requirements could help improve service reliability.

---

## Q3 – Station & Geographic Performance

**Business Question:** Which cities and station groups are performing differently?

The analysis compared city-level unsuccessful attempt rates and station generations.

### Key Findings

- Jaipur recorded the highest city-weighted unsuccessful attempt rate at **7.85%**.
- Mumbai recorded the lowest rate at **4.45%**.
- Gen1 stations had a weighted failure rate of **7.23%**.
- Gen3 stations had a weighted failure rate of **4.84%**.
- Mean charge time was 91.8 minutes for Gen1 stations and 42.2 minutes for Gen3 stations.

### Business Insight

Older station generations show higher unsuccessful attempt rates and longer mean charge times in this dataset.

Station upgrades and targeted maintenance should be evaluated, particularly in underperforming locations.

---

## Q4 – Battery Health & Equipment Performance

**Business Question:** How does battery health relate to battery performance?

The analysis examined State of Health (SOH), distance since the previous swap, observed range and supplier-level differences.

### Key Findings

- Pearson correlation between SOH and distance since the previous swap: **0.449**.
- Spearman correlation: **0.647**.
- Batteries with 95–100% SOH had a mean observed range of **72.6 km**.
- Batteries with 0–70% SOH had a mean observed range of **38.8 km**.
- Kyron had the lowest median returned-pack SOH at **82.8%**.
- Cellora had the highest median returned-pack SOH at **90.2%**.

### Business Insight

Battery health is associated with observed range. Battery health monitoring, supplier evaluation and maintenance planning can help improve fleet performance.

---

## Q5 – Pricing & Partner Economics

**Business Question:** How do pricing patterns and partner contracts relate to business economics?

The analysis examined monthly list prices, peak and off-peak revenue and fleet partner contract discounts.

### Key Findings

- Mean list price increased from **₹64.45 in January 2024** to **₹69.67 in June 2025**.
- The largest monthly list-price increase was **8.7% in July 2024**.
- Mean PEAK revenue per swap: **₹82.50**.
- Mean OFFPEAK revenue per swap: **₹59.48**.
- FP-03 contract discount increased from 12% to 28%.
- Its mean revenue per swap changed from ₹57.48 to ₹48.64.

### Business Insight

Peak and off-peak periods show different revenue per swap. Partner discount structures should be reviewed alongside revenue and contribution to understand their economics.

---

## Q6 – New-Rider Retention

**Business Question:** Are new riders returning after their first completed swap?

The analysis examined eligible new riders and whether they completed another swap within 30 days.

### Key Findings

- **15,043 eligible new riders** were included in the analysis.
- **99.5%** completed another swap within 30 days.
- Only 80 eligible riders were one-time riders.
- The highest observed segment return rate was 100.0%.
- The lowest observed segment return rate was 98.7%.

### Business Insight

The eligible rider cohort shows a high 30-day repeat rate. However, the small difference between the highest and lowest segments does not establish a clear primary retention driver.

---

# 💡 7. Business Recommendations

Based on the analysis, the following recommendations can be considered.

| Area | Recommendation |
|---|---|
| Network Performance | Monitor unsuccessful attempts and completed swap trends regularly. |
| Service Reliability | Investigate the top 10 stations contributing to non-completed events. |
| Vehicle Categories | Review operational issues affecting three-wheelers. |
| Station Performance | Evaluate maintenance and upgrade requirements for older station generations. |
| Battery Management | Monitor battery SOH and investigate low-performing battery suppliers and lots. |
| Pricing Strategy | Review peak/off-peak pricing and partner discount structures. |
| Customer Retention | Continue monitoring repeat usage and investigate one-time riders. |

These are recommendations based on observed patterns, not proven causal effects.

---

## 📁 8. Project Folder Structure

The project is organized into separate folders for datasets, Python analysis, outputs, SQL work, Excel work and presentation materials.

```text
VoltRelay_EV_Analytics_Hackathon_2026/
│
├── Data/
│   ├── Raw/
│   └── Cleaned_data/
│
├── python_analysis/
│   └── outputs/
├── Final_Presentation/
│
└── README.md
```

**Folder descriptions:**

- `Data/Raw/` – Original datasets.
- `Data/Cleaned_data/` – Cleaned datasets prepared for analysis.
- `python_analysis/outputs` – Python-based data analysis work/Generated analysis outputs and findings.
- `Final_Presentation/` – Presentation-related materials.
- `README.md` – Project documentation.

---

## ⚠️ 9. Important Assumptions & Limitations

To interpret the findings correctly, the following limitations should be considered.

1. **Synthetic Data:** The datasets represent a simulated business environment.
2. **Contribution Estimate:** Contribution includes estimated energy costs and prorated station rent and maintenance. It excludes battery depreciation, labour, payment processing and other costs.
3. **Retention Analysis:** The eligible cohort excludes riders whose first completed swap occurred within the final 30 days of the observation period.
4. **Missing CSAT:** Customer satisfaction data may not be missing randomly.
5. **Telemetry:** Blank telemetry values represent missing data, not zero.
6. **Timestamp Correction:** Firmware v3.2.0 timestamps from March 10 to April 14, 2025, were corrected by 5 hours and 30 minutes. The corrected event timestamp should be used.
7. **Test Stations:** `STN-TST` test stations were excluded from relevant analysis.
8. **Battery Cycles:** Observed swaps are a usage proxy and are not a direct measurement of battery charge cycles.
9. **Correlation vs Causation:** The findings describe observed associations and should not be treated as proof of causation.

---

## 📈 10. Project Deliverables

The project focuses on the following hackathon deliverables:

- **Google Colab Notebook:** Data understanding, cleaning, EDA, business analysis and visualizations.
- **Analysis Report:** Business questions, key findings, supporting visualizations and recommendations.
- **3-Minute Presentation:** A concise explanation of the problem, analytical approach, insights and recommendations.

---

## 🚀 11. Future Scope

The project can be extended with additional analytical capabilities:


- Automate recurring data cleaning and reporting.
- Develop station-level failure monitoring.
- Build battery health prediction models.
- Explore rider segmentation and retention strategies.
- Develop operational performance alerts.

These are potential future enhancements, not completed project features.

---

## 👨‍💻 12. Author

**Krish Keshari**

BSc Computer Science Student | Aspiring Data Analyst

**GitHub:** https://github.com/Kkiop90

**Project:** VoltRelay – EV Battery Swapping Network Analytics

---

## ⭐ Acknowledgement

This project was developed as part of the **Gradient Learnings Data Analytics Hackathon 2026**.

The project demonstrates how Python-based data analytics can be used to investigate business problems, identify operational patterns and communicate actionable insights.

---

**If you find this project interesting, consider giving the repository a ⭐!**
