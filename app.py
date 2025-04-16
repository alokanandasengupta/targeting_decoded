import streamlit as st
import pandas as pd
import base64
from io import BytesIO

st.set_page_config(page_title="CSV Processor", layout="wide")

# Title and description
st.title("CSV Data Processor")
st.markdown("Upload your CSV file and process data based on market selection.")

# ===== Configuration =====
COUNTRY_INFO = {
    '1': 10, '44': 10, '60': 9, '65': 8, '971': 9,
    '966': 9, '61': 9, '91': 10, '880': 8
}

currency_mapping = {
    'USD': {'code': '1', 'length': 10},
    'GBP': {'code': '44', 'length': 10},
    'MYR': {'code': '60', 'length': 9},
    'SGD': {'code': '65', 'length': 8},
    'AED': {'code': '971', 'length': 9},
    'SAR': {'code': '966', 'length': 9},
    'AUD': {'code': '61', 'length': 9},
    'CAD': {'code': '1', 'length': 10},
    'INR': {'code': '91', 'length': 10},
    'BDT': {'code': '880', 'length': 8}
}

# ===== Snippet 1: Extract phone from email prefix =====
def process_snippet1_data(df):
    results = []
    for _, row in df.iterrows():
        try:
            email = str(row['Email']).strip()
            if pd.isna(email) or '@' not in email:
                continue

            if any(domain in email.lower() for domain in ['@hoichoi.tv', '@hoichoitv.com']):
                phone_part = email.split('@')[0].strip()
                formatted_number = phone_part

                if phone_part.startswith('+'):
                    for code, length in COUNTRY_INFO.items():
                        if phone_part[1:].startswith(code):
                            number_part = ''.join(filter(str.isdigit, phone_part[1+len(code):]))
                            formatted_number = f"{code} {number_part[-length:]}" if number_part else phone_part
                            break

                results.append({'Email': email, 'Formatted_Number': formatted_number})

        except Exception as e:
            st.error(f"Error processing row in snippet 1: {e}")
            continue

    return pd.DataFrame(results)

# ===== Snippet 2: Format phones from Phone column =====
def process_snippet2_data(df):
    try:
        email_col = 'Email'
        phone_col = 'Phone'
        currency_col = 'currency'

        filtered_df = df[
            ~df[email_col].fillna('').str.lower().str.endswith(('@hoichoi.tv', '@hoichoitv.com'))
        ].copy()
        filtered_df = filtered_df[
            filtered_df[phone_col].notnull() &
            (filtered_df[phone_col].astype(str).str.strip() != '') &
            (filtered_df[phone_col].astype(str).str.replace(r'\D', '', regex=True).str.len() >= 5)
        ].copy()

        def format_phone(row):
            phone = ''.join(filter(str.isdigit, str(row[phone_col])))
            currency = str(row[currency_col]).strip()

            if currency in currency_mapping:
                code = currency_mapping[currency]['code']
                length = currency_mapping[currency]['length']
                if phone.startswith(code):
                    phone = phone[len(code):]
                return f"{code} {phone[:length]}"
            return ''

        filtered_df['clean_phone'] = filtered_df.apply(format_phone, axis=1)
        return filtered_df[[email_col, 'clean_phone']].rename(columns={email_col: 'Email'})

    except Exception as e:
        st.error(f"Error in snippet 2 processing: {e}")
        return pd.DataFrame()

# ===== Combine both phone outputs =====
def combine_results(df1, df2):
    combined = pd.concat([
        df1[['Email', 'Formatted_Number']].rename(columns={'Formatted_Number': 'Phone'}),
        df2[['Email', 'clean_phone']].rename(columns={'clean_phone': 'Phone'})
    ])
    combined = combined.drop_duplicates(subset=['Email', 'Phone'])
    final_result = combined.groupby('Email')['Phone'].apply(lambda x: ', '.join(filter(None, x))).reset_index()
    return final_result

# Function to create a download link for DataFrame
def get_table_download_link(df, filename, text):
    """Generates a link to download the DataFrame as a file"""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    excel_data = buffer.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{text}</a>'
    return href

