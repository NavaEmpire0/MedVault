import streamlit as st
import pandas as pd
import os
import qrcode
from PIL import Image
import random
import datetime
from io import BytesIO
import requests

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="MedVault Dashboard",
    page_icon="⚕️",
    layout="wide"
)

# --- PATHS AND FOLDER SETUP ---
DATA_DIR = "data"
PATIENTS_CSV_PATH = os.path.join(DATA_DIR, "patients.csv")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
DRUG_MAP_CSV_PATH = os.path.join(DATA_DIR, "drug_map.csv") 

LOGO_PATH = "medvault_logo.png"

os.makedirs(UPLOADS_DIR, exist_ok=True)
if not os.path.exists(PATIENTS_CSV_PATH):
    pd.DataFrame(columns=['patient_id', 'name', 'dob', 'blood_group', 'current_medications', 'medication_history', 'pin']).to_csv(PATIENTS_CSV_PATH, index=False)
if not os.path.exists(DRUG_MAP_CSV_PATH):
     pd.DataFrame({
         'indian_name': ['paracetamol', 'crocin', 'calpol', 'dolo', 'combiflam', 'brufen', 'ibuprofen', 'aspirin', 'disprin', 'benadryl'],
         'us_name': ['acetaminophen', 'acetaminophen', 'acetaminophen', 'acetaminophen', 'ibuprofen', 'ibuprofen', 'ibuprofen', 'aspirin', 'aspirin', 'diphenhydramine']
     }).to_csv(DRUG_MAP_CSV_PATH, index=False)

# --- HELPER FUNCTIONS ---
def load_patients_df():
    return pd.read_csv(PATIENTS_CSV_PATH, dtype={'pin': str}).fillna('')

def save_patients_df(df):
    df.to_csv(PATIENTS_CSV_PATH, index=False)

# --- FIX: Rewritten function for robust ID generation ---
def generate_patient_id(df):
    """Generates a new patient ID by finding the maximum existing ID and incrementing it."""
    if df.empty:
        return "PAT001"
    
    # Extract numbers from all existing patient IDs
    existing_ids = df['patient_id'].str.replace("PAT", "").astype(int)
    # Find the highest number
    max_id = existing_ids.max()
    # Increment to get the new ID number
    new_id_num = max_id + 1
    # Format back into PATXXX format
    return f"PAT{new_id_num:03d}"
    
def authenticate_patient(patient_id, pin):
    df = load_patients_df()
    patient_record = df[(df['patient_id'] == patient_id) & (df['pin'] == pin)]
    if not patient_record.empty:
        return patient_record.iloc[0].to_dict()
    return None
    
def get_patient_files(patient_id):
    patient_folder = os.path.join(UPLOADS_DIR, patient_id)
    files_to_exclude = ['profile_pic.png', 'profile_pic.jpg', 'profile_pic.jpeg']
    if os.path.exists(patient_folder):
        return [f for f in os.listdir(patient_folder) if f.lower() not in files_to_exclude]
    return []

def load_drug_map():
    if os.path.exists(DRUG_MAP_CSV_PATH):
        return pd.read_csv(DRUG_MAP_CSV_PATH)
    return pd.DataFrame(columns=['indian_name', 'us_name'])

@st.cache_data(ttl=3600)
def fetch_drug_info(drug_name):
    drug_map_df = load_drug_map()
    search_term = drug_name.lower()
    match = drug_map_df[drug_map_df['indian_name'].str.lower() == search_term]
    
    api_search_term = match.iloc[0]['us_name'] if not match.empty else drug_name
    
    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:\"{api_search_term}\"&limit=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'results' in data and data['results']:
            drug_info = data['results'][0]
            info = {
                "Purpose": drug_info.get('purpose', ["Not available"])[0],
                "Warnings": drug_info.get('warnings', ["Not available"])[0],
                "Active Ingredient": drug_info.get('active_ingredient', ["Not available"])[0],
            }
            return info
        else:
            return {"Error": f"No information found for '{drug_name}'."}
    except requests.exceptions.RequestException:
        return {"Error": f"Could not connect to the server. Please check your internet connection."}

