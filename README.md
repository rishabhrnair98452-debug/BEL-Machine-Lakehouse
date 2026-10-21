# Unified Data Lakehouse for Machine Health Monitoring and Predictive Maintenance

A Flask-based machine health monitoring dashboard designed to organize sensor data, identify potentially abnormal machine conditions, and support predictive maintenance workflows.

## 📌 Project Overview

Industrial machines generate sensor data such as temperature, vibration, and pressure. Monitoring these parameters can help maintenance teams identify unusual operating conditions and investigate potential equipment problems.

This project demonstrates a data lakehouse workflow that organizes machine sensor data into Bronze, Silver, and Gold layers and presents machine health information through a web-based dashboard.

**Project:** Unified Data Lakehouse for Machine Health Monitoring and Predictive Maintenance
**Organization:** Bharat Electronics Limited (BEL) — Internship Project
**Technology Focus:** Python, Flask, Pandas, Data Engineering, and Machine Health Monitoring

## 🎯 Objectives

* Organize machine sensor data using a layered data processing approach.
* Clean and prepare sensor records for analysis.
* Generate machine-level summaries and identify potentially abnormal readings.
* Display machine health information through a web dashboard.
* Support report generation and data export.
* Establish a foundation for future predictive maintenance and analytics capabilities.

## ✨ Key Features

* **Machine Health Dashboard:** View machine sensor readings and summarized health information.
* **Sensor Data Processing:** Process and clean machine sensor records using Python and Pandas.
* **Bronze, Silver, and Gold Layers:** Organize data into raw, cleaned, and analytical stages.
* **Condition Monitoring:** Identify readings that cross configurable demonstration thresholds.
* **Machine-Level Reports:** Present summarized information for individual machines.
* **Data Export:** Export supported reports or dashboard data to CSV.
* **User Authentication:** Provide a login interface for authorized dashboard access.
* **Role-Based Access:** Support role-specific access where configured in the application.

> Note: This repository contains a prototype. Demonstration thresholds and synthetic sensor readings must not be treated as validated operational limits for actual industrial equipment.

## 🏗️ Architecture

```text
       Machine Sensor Data
                |
                v
       +------------------+
       |   Bronze Layer   |
       |    Raw Data      |
       +------------------+
                |
                v
       +------------------+
       |   Silver Layer   |
       | Cleaned Data     |
       +------------------+
                |
                v
       +------------------+
       |    Gold Layer    |
       | Analytical Data  |
       +------------------+
                |
                v
       +------------------+
       | Python + Pandas  |
       | Data Processing  |
       +------------------+
                |
                v
       +------------------+
       |   Flask Web App  |
       | Dashboard/Reports|
       +------------------+
                |
                v
       Machine Health Monitoring
```

The diagram represents the intended data-processing workflow. Individual integrations should be considered implemented only when they are configured and working in the application.

## 🛠️ Technology Stack

| Technology     | Purpose                                    |
| -------------- | ------------------------------------------ |
| Python         | Application and data processing            |
| Flask          | Web application and backend                |
| Pandas         | Sensor data cleaning and analysis          |
| HTML and CSS   | Dashboard and login interface              |
| JavaScript     | Dashboard interactions                     |
| SQLite         | Local user database, where configured      |
| CSV            | Sensor data storage and exchange           |
| Git and GitHub | Version control and source code management |

## 📂 Project Structure

```text
BEL_Machine_Lakehouse_Fixed/
│
├── app.py
├── auth.py
├── create_admin.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   ├── silver/
│   └── gold/
│
├── templates/
│   ├── login.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── venv/                  # Local virtual environment
```

The exact contents of the `templates/`, `static/`, and `data/` folders may vary depending on your current project files. The local virtual environment and secret configuration should not be committed to GitHub.

## ⚙️ Installation and Setup

### Prerequisites

* Python 3.12 or a compatible Python version
* Git
* Visual Studio Code (recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/rishabhrnair98452-debug/BEL-Machine-Lakehouse.git
```

### 2. Open the Project Folder

```bash
cd BEL-Machine-Lakehouse
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a local `.env` file in the project root and configure the secret key required by your application.

Do not publish your real secret key or other credentials on GitHub. Follow the environment variable names expected by your current application.

### 7. Initialize the Admin Account

If your application requires initial user creation, follow the project's configured user setup process. For example:

```bash
python create_admin.py
```

Run this command only after reviewing the script and confirming that its database and credential setup match your application.

### 8. Start the Application

```bash
python app.py
```

Open the local address printed by Flask in your terminal. The application is intended to run locally unless you separately configure a deployment environment.

## 📊 Data Processing Workflow

### Bronze Layer — Raw Data

Stores incoming sensor records before cleaning or transformation.

### Silver Layer — Cleaned Data

Processes sensor records to improve consistency and prepare the data for analysis.

### Gold Layer — Analytical Data

Contains aggregated information, such as machine-level readings and health summaries, for dashboard reporting.

### Machine Health Monitoring

The application evaluates sensor readings against configured demonstration thresholds to highlight conditions that may require further inspection.

## 🔒 Security Considerations

* Keep `.env` files and secret keys out of version control.
* Do not upload real passwords, database credentials, or private configuration files.
* Use authorized and appropriately protected accounts.
* Review role permissions before using the application with multiple users.
* Use synthetic or explicitly approved data for demonstrations.
* Do not connect this prototype to operational industrial equipment without appropriate validation, security review, and authorization.

## 🚀 Future Enhancements

* Integrate a production-ready object storage system for the lakehouse layers.
* Introduce scalable distributed data processing where required.
* Implement automated data ingestion and scheduled pipelines.
* Add time-series trend analysis and configurable alerts.
* Evaluate machine learning models for predictive maintenance using suitable historical data.
* Improve audit logging, access controls, and deployment security.
* Validate thresholds and analytical methods against approved equipment specifications.

## 👨‍💻 Developer

Developed as an internship project focused on data engineering and machine health monitoring.

**GitHub Repository:**
https://github.com/rishabhrnair98452-debug/BEL-Machine-Lakehouse

---

*This project is a demonstration and development prototype. It is not a certified industrial monitoring or safety system.*
