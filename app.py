# app.py — Streamlit front-end (imports from audit_lib)
import io, pathlib, traceback, sys, os, pkgutil
import streamlit as st

st.set_page_config(page_title="Numerals & Units Audit", page_icon="📏", layout="wide")
st.title("📏 Numerals & Units Audit")

# ---- Diagnostics (optional) ----
with st.expander("Environment diagnostics", expanded=False):
    st.write("**Python**", sys.version)
    st.write("**CWD**", os.getcwd())
    st.write("**Files in CWD**", os.listdir("."))
    st.write("**Top installed packages**", [m.name for m in list(pkgutil.iter_modules())][:50])

# ---- Import library (renamed to avoid collisions) ----
try:
    from audit_lib import audit_files
except Exception:
    st.error("Failed to import `audit_lib.py`. See details below.")
    st.code(traceback.format_exc(), language="text")
    st.stop()

with st.sidebar:
    st.markdown("**Supported file types**")
    st.markdown("- TXT / MD\n- DOCX\n- PPTX\n- XLSX / CSV / TSV\n- XLIFF / XLF / MXLIFF / SDLXLIFF")
    st.caption("Tip: Upload an XLIFF as source (reads <source>) and another XLIFF as target (reads <target>).")

# Stable, run-unique key prefix to avoid DuplicateElementId
if "run_id" not in st.session_state:
    import uuid
    st.session_state["run_id"] = str(uuid.uuid4())[:8]
KP = f"audit_{st.session_state['run_id']}_"

# ---- Inputs ----
src_file = st.file_uploader(
    "Upload Source File",
    type=["txt","md","docx","pptx","xlsx","csv","tsv","xliff","xlf","mxliff","sdlxliff"],
    key=KP + "uploader_source",
)
tgt_file = st.file_uploader(
    "Upload Target File",
    type=["txt","md","docx","pptx","xlsx","csv","tsv","xliff","xlf","mxliff","sdlxliff"],
    key=KP + "uploader_target",
)

if src_file and tgt_file:
    st.success(f"Ready: **{src_file.name}** → **{tgt_file.name}**", icon="✅")
else:
    st.info("Upload both source and target to enable the button.", icon="ℹ️")

run = st.button("Run Audit", type="primary", disabled=not (src_file and tgt_file), key=KP + "btn_run")

# ---- Run ----
if run:
    try:
        st.info("Saving uploads…", icon="💾")
        src_ext = src_file.name.split(".")[-1].lower() if "." in src_file.name else "bin"
        tgt_ext = tgt_file.name.split(".")[-1].lower() if "." in tgt_file.name else "bin"
        src_path = pathlib.Path(f"{KP}source_upload.{src_ext}")
        tgt_path = pathlib.Path(f"{KP}target_upload.{tgt_ext}")

        with open(src_path, "wb") as f:
            f.write(src_file.getbuffer())
        with open(tgt_path, "wb") as f:
            f.write(tgt_file.getbuffer())

        st.success(f"Saved: {src_path.name} • {tgt_path.name}", icon="✅")
        st.info("Running audit…", icon="🔎")

        result = audit_files(src_path, tgt_path)

        st.success("Audit complete.", icon="✅")

        # Summary
        st.subheader("Summary", anchor=False)
        st.dataframe(result["Summary"], use_container_width=True, key=KP + "df_summary")

        # Download Excel
        import pandas as pd
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            for name, df in result.items():
                df.to_excel(writer, sheet_name=name[:31], index=False)
        buf.seek(0)
        st.download_button(
            "⬇️ Download Excel Report",
            data=buf,
            file_name="numbers_units_audit.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=KP + "download_xlsx",
        )

        # Details
        with st.expander("Missing pairs in target", expanded=False):
            st.dataframe(result["Missing_in_Target"], use_container_width=True, key=KP + "df_missing")
        with st.expander("Extra pairs in target", expanded=False):
            st.dataframe(result["Extra_in_Target"], use_container_width=True, key=KP + "df_extra")
        with st.expander("Value changed", expanded=False):
            st.dataframe(result["Value_Changed"], use_container_width=True, key=KP + "df_changed")
        with st.expander("Pure numbers — Missing / Extra", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.caption("Missing kinds")
                st.dataframe(result["PureNums_Missing"], use_container_width=True, key=KP + "df_pure_missing")
            with c2:
                st.caption("Extra kinds")
                st.dataframe(result["PureNums_Extra"], use_container_width=True, key=KP + "df_pure_extra")

    except Exception:
        st.error("An error occurred during the audit. Details below.")
        st.code(traceback.format_exc(), language="text")