# --- SESSION STATE MANAGEMENT ---
if 'page' not in st.session_state: st.session_state['page'] = 'login'
if 'logged_in_patient' not in st.session_state: st.session_state['logged_in_patient'] = None
if 'view_only_patient_data' not in st.session_state: st.session_state['view_only_patient_data'] = None
if 'new_profile_info' not in st.session_state: st.session_state['new_profile_info'] = None
if 'current_med_list' not in st.session_state: st.session_state['current_med_list'] = []
if 'history_med_list' not in st.session_state: st.session_state['history_med_list'] = []

# --- UI DRAWING FUNCTIONS ---

def draw_login_page():
    st.session_state['current_med_list'] = []
    st.session_state['history_med_list'] = []

    logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
    with logo_col2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        else:
            st.title("MedVault Dashboard")

    st.markdown("<h2 style='text-align: center; color: grey;'>Your personal health record, accessible anywhere.</h2>", unsafe_allow_html=True)
    st.divider()

    login_token = st.query_params.get("token")
    if login_token and not st.session_state.get('logged_in_patient'):
        try:
            patient_id, pin = login_token.split('_')
            patient_data = authenticate_patient(patient_id, pin)
            if patient_data:
                st.session_state['view_only_patient_data'] = patient_data
                st.session_state['page'] = 'view_only_dashboard'
                st.query_params.clear()
                st.rerun()
        except (ValueError, IndexError):
            st.error("Invalid or expired QR code link.")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Login to Your Dashboard")
        with st.form("login_form"):
            patient_id = st.text_input("Patient ID")
            pin = st.text_input("PIN", type="password")
            submitted = st.form_submit_button("Login 🔑")
            if submitted:
                with st.spinner("Authenticating..."):
                    patient_data = authenticate_patient(patient_id, pin)
                    if patient_data:
                        st.session_state['logged_in_patient'] = patient_data
                        st.session_state['page'] = 'dashboard'
                        st.rerun()
                    else:
                        st.error("Invalid Patient ID or PIN.")
    with c2:
        st.subheader("Don't have a profile?")
        st.info("Create a secure health profile to manage your medical reports and information.")
        if st.button("Create a New Health Profile ➕"):
            st.session_state['page'] = 'create_profile'
            st.rerun()

