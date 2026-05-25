# 👮‍♂️ Smart Traffic Violation Logger (E-Challan System)

## 📌 Overview
The **Smart Traffic Violation Logger** is a Flask-based web application designed to help traffic police officials record and manage vehicle violations efficiently. The system automates the process of generating "E-Challans" by providing unique QR codes for every recorded violation, which can be scanned to view the status of the fine.

## 🚀 Key Features
- **Secure Police Authentication:** Restricted access for authorized personnel only.
- **Violation Recording:** Easily log vehicle numbers, violation types (Speeding, No Helmet, etc.), location, and fine amounts.
- **Automated QR Code Generation:** Every violation record automatically generates a unique QR code.
- **Public Status Page:** Citizens can scan the QR code to check their violation details and payment status.
- **Search & Filter History:** Admins can search for specific vehicle numbers or filter violations by status (Paid/Unpaid).
- **Status Management:** Officials can update violation status from "Unpaid" to "Paid" once the fine is settled.

## 🛠️ Technology Stack
- **Backend:** Python (Flask)
- **Database:** SQLite (SQLAlchemy ORM)
- **Security:** Flask-Bcrypt (Password Hashing), Flask-Login (Session Management)
- **QR Engine:** Python-QRcode (with PIL/Pillow)
- **Frontend:** HTML5, CSS3, Bootstrap 5.3 (Responsive Design)

## 📊 Database Models
1. **User:** Stores admin/police credentials.
2. **Violation:** Stores vehicle number, violation type, location, date, fine amount, status, and QR code path.

## ⚙️ Installation & Setup
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd CN-2
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```
   *The app will be accessible at `http://127.0.0.1:5000/`*

4. **Default Credentials:**
   - **Username:** `Artheesh`
   - **Password:** `Artheesh123`

## 📁 Project Structure
- `app.py`: Main application logic and routes.
- `models.py`: Database schema (integrated in app.py).
- `templates/`: HTML templates (Jinja2).
- `static/`: CSS files and generated QR codes.
- `instance/`: SQLite database storage.

## 🛡️ License
This project is developed for educational purposes as part of a Computer Science Capstone Project.

---
Developed by **Artheesh** 👮‍♂️
