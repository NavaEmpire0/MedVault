<div align="center">
<img src="medvault_logo.png" alt="MedVault Logo" width="200"/>
<h1>MedVault: QR-Based Health Dashboard</h1>
<p>
Your personal health record, accessible anywhere. A Streamlit web application for creating, managing, and sharing a secure digital health profile via a scannable QR code.
</p>

</div>

📖 About The Project
MedVault is a web application designed to solve the problem of managing and accessing personal health reports, especially in environments without advanced digital infrastructure. It allows patients to create a persistent digital profile, upload medical documents, and generate a unique QR code. This QR code can be scanned by any smartphone to display a secure, view-only version of their health dashboard, making it easy to share critical information with doctors quickly and efficiently.

✨ Core Features
Secure Patient Profiles: Create a persistent health profile protected by a Patient ID and a PIN.

Editable Dashboard: Log in to a full-featured dashboard to edit personal details, update medication lists, and manage your profile picture.

File Uploads: Easily upload and store medical documents like blood tests, X-ray reports, and more.

Shareable QR Codes: Generate a unique QR code that links to a password-less, read-only version of your dashboard, perfect for sharing with healthcare providers.

Interactive Medication Management: Build and manage lists for "Currently Using Medicines" and "Medication History" with an easy-to-use interface.

Integrated Drug API: Look up information on common medications directly within the app, powered by the openFDA API.

🛠️ Built With
Streamlit

Pandas

QRCode

Pillow

Requests

🚀 Getting Started
Follow these steps to get a local copy up and running.

Prerequisites
Python 3.9 or higher

pip package manager

Installation
Clone the repository (or download the files):

Bash

git clone https://github.com/NavaEmpire0/MedVault.git
cd MedVault
Create the required folder structure:
The application needs a data folder with an uploads subfolder to store patient files.

Bash

mkdir -p data/uploads
Install the required packages:

Bash

pip install -r requirements.txt
Running the App
Navigate to the project directory in your terminal.

Run the following command:

Bash

streamlit run app.py
Your web browser should automatically open to the application's login page.

📁 Project Structure
MedVault/
├── app.py              # The main Streamlit application script
├── requirements.txt    # All Python dependencies
├── medvault_logo.png   # The application logo
└── data/
    ├── drug_map.csv    # Maps Indian to US drug names for the API
    ├── patients.csv    # The simple database for patient profiles
    └── uploads/        # Directory to store uploaded reports and profile pictures
📜 Usage
The application has two main user journeys:

1. Creating a New Profile
From the login page, click "Create a New Health Profile".

Fill in your mandatory personal details (Name, DOB, Blood Group).

Use the interactive builder to add your current and past medications. You can select from a list or add a custom one by choosing "Other...".

Optionally, upload a profile picture and any initial health reports.

Click the "Create Profile" button at the bottom.

Securely save the generated Patient ID and PIN. You will need these to log in later.

2. Logging In and Managing Your Dashboard
Use your Patient ID and PIN to log in.

You will be taken to your full, editable dashboard. Here you can:

Update your personal information in the "Edit Your Profile" section.

Upload new reports.

Download existing reports.

Look up drug information.

View and save your shareable QR code.

3. Sharing with a Doctor
From your dashboard, show the QR code to your doctor.

They can scan it with any smartphone camera.

The link will open a view-only version of your dashboard with all your key information and reports, but with no option to edit or see your PIN.

📄 License
Distributed under the MIT License. See LICENSE for more information.

📧 Contact
Project Link: https://github.com/NavaEmpire0/MedVault