def draw_create_profile_page():
    st.title("Create Your Health Profile")
    st.info("Fill out your details below. The final 'Create Profile' button is at the bottom of the page.")

    with st.container(border=True):
        st.subheader("🧑 Personal Information (Mandatory)")
        name = st.text_input("Full Name*")
        dob = st.date_input("Date of Birth*", value=None, min_value=datetime.date(1920, 1, 1))
        blood_group = st.selectbox("Blood Group*", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], index=None, placeholder="Select...")

    st.divider()

    with st.container(border=True):
        st.subheader("💊 Build Your Medication Lists")
        drug_map_df = load_drug_map()
        known_drugs = ["--- Select a Drug ---"] + sorted(drug_map_df['indian_name'].str.capitalize().tolist()) + ["Other..."]
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Currently Using Medicines**")
            selected_current_med = st.selectbox("Select to add to current list", options=known_drugs, key="current_med_selector")
            
            other_current_med = ""
            if selected_current_med == "Other...":
                other_current_med = st.text_input("Enter custom medication name", key="other_current")

            if st.button("Add to Current List"):
                med_to_add = other_current_med if selected_current_med == "Other..." else selected_current_med
                if med_to_add and med_to_add != "--- Select a Drug ---" and med_to_add not in st.session_state.current_med_list:
                    st.session_state.current_med_list.append(med_to_add)
            
            if st.session_state.current_med_list:
                st.write("Current Medication List:")
                for i, med in enumerate(st.session_state.current_med_list):
                    col_med, col_btn = st.columns([4,1])
                    with col_med:
                        st.markdown(f"- {med}")
                    with col_btn:
                        if st.button("Remove", key=f"remove_current_{i}"):
                            st.session_state.current_med_list.pop(i)
                            st.rerun()
        with c2:
            st.write("**Medication History**")
            selected_history_med = st.selectbox("Select to add to history", options=known_drugs, key="history_med_selector")

            other_history_med = ""
            if selected_history_med == "Other...":
                other_history_med = st.text_input("Enter custom medication name", key="other_history")

            if st.button("Add to History List"):
                med_to_add = other_history_med if selected_history_med == "Other..." else selected_history_med
                if med_to_add and med_to_add != "--- Select a Drug ---" and med_to_add not in st.session_state.history_med_list:
                    st.session_state.history_med_list.append(med_to_add)

            if st.session_state.history_med_list:
                st.write("Medication History List:")
                for i, med in enumerate(st.session_state.history_med_list):
                    col_med, col_btn = st.columns([4,1])
                    with col_med:
                        st.markdown(f"- {med}")
                    with col_btn:
                        if st.button("Remove", key=f"remove_history_{i}"):
                            st.session_state.history_med_list.pop(i)
                            st.rerun()
    
    with st.expander("🔍 Unsure about a medication? Look it up here."):
        drug_to_lookup = st.selectbox("Select a medication to look up", options=known_drugs, key="create_lookup")
        if st.button("Look up Info", key="create_lookup_btn"):
            if drug_to_lookup != "--- Select a Drug ---" and drug_to_lookup != "Other...":
                with st.spinner(f"Searching for {drug_to_lookup}..."):
                    drug_details = fetch_drug_info(drug_to_lookup)
                    if "Error" in drug_details:
                        st.error(drug_details["Error"])
                    else:
                        st.success(f"Information for {drug_to_lookup}:")
                        st.json(drug_details)
            else:
                st.warning("Please select a specific medication from the list to look up.")

    st.divider()

    with st.container(border=True):
        st.subheader("🖼️ Profile Picture and Reports (Optional)")
        profile_pic = st.file_uploader("Upload a profile picture", type=['png', 'jpg', 'jpeg'])
        initial_reports = st.file_uploader("Upload initial health reports", accept_multiple_files=True, type=["pdf", "png", "jpg", "csv"])

    st.divider()

    if st.button("Create Profile", type="primary", use_container_width=True):
        if not name or not dob or not blood_group:
            st.error("Please fill in all mandatory fields (*) in the Personal Information section.")
        else:
            with st.spinner("Creating your secure profile..."):
                patients_df = load_patients_df()
                patient_id = generate_patient_id(patients_df)
                pin = str(random.randint(1000, 9999))
                
                current_medications_str = "\n".join(st.session_state.current_med_list)
                medication_history_str = "\n".join(st.session_state.history_med_list)

                new_patient_data = {
                    'patient_id': patient_id, 'name': name, 'dob': dob.strftime("%Y-%m-%d"),
                    'blood_group': blood_group, 'current_medications': current_medications_str, 
                    'medication_history': medication_history_str, 'pin': pin
                }
                new_df = pd.DataFrame([new_patient_data])
                patients_df = pd.concat([patients_df, new_df], ignore_index=True)
                save_patients_df(patients_df)
                
                patient_folder = os.path.join(UPLOADS_DIR, patient_id)
                os.makedirs(patient_folder, exist_ok=True)
                if profile_pic:
                    ext = profile_pic.name.split('.')[-1]
                    with open(os.path.join(patient_folder, f'profile_pic.{ext}'), "wb") as f: f.write(profile_pic.getbuffer())
                for report in initial_reports:
                    with open(os.path.join(patient_folder, report.name), "wb") as f: f.write(report.getbuffer())
                
                st.session_state['new_profile_info'] = {'patient_id': patient_id, 'pin': pin}
            st.rerun()

    if st.session_state.get('new_profile_info'):
        info = st.session_state['new_profile_info']
        st.success("Profile Created Successfully!")
        st.info("Please save your credentials securely:")
        st.code(f"Patient ID: {info['patient_id']}\nPIN: {info['pin']}")
        
        if st.button("Go to Login Page"):
            st.session_state['new_profile_info'] = None
            st.session_state['page'] = 'login'
            st.rerun()