# File upload
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    try:
        input_df = pd.read_csv(uploaded_file)
        st.success(f"✅ Successfully read {len(input_df)} records from uploaded file")
        
        # Display sample data
        st.subheader("Sample Data")
        st.dataframe(input_df.head())
        
        # Market selection
        st.subheader("Select Market")
        market_options = ["India", "Bangladesh", "International", "ALL"]
        selected_markets = st.multiselect("Choose markets to process:", market_options, default=["ALL"])
        
        if st.button("Process Data"):
            if not selected_markets:
                st.warning("Please select at least one market to proceed.")
            else:
                # Process the selected markets
                filtered_df = pd.DataFrame()
                
                if "ALL" in selected_markets:
                    filtered_df = input_df.copy()
                    st.info(f"🌐 All markets selected: {len(filtered_df)} records")
                else:
                    market_filters = []
                    if "India" in selected_markets:
                        india_df = input_df[input_df['currency'].str.upper() == 'INR']
                        market_filters.append(india_df)
                        st.info(f"🇮🇳 India market: {len(india_df)} records")
                    
                    if "Bangladesh" in selected_markets:
                        bangladesh_df = input_df[input_df['currency'].str.upper() == 'BDT']
                        market_filters.append(bangladesh_df)
                        st.info(f"🇧🇩 Bangladesh market: {len(bangladesh_df)} records")
                    
                    if "International" in selected_markets:
                        international_df = input_df[~input_df['currency'].str.upper().isin(['INR', 'BDT'])]
                        market_filters.append(international_df)
                        st.info(f"🌍 International market: {len(international_df)} records")
                    
                    filtered_df = pd.concat(market_filters)
                
                # Process data
                with st.spinner("Processing data..."):
                    df1 = process_snippet1_data(filtered_df)
                    df2 = process_snippet2_data(filtered_df)
                    final_result_df = combine_results(df1, df2)
                    
                    if final_result_df.empty:
                        st.warning("⚠️ No valid results to return")
                    else:
                        # Create separate Email and Phone DataFrames
                        emails_df = final_result_df[['Email']].dropna().drop_duplicates().reset_index(drop=True)
                        phones_df = final_result_df[['Phone']].dropna().drop_duplicates().reset_index(drop=True)
                        
                        # Filter out undesired entries
                        emails_df = emails_df[~emails_df['Email'].str.lower().str.endswith(('@hoichoi.tv', '@hoichoitv.com', '@viewlift.com'))]
                        phones_df = phones_df[~phones_df['Phone'].str.strip().str.startswith('+')]
                        
                        # Display results
                        st.subheader("Results")
                        
                        # Show email count
                        st.metric("Total Emails", len(emails_df))
                        
                        # Show phone number count
                        st.metric("Total Phone Numbers", len(phones_df))
                        
                        # Download links
                        st.markdown("### Download Processed Data")
                        
                        # Create Excel file with two sheets
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            emails_df.to_excel(writer, sheet_name='Emails', index=False)
                            phones_df.to_excel(writer, sheet_name='Phones', index=False)
                        
                        buffer.seek(0)
                        b64 = base64.b64encode(buffer.read()).decode()
                        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="processed_data.xlsx">Download Excel with Emails and Phones</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        
                        # Display sample emails and phones
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Sample Emails")
                            st.dataframe(emails_df.head(10))
                        
                        with col2:
                            st.subheader("Sample Phone Numbers")
                            st.dataframe(phones_df.head(10))
                        
    except Exception as e:
        st.error(f"Error processing file: {e}")

# Footer with instructions
st.markdown("---")
st.markdown("""
### How to Use
1. Upload your CSV file containing email, phone, and currency data
2. Select which markets you want to process
3. Click "Process Data" to analyze the file
4. Download the results as an Excel file with separate sheets for emails and phone numbers
""")

# GitHub repository information
st.sidebar.header("About")
st.sidebar.info(
    "This is a CSV processing app for extracting and formatting emails and phone numbers. "
    "The source code is available on GitHub."
)

# Add version information
st.sidebar.markdown("v1.0.0")