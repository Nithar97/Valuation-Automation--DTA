import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
import os
import numpy as np
from datetime import datetime, timedelta

# Set Streamlit page configuration
st.set_page_config(page_title="VALUATION AUTOMATION", layout="wide")


# Display the logo
st.image("./image/hnblogo.jpg", width=50, use_column_width="auto")

# Display the logo at the right corner


# Apply custom CSS for styling
def local_css():
    st.markdown(
        """
        <style>
            .title {
                color: #ffffff;
                text-align: center;
                background-color: #4CAF50;
                padding: 10px;
                border-radius: 10px;
            }
            .frame {
                border: 3px solid #ff9800;
                padding: 15px;
                border-radius: 15px;
                background-color: #f9f9f9;
            }
            .footer {
                text-align: center;
                font-size: 18px;
                font-weight: bold;
                color: white;
                background: linear-gradient(to right, #ff416c, #ff4b2b);
                padding: 15px;
                border-radius: 10px;
                margin-top: 30px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
local_css()


# Title and Description
st.markdown("<h1 class='title'>MP File - MRP/Micro/Tackafull</h1></BR>", unsafe_allow_html=True)

# Load and Display Image 
image_path = "IMAGE/Image1.webp"  # Adjust the image filename as necessary
if os.path.exists(image_path):
    image = Image.open(image_path)
    st.image(image, use_column_width=True)


# Valuation Date Input
st.markdown("<div class='frame'>", unsafe_allow_html=True)
st.subheader("Step 1: Choose Valuation Date")
valuation_date = st.date_input("Select Valuation Date:")
st.markdown("</div>", unsafe_allow_html=True)

# Load RI_Company Table (Preloaded from TABLE folder)
ri_company_path = "TABLE/RI_Company.csv"
try:
    ri_company_df = pd.read_csv(ri_company_path, dtype=str)
    ri_company_dict = dict(zip(ri_company_df['PolicyNo'].astype(str).str.strip(), ri_company_df['RI_Company'].astype(str).str.strip()))
except Exception as e:
    st.error(f"Error loading RI_Company table: {e}")
    ri_company_dict = {}

# Load MRP_LOAN_TYPE Table (Preloaded from TABLE folder)
mrp_loan_type_path = "TABLE/MRP_LOAN_TYPE.csv"
try:
    mrp_loan_type_df = pd.read_csv(mrp_loan_type_path, dtype=str)
    mrp_loan_type_dict = dict(zip(mrp_loan_type_df['Product Code'].astype(str).str.strip(),
                                  mrp_loan_type_df['Loan Type - RBC'].astype(str).str.strip()))
except Exception as e:
    st.error(f"Error loading MRP_LOAN_TYPE table: {e}")
    mrp_loan_type_dict = {}


# File Upload Section
st.markdown("<div class='frame'>", unsafe_allow_html=True)
st.subheader("Step 2: Upload Your File (Excel or CSV)")
uploaded_file = st.file_uploader("Upload a file (File should be Excel or CSV formet)", type=["csv", "xlsx"], key="file_uploader")
st.markdown("</div>", unsafe_allow_html=True)


if uploaded_file:
    try:
        # Read file without headers to preview data
        preview_df = pd.read_csv(uploaded_file, header=None, dtype=str, nrows=10) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file, header=None, dtype=str, nrows=10)
        
        # Display preview for user reference
        st.markdown("<div class='frame'>", unsafe_allow_html=True)        
        st.subheader("Uploaded File Preview:")
        st.dataframe(preview_df)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Header Row Selection
        st.markdown("<div class='frame'>", unsafe_allow_html=True)
        st.subheader("Step 3: Select Header Row")
        header_row = st.number_input("Header Row:", min_value=0, max_value=len(preview_df)-1, value=4, step=1)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Read file again with the chosen header row
        uploaded_file.seek(0)  # Reset file pointer
        input_df = pd.read_csv(uploaded_file, skiprows=header_row) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file, skiprows=header_row)
        
        if input_df.empty or len(input_df.columns) == 0:
            st.error("Error: No valid columns detected after skipping the selected header row. Please choose a different row.")
        else:
            try:
                # Rename columns based on the chosen header row
                input_df.columns = input_df.iloc[0]
                input_df = input_df[1:].reset_index(drop=True)
                
                # Display processed file
                st.subheader("Processed File:")
                st.dataframe(input_df)
                
                # Step 4: Ignore Group Data
                st.subheader("Step 4: Ignore Group Life MCR Policies")
                if 'Product Code' in input_df:
                    product_code_options = input_df['Product Code'].dropna().unique().tolist()
                    ignored_product_codes = st.multiselect("Select Product Codes of Group to Ignore:", product_code_options)
            
                selected_policies = input_df[input_df['Product Code'].isin(ignored_product_codes)]
                input_df = input_df[~input_df['Product Code'].isin(ignored_product_codes)]
            
                if not selected_policies.empty:
                    st.markdown("<div class='frame'>", unsafe_allow_html=True)
                    st.subheader("Selected Policies (Ignored Product Codes)")
                    st.dataframe(selected_policies)
                
                # Download selected policies
                buffer = BytesIO()
                selected_policies.to_excel(buffer, index=False)
                buffer.seek(0)
                st.download_button(
                    label="Download Group MCR Policies",
                    data=buffer,
                    file_name="selected_policies.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                st.markdown("</div>", unsafe_allow_html=True)

                
                # Step 5: Ignore Policies by Commencement Date and Preview Ignored Policies
                st.subheader("Step 5: Ignore Policies by Commencement Date")
                st.write("In Step 5, we will filter out policies based on their commencement date. If the commencement date is greater than the valuation date, we will remove those policies from the valuation.")
                if 'Policy Start Date' in input_df:
                    input_df['Policy Start Date'] = pd.to_datetime(input_df['Policy Start Date'], errors='coerce')
                    ignored_policies = input_df[input_df['Policy Start Date'] > pd.to_datetime(valuation_date)]
                    input_df = input_df[input_df['Policy Start Date'] <= pd.to_datetime(valuation_date)]
    
                if not ignored_policies.empty:
                    st.markdown("<div class='frame'>", unsafe_allow_html=True)
                    st.subheader("Ignored Policies (Commencement Date After Valuation Date)")
                    st.dataframe(ignored_policies)
        
                # Download ignored policies
                buffer = BytesIO()
                ignored_policies.to_excel(buffer, index=False)
                buffer.seek(0)
                st.download_button(
                    label="Download Ignored Policies",
                    data=buffer,
                    file_name="ignored_policies.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                st.markdown("</div>", unsafe_allow_html=True)

                # Step 6: Ignore Policies by Maturity Date and Preview Ignored Policies

                # Step 6: Ignore Policies by Maturity Date and Preview Ignored Policies
                st.subheader("Step 6: Ignore Policies by Maturity Date")

                if 'Policy Start Date' in input_df and 'Policy Term (Months)' in input_df:
                    def convert_to_date(value):
                        """Converts different date formats into a valid datetime."""
                        try:
                            if isinstance(value, (int, float)) and value > 30000:  # Likely an Excel date serial number
                                return datetime(1899, 12, 30) + timedelta(days=value)
                            
                            # Try parsing standard datetime formats
                            parsed_date = pd.to_datetime(value, errors='coerce', dayfirst=True)
                            if pd.notna(parsed_date):
                                return parsed_date
                            
                            # If still invalid, return NaT
                            return pd.NaT
                        except:
                            return pd.NaT

                    # Convert Policy Start Date
                    input_df['Policy Start Date'] = input_df['Policy Start Date'].apply(convert_to_date)
                    input_df['Policy Term (Months)'] = pd.to_numeric(input_df['Policy Term (Months)'], errors='coerce')

                    # Correct Maturity Date Calculation: Year is adjusted by quotient, Month by remainder, Fractional Months to Days
                    def calculate_maturity(row):
                        if pd.isna(row['Policy Start Date']) or pd.isna(row['Policy Term (Months)']) or row['Policy Term (Months)'] == 0:
                            return "Error"
                        
                        # Split into integer and fractional parts
                        total_months = row['Policy Term (Months)']
                        years = int(total_months // 12)  # Quotient for years
                        months = int(total_months % 12)  # Remainder for months
                        
                        # Handle fractional months (convert to approximate days)
                        fractional_month = total_months % 1  # Extract decimal part
                        days = int(fractional_month * 30)  # Convert fractional month to days (approximation)

                        # Add years and months to the Policy Start Date
                        maturity_date = row['Policy Start Date'] + pd.DateOffset(years=years, months=months, days=days)
                        return maturity_date

                    input_df['Maturity Date'] = input_df.apply(calculate_maturity, axis=1)
                    
                    # Convert only valid maturity dates to datetime for comparison, set "Error" values to NaT
                    input_df['Maturity Date'] = pd.to_datetime(input_df['Maturity Date'], errors='coerce')
                    
                    # Filter ignored policies (only those with valid maturity dates)
                    ignored_maturity_policies = input_df[input_df['Maturity Date'].notna() & (input_df['Maturity Date'] <= pd.to_datetime(valuation_date))]
                    error_maturity_policies = input_df[input_df['Maturity Date'].isna()]  # Policies where Maturity Date is "Error"
                    input_df = input_df[input_df['Maturity Date'].isna() | (input_df['Maturity Date'] > pd.to_datetime(valuation_date))]

                # Preview and download ignored policies
                if not ignored_maturity_policies.empty:
                    st.markdown("<div class='frame'>", unsafe_allow_html=True)
                    st.subheader("Ignored Policies (Maturity Date Less Than or Equal to Valuation Date)")
                    st.dataframe(ignored_maturity_policies)

                    buffer = BytesIO()
                    ignored_maturity_policies.to_excel(buffer, index=False)
                    buffer.seek(0)
                    st.download_button(
                        label="Download Ignored Maturity Policies",
                        data=buffer,
                        file_name="ignored_maturity_policies.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

                # Preview and download error policies
                if not error_maturity_policies.empty:
                    st.markdown("<div class='frame'>", unsafe_allow_html=True)
                    st.subheader("Error Value Policies (Maturity Date Calculation Failed)")
                    st.dataframe(error_maturity_policies)

                    buffer = BytesIO()
                    error_maturity_policies.to_excel(buffer, index=False)
                    buffer.seek(0)
                    st.download_button(
                        label="Download Error Value Policies",
                        data=buffer,
                        file_name="error_maturity_policies.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                    st.markdown("</div>", unsafe_allow_html=True)






                
                
                # Step 7: Filter Data by Policy Status
                st.subheader("Step 7: Filter Data by Policy Status")
                policy_status_options = input_df['Policy Status'].dropna().unique().tolist() if 'Policy Status' in input_df else []
                selected_status = st.multiselect("Select Policy Status to Include:", policy_status_options)

                if selected_status:
                    filtered_df = input_df[input_df['Policy Status'].isin(selected_status)]
                    st.subheader("Status Wise Filtered Data")
                    st.write(f"Total Records Selected for MP File Conversion: {len(filtered_df)}")
                    st.dataframe(filtered_df)
                    
                # Step 8: Generate Output Fields
                    st.subheader("Step 8: Generate Output Fields")
                    
                    def process_data(df):
                        output_data = pd.DataFrame(index=df.index)
                        #output_data = pd.DataFrame()
                        
                        # 1. SPCODE (Static Value)
                        output_data['SPCODE'] = 1
                        output_data['SPCODE'] = output_data['SPCODE'].astype(int)

                        # 2. PROPHET_CODE (Derived from Plan Code)
                        def get_prophet_code(plan_code):
                            if str(plan_code).startswith("PLAN07"):
                                return "C_07MRP"
                            elif str(plan_code).startswith("PLAN11"):
                                return "C_11MICRO"
                            elif str(plan_code).startswith("PLAN25"):
                                return "C_25MRPTAKAFUL"
                            return "Check"
                        
                        output_data['PROPHET_CODE'] = df['Plan Code'].apply(get_prophet_code)
                        
                        # 3. PolNo (Integer or Text Based on Original Data Type)
                        def convert_policy_number(value):
                            try:
                                return int(value) if value.replace(".", "", 1).isdigit() else value
                            except:
                                return value
                        output_data['PolNo'] = df['Policy Number'].apply(convert_policy_number)
                        
                        # 4. PLAN_NO (Derived from Plan Code as Integer)
                        def get_plan_no(plan_code):
                            if str(plan_code).startswith("PLAN07"):
                                return 7
                            elif str(plan_code).startswith("PLAN11"):
                                return 11
                            elif str(plan_code).startswith("PLAN25"):
                                return 25
                            return None
                        
                        output_data['PLAN_NO'] = df['Plan Code'].apply(get_plan_no)
                        
                        # 5. COMM_DAT (Formatted as 8-digit YYYYMMDD as Integer from Policy Start Date)
                        def convert_date_to_8_digits(date):
                            try:
                                date_obj = pd.to_datetime(date, errors='coerce')
                                return int(f"{date_obj.year:04d}{date_obj.month:02d}{date_obj.day:02d}")
                            except:
                                return 0
                        output_data['COMM_DAT'] = df['Policy Start Date'].apply(convert_date_to_8_digits)
                        
                        # 6. NEXT_DUE_DATE (Static Value)
                        output_data['NEXT_DUE_DATE'] = 0
                        
                        # 7. BIRTH_DAT (Formatted as 8-digit YYYYMMDD as Integer from DOB (Life 1))
                        output_data['BIRTH_DAT'] = df['DOB (Life 1)'].apply(convert_date_to_8_digits)
                        
                        # 8. SEX (Mapped from Gender (Life 1))
                        def map_gender(gender):
                            gender = str(gender).strip().lower()
                            if gender in ["male", "m"]:
                                return 0
                            elif gender in ["female", "f"]:
                                return 1
                            return "Error"
                        output_data['SEX'] = df['Gender (Life 1)'].apply(map_gender)


                        # 9. BIRTH_DAT2 (Formatted as 8-digit YYYYMMDD as Integer from DOB (Life 2))
                        output_data['BIRTH_DAT2'] = df['DOB (Life 2)'].apply(convert_date_to_8_digits)
                        
                        # 10. SEX2 (Mapped from Gender (Life 2))
                        output_data['SEX2'] = df['Gender (Life 2)'].apply(map_gender)

                        # 11. POL_TERM_Y (Policy Term in Years)
                        output_data['POL_TERM_Y'] = df['Policy Term (Months)'].apply(lambda x: int(x) / 12 if str(x).isdigit() else 0)
                        
                        # 12. PREM_FREQ (Static Value)
                        output_data['PREM_FREQ'] = 0

                        # 13. ANNUAL_PREM (Static Value)
                        output_data['ANNUAL_PREM'] = 0


                        # 14. SINGLE_PREM (Extracted from Single Premium as Number)
                        def convert_to_number(value):
                            try:
                                return float(value) if str(value).replace(".", "", 1).isdigit() else 0
                            except:
                                return 0
                        output_data['SINGLE_PREM'] = df['Single Premium'].apply(convert_to_number)
                        

                        # 15. SUM_ASSURED
                        output_data['SUM_ASSURED'] = 0

                        # 16. INIT_DECB_IF
                        output_data['INIT_DECB_IF'] = 0

                        # 17. LOAN_AMT_1
                        output_data['LOAN_AMT_1'] = df['Loan Amount (Death Benefit) -Life 1'].apply(convert_to_number)

                        # 18. LOAN_AMT_2
                        output_data['LOAN_AMT_2'] = 0

                        # 19. LOAN_AMT_3
                        output_data['LOAN_AMT_3'] = 0

                        # 20. LOAN_INT_1 Calculation
                        def calculate_loan_int(row):
                            try:
                                if str(row['Interest Type']).strip().lower() == "fixed":
                                    return float(row['Fixed Interest']) if str(row['Fixed Interest']).replace(".", "", 1).isdigit() else 0
                                elif str(row['Interest Type']).strip().lower() == "variable":
                                    current_awplr = float(row['Current AWPLR']) if str(row['Current AWPLR']).replace(".", "", 1).isdigit() else 0
                                    additional_awplr = float(row['Additional AWPLR']) if str(row['Additional AWPLR']).replace(".", "", 1).isdigit() else 0
                                    return current_awplr + additional_awplr
                                else:
                                    return 0
                            except:
                                return 0
                        
                        output_data['LOAN_INT_1'] = df.apply(calculate_loan_int, axis=1)

                     
                        # 21. LOAN_INT_2
                        output_data['LOAN_INT_2'] = 0

                        # 22. LOAN_INT_3
                        output_data['LOAN_INT_3'] = 0

                        # 23. TPD_DECLINE Calculation
                        def calculate_tpd_decline(value):
                            value = str(value).strip().lower()
                            if value == "yes":
                                return "N"
                            elif value == "no":
                                return "Y"
                            else:
                                return "Error"
                        
                        output_data['TPD_DECLINE'] = df['TPD Option  - Life 1'].apply(calculate_tpd_decline)

                        # 24. TPD_DECLINE2 Calculation
                        def calculate_tpd_decline2(value):
                            value = str(value).strip().lower()
                            if value == "yes":
                                return "N"
                            elif value == "no":
                                return "Y"
                            else:
                                return 0
                        
                        output_data['TPD_DECLINE2'] = df['TPD Option  - Life 2'].apply(calculate_tpd_decline2)
                        
                        # 25. MAT_BEN_PP
                        output_data['MAT_BEN_PP'] = 0

                        # 26. CURR_FUND_BAL
                        output_data['CURR_FUND_BAL'] = 0

                        # 27. SUM_ASSD_HB
                        output_data['SUM_ASSD_HB'] = 0

                        # 28. ANN_ANNUITY
                        output_data['ANN_ANNUITY'] = 0

                        # 29. DEFER_PER_Y
                        output_data['DEFER_PER_Y'] = 0

                        # 30. RPR_COMPANY Mapping (Using Preloaded Table)
                        def map_ri_company(polno):
                            return ri_company_dict.get(str(polno), "MunichRe")
                        
                        output_data['RPR_COMPANY'] = df['Policy Number'].apply(map_ri_company)
                        
                        # 31. SERIES_NO
                        output_data['SERIES_NO'] = 0

                        # 32. PREM_TERM_Y
                        output_data['PREM_TERM_Y'] = 0

                        # 33. GRACE_START_ONE
                        output_data['GRACE_START_ONE'] = 0

                        # 34. GRACE_PERIOD_ONE
                        output_data['GRACE_PERIOD_ONE'] = 0

                        # 35. DOV_INDICATOR Calculation
                        def generate_dov_indicator(date):
                            return f"M{date.month}_{date.year}"
                            #return f"M{date.month:02d}_{date.year}"
                    
                        output_data['DOV_INDICATOR'] = generate_dov_indicator(valuation_date)

                        # 36. GRACE_START_TWO
                        output_data['GRACE_START_TWO'] = 0

                        # 37. GRACE_PERIOD_TWO
                        output_data['GRACE_PERIOD_TWO'] = 0

                        # 38. STUDY_GUARD_TYPE
                        output_data['STUDY_GUARD_TYPE'] = 0

                        # 39. MRP_LOAN_TYPE Mapping (Using Preloaded Table)
                        def map_loan(Product_CODE):
                            return mrp_loan_type_dict.get(str(Product_CODE), "Error")


                        output_data['LoanType'] = df['Product Code'].apply(map_loan)       

                        # 40. GRACE_START_THREE
                        output_data['GRACE_START_THREE'] = 0                        

                        # 41. GRACE_PERIOD_THREE
                        output_data['GRACE_PERIOD_THREE'] = 0 

                        # 42. MCR_LOAN_TYPE
                        output_data['MCR_LOAN_TYPE'] = 0 

                        # 43. CHANNEL_CODE
                        output_data['CHANNEL_CODE'] = "Partnership"

                        # Ensure SPCODE remains 1 and properly formatted as integer
                        #output_data['SPCODE'] = output_data['SPCODE'].astype(int)

                        # Debugging Output (Optional - You can remove this after verification)
                        #st.write("SPCODE Column Unique Values:", output_data['SPCODE'].unique())

                        return output_data
            
                    
                    output_df = process_data(filtered_df)
                    
                    # Display Output Data
                    st.subheader("Generated Output Preview")
                    st.dataframe(output_df)
                    
                    # Download Output Data
                    buffer = BytesIO()
                    output_df.to_excel(buffer, index=False)
                    buffer.seek(0)
                    
                    st.download_button(
                        label="Download Generated Output",
                        data=buffer,
                        file_name="generated_output.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
            except Exception as e:
                st.error(f"Error processing data: {e}")
    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload a file to proceed.")


# Load and Display Video at the End
video_path = "IMAGE/Thank.mp4"

if os.path.exists(video_path):
    # Custom CSS for resizing the video
    st.markdown(
        """
        <style>
        video {
            max-width: 600px;
            height: auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.video(video_path, start_time=0)
else:
    st.warning("Video file not found. Please check the file name and path.")



# Footer with creator info
st.markdown("""
    <div class='footer'>
        ✨ Automated By <span style='font-style:italic;'>Nitha</span> ✨
    </div>
""", unsafe_allow_html=True)