def draw_dashboard():
    patient = st.session_state['logged_in_patient']
    st.title(f"MedVault Dashboard for {patient['name']}")
    col1, col2 = st.columns([1, 3])
    with col1:
        profile_pic_path = None
        for ext in ['png', 'jpg', 'jpeg']:
            path = os.path.join(UPLOADS_DIR, patient['patient_id'], f'profile_pic.{ext}')
            if os.path.exists(path):
                profile_pic_path = path
                break
        st.image(profile_pic_path if profile_pic_path else "https://www.iconpacks.net/icons/2/free-user-icon-3296-thumb.png", use_container_width=True)
    with col2:
        st.subheader("Your Details")
        m1, m2, m3 = st.columns(3)
        m1.metric("Patient ID", patient['patient_id'])
        m2.metric("Date of Birth", patient['dob'])
        m3.metric("Blood Group", patient['blood_group'])
        with st.expander("✏️ Edit Your Profile"):
            with st.form("edit_profile_form"):
                new_name = st.text_input("Full Name", value=patient['name'])
                new_dob = st.date_input("Date of Birth", value=datetime.datetime.strptime(patient['dob'], "%Y-%m-%d").date(), min_value=datetime.date(1920, 1, 1))
                blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
                new_blood_group = st.selectbox("Blood Group", blood_groups, index=blood_groups.index(patient['blood_group']))
                new_current_medications = st.text_area("Currently Using Medicines", value=patient.get('current_medications', ''))
                new_medication_history = st.text_area("Medication History", value=patient.get('medication_history', ''))
                new_profile_pic = st.file_uploader("Upload new profile picture", type=['png', 'jpg', 'jpeg'])
                update_submitted = st.form_submit_button("Update Profile")
                if update_submitted:
                    with st.spinner("Saving your changes..."):
                        df = load_patients_df()
                        patient_index = df.index[df['patient_id'] == patient['patient_id']].tolist()[0]
                        df.at[patient_index, 'name'] = new_name
                        df.at[patient_index, 'dob'] = new_dob.strftime("%Y-%m-%d")
                        df.at[patient_index, 'blood_group'] = new_blood_group
                        df.at[patient_index, 'current_medications'] = new_current_medications
                        df.at[patient_index, 'medication_history'] = new_medication_history
                        save_patients_df(df)
                        if new_profile_pic:
                            ext = new_profile_pic.name.split('.')[-1]
                            with open(os.path.join(UPLOADS_DIR, patient['patient_id'], f'profile_pic.{ext}'), "wb") as f:
                                f.write(new_profile_pic.getbuffer())
                    st.session_state['logged_in_patient'] = authenticate_patient(patient['patient_id'], patient['pin'])
                    st.success("Profile updated successfully!")
                    st.rerun()

    st.divider()
    med_col, report_col = st.columns(2)
    with med_col:
        st.subheader("💊 Current Medicines")
        current_meds_list = [med for med in str(patient.get('current_medications', '')).splitlines() if med.strip()]
        st.info(", ".join(current_meds_list) if current_meds_list else "No current medications listed.")
        
        st.subheader("📜 Medication History")
        history_meds_list = [med for med in str(patient.get('medication_history', '')).splitlines() if med.strip()]
        st.info(", ".join(history_meds_list) if history_meds_list else "No medication history listed.")
    with report_col:
        st.subheader("📁 Your Health Reports")
        uploaded_file = st.file_uploader("Upload a new report", type=["pdf", "png", "jpg", "csv"], key="report_uploader")
        if uploaded_file:
            with st.spinner(f"Uploading {uploaded_file.name}..."):
                with open(os.path.join(UPLOADS_DIR, patient['patient_id'], uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
            st.success(f"Report '{uploaded_file.name}' uploaded!")
            st.rerun()
        patient_files = get_patient_files(patient['patient_id'])
        if patient_files:
            for file_name in patient_files:
                file_path = os.path.join(UPLOADS_DIR, patient['patient_id'], file_name)
                with open(file_path, "rb") as f:
                    st.download_button(f"📄 Download {file_name}", f.read(), file_name, key=f"download_dash_{file_name}")
        else:
            st.info("No reports uploaded yet.")
            
    st.divider()
    with st.expander("🔍 Drug Information Lookup (Supports Indian Names)"):
        drug_map_df = load_drug_map()
        known_drugs = ["--- Select a Drug ---"] + sorted(drug_map_df['indian_name'].str.capitalize().tolist())
        search_term = st.selectbox("Select a common medication to look up", options=known_drugs, key="dash_lookup")
        if st.button("Search for Drug Info"):
            if search_term != "--- Select a Drug ---":
                with st.spinner(f"Searching for {search_term}..."):
                    drug_details = fetch_drug_info(search_term)
                    if "Error" in drug_details:
                        st.error(drug_details["Error"])
                    else:
                        st.success(f"Information for {search_term}:")
                        st.json(drug_details)
            else:
                st.warning("Please select a medication to search.")

    st.divider()
    qr_col1, qr_col2 = st.columns([2,1])
    with qr_col1:
        st.subheader("📲 Share Your Dashboard")
        st.info("Scan this QR code to get instant, password-less access to a view-only version of this dashboard.")
    with qr_col2:
        BASE_URL = "https://medvault.streamlit.app" 
        login_token = f"{patient['patient_id']}_{patient['pin']}"
        qr_data = f"{BASE_URL}/?token={login_token}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.image(buf, use_container_width=True)

    if st.button("Logout"):
        st.session_state['page'] = 'login'
        st.session_state['logged_in_patient'] = None
        st.query_params.clear()
        st.rerun()

def draw_view_only_dashboard():
    patient = st.session_state['view_only_patient_data']
    st.title(f"MedVault Dashboard for {patient['name']}")
    col1, col2 = st.columns([1, 3])
    with col1:
        profile_pic_path = None
        for ext in ['png', 'jpg', 'jpeg']:
            path = os.path.join(UPLOADS_DIR, patient['patient_id'], f'profile_pic.{ext}')
            if os.path.exists(path):
                profile_pic_path = path
                break
        st.image(profile_pic_path if profile_pic_path else "https://www.iconpacks.net/icons/2/free-user-icon-3296-thumb.png", use_container_width=True)
    with col2:
        st.subheader("Patient Details")
        m1, m2, m3 = st.columns(3)
        m1.metric("Patient ID", patient['patient_id'])
        m2.metric("Date of Birth", patient['dob'])
        m3.metric("Blood Group", patient['blood_group'])
    st.divider()
    med_col, report_col = st.columns(2)
    with med_col:
        st.subheader("💊 Current Medicines")
        current_meds_list = [med for med in str(patient.get('current_medications', '')).splitlines() if med.strip()]
        st.info(", ".join(current_meds_list) if current_meds_list else "No current medications listed.")

        st.subheader("📜 Medication History")
        history_meds_list = [med for med in str(patient.get('medication_history', '')).splitlines() if med.strip()]
        st.info(", ".join(history_meds_list) if history_meds_list else "No medication history listed.")
    with report_col:
        st.subheader("📁 Health Reports")
        patient_files = get_patient_files(patient['patient_id'])
        if patient_files:
            for file_name in patient_files:
                file_path = os.path.join(UPLOADS_DIR, patient['patient_id'], file_name)
                with open(file_path, "rb") as f:
                    st.download_button(f"📄 Download {file_name}", f.read(), file_name, key=f"download_view_{file_name}")
        else:
            st.info("No reports available.")
    st.divider()
    if st.button("Back to Main Page"):
        st.session_state['page'] = 'login'
        st.session_state['view_only_patient_data'] = None
        st.rerun()

# --- MAIN ROUTER ---
if st.session_state['page'] == 'login':
    draw_login_page()
elif st.session_state['page'] == 'create_profile':
    draw_create_profile_page()
elif st.session_state['page'] == 'dashboard' and st.session_state['logged_in_patient']:
    draw_dashboard()
elif st.session_state['page'] == 'view_only_dashboard' and st.session_state['view_only_patient_data']:
    draw_view_only_dashboard()
else:
    draw_login_page()