import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import os
import json
from dotenv import load_dotenv
from helper import configure_genai, get_gemini_response, extract_pdf_text, prepare_prompt

def init_session_state():
    """Initialize session state variables."""
    if 'processing' not in st.session_state:
        st.session_state.processing = False

def get_api_key():
    """Get API key from Streamlit secrets or local .env file"""
    try:
        # First, try to get from Streamlit secrets (for production)
        return st.secrets["GOOGLE_API_KEY"]
    except:
        # Fallback to local .env file (for development)
        load_dotenv()
        return os.getenv("GOOGLE_API_KEY")

def main():
    # Initialize session state
    init_session_state()
    
    # Get API key using the new function
    api_key = get_api_key()
    if not api_key:
        st.error("API Key not found. Please check your configuration.")
        return
        
    try:
        configure_genai(api_key)
    except Exception as e:
        st.error(f"Failed to configure API: {str(e)}")
        return

    # Sidebar
    with st.sidebar:
        st.title("🏡 ATS Hub")
        st.subheader("About")
        st.write("""
        ATS Hub helps you:
        - Assess the alignment between the resume and job description.
        - Detect missing keywords.
        - Receive tailored suggestions for improvement.
        """)

    # Main content
    st.title("📄 ATS Hub Resume Analyzer")
    st.subheader("Optimize Your Resume for ATS")
    
    # Input sections with validation
    jd = st.text_area(
        "Job Description",
        placeholder="Paste the job description here...",
        help="Copy & Paste the complete job description for accurate analysis"
    )
    
    uploaded_file = st.file_uploader(
        "Resume (PDF)",
        type="pdf",
        help="Upload your resume in PDF format"
    )

    # Process button with loading state
    if st.button("Analyze Resume", disabled=st.session_state.processing):
        if not jd:
            st.warning("Please provide a job description.")
            return
            
        if not uploaded_file:
            st.warning("Please upload a resume in PDF format.")
            return
            
        st.session_state.processing = True
        
        try:
            with st.spinner("📊 Analyzing your resume..."):
                # Extract text from PDF
                resume_text = extract_pdf_text(uploaded_file)
                
                # Prepare prompt
                input_prompt = prepare_prompt(resume_text, jd)
                
                # Get and parse response
                response = get_gemini_response(input_prompt)
                
                # Add error handling for JSON parsing
                try:
                    response_json = json.loads(response)
                except json.JSONDecodeError as e:
                    st.error("Error parsing response. Please try again.")
                    return
                
                # Display results
                st.success("✨ Analysis Complete!")
                
                # Match percentage
                match_percentage = response_json.get("JD Match", "N/A")
                st.metric("Match Score", match_percentage)
                
                # Missing keywords
                st.subheader("Missing Keywords")
                missing_keywords = response_json.get("MissingKeywords", [])
                if missing_keywords:
                    st.write(", ".join(missing_keywords))
                else:
                    st.write("No critical missing keywords found!")
                
                # Profile summary
                st.subheader("Profile Summary")
                st.write(response_json.get("Profile Summary", "No summary available"))
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            
        finally:
            st.session_state.processing = False

if __name__ == "__main__":
    main()
