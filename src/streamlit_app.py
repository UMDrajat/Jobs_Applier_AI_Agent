import base64
from pathlib import Path
import streamlit as st

from src.libs.resume_and_cover_builder.style_manager import StyleManager
from src.libs.resume_and_cover_builder.resume_generator import ResumeGenerator
from src.libs.resume_and_cover_builder.resume_facade import ResumeFacade
from src.resume_schemas.resume import Resume
from src.utils.chrome_utils import init_browser


def generate_document(action: str, api_key: str, resume_text: str, style: str, job_url: str | None) -> tuple[bytes, str]:
    style_manager = StyleManager()
    style_manager.set_selected_style(style)
    resume_generator = ResumeGenerator()
    resume_object = Resume(resume_text)
    driver = init_browser()
    resume_generator.set_resume_object(resume_object)
    facade = ResumeFacade(
        api_key=api_key,
        style_manager=style_manager,
        resume_generator=resume_generator,
        resume_object=resume_object,
        output_path=Path("streamlit_output"),
    )
    facade.set_driver(driver)

    if action == "Generate Resume":
        result_base64 = facade.create_resume_pdf()
        name = "resume_base"
    else:
        if not job_url:
            raise ValueError("Job URL is required for this action")
        facade.link_to_job(job_url)
        if action == "Generate Resume Tailored for Job Description":
            result_base64, name = facade.create_resume_pdf_job_tailored()
        else:
            result_base64, name = facade.create_cover_letter()
    pdf_bytes = base64.b64decode(result_base64)
    return pdf_bytes, name


def main():
    st.title("AIHawk Job Application Helper")
    api_key = st.text_input("LLM API Key", type="password")

    style_manager = StyleManager()
    styles = list(style_manager.get_styles().keys())
    if styles:
        style = st.selectbox("Select style", styles)
    else:
        st.warning("No styles available")
        style = ""

    action = st.selectbox(
        "Select action",
        [
            "Generate Resume",
            "Generate Resume Tailored for Job Description",
            "Generate Tailored Cover Letter for Job Description",
        ],
    )

    resume_file = st.file_uploader("Upload plain text resume", type=["txt", "yaml", "yml"])
    job_url = st.text_input("Job URL", "")

    if st.button("Generate"):
        if not api_key or resume_file is None or not style:
            st.error("Please provide API key, resume file and style")
        else:
            resume_text = resume_file.read().decode("utf-8")
            try:
                pdf_bytes, name = generate_document(action, api_key, resume_text, style, job_url)
                st.download_button("Download PDF", pdf_bytes, file_name=f"{name}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(str(e))


if __name__ == "__main__":
    main()
