"""Q-Shield inventory workspace: import, browse, edit, and export assets."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from qshield.database import Database
from qshield.detection import analyze_asset
from qshield.inventory import export_assets_csv, get_assets_dataframe, import_assets_to_db, load_demo_assets
from qshield.models import (
    AssetType,
    BusinessCriticality,
    CryptoPurpose,
    CryptographicAsset,
    DataSensitivity,
    Environment,
    MigrationStatus,
)
from qshield.risk_engine import compute_risk_score
from qshield.ui import inject_styles, render_flow_map, render_page_header, render_sidebar, section_title
from qshield.validation import MAX_UPLOAD_MB, sanitize_text, validate_dataframe, validate_file_upload, validate_single_asset


st.set_page_config(page_title="Inventory — Q-Shield", page_icon="▦", layout="wide")
inject_styles()
render_sidebar("Inventory")


@st.cache_resource
def get_database() -> Database:
    return Database()


db = get_database()


def assess_assets(assets) -> None:
    for asset in assets:
        data = asset.to_dict() if hasattr(asset, "to_dict") else asset
        finding = analyze_asset(data)
        score = compute_risk_score(data, finding)
        db.save_assessment(data["asset_id"], finding.to_dict(), score.to_dict())


render_page_header(
    "INVENTORY",
    "Build a trustworthy cryptographic inventory",
    "Import sanitized data, validate the fields, then keep ownership and migration state current so every finding has accountable context.",
)
render_flow_map([
    ("N1", "Observe", "Inventory the cryptographic estate."),
    ("N2", "Detect", "Classify vulnerable and PQC usage."),
    ("N3", "Prioritize", "Explain what needs attention first."),
    ("N4", "Migrate", "Move assets through a verified roadmap."),
])

top_col1, top_col2, top_col3 = st.columns([1, 1, 2.5])
with top_col1:
    if st.button("＋ Load demo data", use_container_width=True):
        demo = load_demo_assets()
        count = import_assets_to_db(db, demo, source="demo_dataset")
        assess_assets(demo)
        db.log_activity("Assessment completed", f"Assessed {count} demo assets", count)
        st.success(f"Loaded and assessed {count} assets")
        st.rerun()
with top_col2:
    csv_data = export_assets_csv(db) if db.asset_count() else ""
    st.download_button(
        "⇩ Export inventory",
        csv_data,
        file_name="qshield_inventory.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=not bool(csv_data),
    )
with top_col3:
    st.caption("Import flow: upload → validate → review → assess. Existing data is never replaced without an explicit choice.")

section_title("Import inventory", "CSV and JSON uploads are validated before anything is written to the local database.")
with st.expander("Upload CSV or JSON", expanded=db.asset_count() == 0):
    st.markdown(f"Maximum upload size: **{MAX_UPLOAD_MB} MB** · Required fields: asset ID, name, type, algorithm")
    st.warning("Use synthetic or sanitized data in a public demo. Production inventories may contain sensitive information.")
    replace_existing = st.checkbox("Replace existing inventory before import", value=False)
    uploaded = st.file_uploader("Choose a CSV or JSON file", type=["csv", "json"])

    if uploaded:
        valid, message, dataframe = validate_file_upload(uploaded.read(), uploaded.name)
        if not valid:
            st.error(message)
        else:
            st.success(message)
            valid_assets, errors = validate_dataframe(dataframe)
            if errors:
                st.warning(f"{len(errors)} validation issue(s) need attention before import.")
                st.dataframe(pd.DataFrame(errors), use_container_width=True, hide_index=True, height=180)
            if valid_assets:
                st.info(f"{len(valid_assets)} valid assets are ready to import.")
                if replace_existing:
                    st.warning(f"Importing will delete the current {db.asset_count()} assets first.")
                if st.button("Import and assess", type="primary"):
                    if replace_existing:
                        db.delete_all_assets()
                    count = import_assets_to_db(db, valid_assets, source=uploaded.name)
                    progress = st.progress(0, text="Assessing imported assets...")
                    for index, asset in enumerate(valid_assets, start=1):
                        data = asset.to_dict()
                        finding = analyze_asset(data)
                        score = compute_risk_score(data, finding)
                        db.save_assessment(data["asset_id"], finding.to_dict(), score.to_dict())
                        progress.progress(index / len(valid_assets), text=f"Assessing {data['asset_id']}...")
                    progress.empty()
                    db.log_activity("Assessment completed", f"Assessed {count} imported assets", count)
                    st.success(f"Imported and assessed {count} assets")
                    st.rerun()
            elif not errors:
                st.warning("No valid assets were found in the upload.")

df = get_assets_dataframe(db)
if df.empty:
    st.info("No assets in inventory yet. Load demo data or upload a sanitized dataset above.")
    st.stop()

section_title("Inventory workspace", f"{len(df)} assets · filter first, then open the record you need to edit or review.")
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
with filter_col1:
    search = st.text_input("Search", placeholder="Name, ID, algorithm, owner")
with filter_col2:
    type_filter = st.multiselect("Asset type", sorted(df["asset_type"].unique()))
with filter_col3:
    algo_filter = st.multiselect("Algorithm", sorted(df["cryptographic_algorithm"].unique()))
with filter_col4:
    status_filter = st.multiselect("Migration status", sorted(df["migration_status"].unique()))

filter_col5, filter_col6, filter_col7 = st.columns(3)
with filter_col5:
    env_filter = st.multiselect("Environment", sorted(df["environment"].unique()))
with filter_col6:
    sens_filter = st.multiselect("Data sensitivity", sorted(df["data_sensitivity"].unique()))
with filter_col7:
    crit_filter = st.multiselect("Business criticality", sorted(df["business_criticality"].unique()))

filtered = df.copy()
if search:
    filtered = filtered[filtered.apply(lambda row: search.lower() in " ".join(str(value).lower() for value in row.values), axis=1)]
if type_filter:
    filtered = filtered[filtered["asset_type"].isin(type_filter)]
if algo_filter:
    filtered = filtered[filtered["cryptographic_algorithm"].isin(algo_filter)]
if status_filter:
    filtered = filtered[filtered["migration_status"].isin(status_filter)]
if env_filter:
    filtered = filtered[filtered["environment"].isin(env_filter)]
if sens_filter:
    filtered = filtered[filtered["data_sensitivity"].isin(sens_filter)]
if crit_filter:
    filtered = filtered[filtered["business_criticality"].isin(crit_filter)]

st.caption(f"Showing {len(filtered)} of {len(df)} assets")
display_cols = [
    "asset_id", "asset_name", "asset_type", "cryptographic_algorithm",
    "cryptographic_purpose", "owner", "environment", "business_criticality",
    "internet_exposed", "migration_status",
]
display = filtered[[column for column in display_cols if column in filtered.columns]].rename(
    columns={
        "asset_id": "Asset ID",
        "asset_name": "Asset",
        "asset_type": "Type",
        "cryptographic_algorithm": "Algorithm",
        "cryptographic_purpose": "Purpose",
        "business_criticality": "Criticality",
        "internet_exposed": "Internet",
        "migration_status": "Migration",
    }
)
st.dataframe(display, use_container_width=True, hide_index=True, height=390)

section_title("Manage records", "Editing an asset automatically recalculates its finding and risk score.")
tab_add, tab_edit, tab_delete = st.tabs(["Add asset", "Edit asset", "Delete asset"])

with tab_add:
    with st.form("add_asset_form"):
        st.markdown("**1 · Identify the asset**")
        id_col, name_col, type_col = st.columns(3)
        with id_col:
            new_id = st.text_input("Asset ID*", placeholder="ASSET-016")
        with name_col:
            new_name = st.text_input("Asset name*", placeholder="Payments API")
        with type_col:
            new_type = st.selectbox("Asset type*", [entry.value for entry in AssetType])

        st.markdown("**2 · Describe the cryptography**")
        crypto_col1, crypto_col2, crypto_col3 = st.columns(3)
        with crypto_col1:
            new_algo = st.text_input("Algorithm*", placeholder="RSA-2048")
            new_purpose = st.selectbox("Purpose", [entry.value for entry in CryptoPurpose])
        with crypto_col2:
            new_protocol = st.text_input("Protocol", placeholder="TLS 1.3")
            new_cert = st.text_input("Certificate expiry", placeholder="2027-12-31")
        with crypto_col3:
            new_env = st.selectbox("Environment", [entry.value for entry in Environment])
            new_owner = st.text_input("Owner", placeholder="Payments Platform")

        st.markdown("**3 · Capture business impact and migration context**")
        impact_col1, impact_col2, impact_col3 = st.columns(3)
        with impact_col1:
            new_sens = st.selectbox("Data sensitivity", [entry.value for entry in DataSensitivity])
            new_ret = st.number_input("Retention (years)", 0, 100, 5)
        with impact_col2:
            new_crit = st.selectbox("Business criticality", [entry.value for entry in BusinessCriticality])
            new_deps = st.number_input("Dependencies", 0, 100, 0)
        with impact_col3:
            new_exposed = st.checkbox("Internet exposed")
            new_status = st.selectbox("Migration status", [entry.value for entry in MigrationStatus])
        new_domain = st.text_input("Business domain", placeholder="Payments")
        new_notes = st.text_area("Notes", height=80)

        if st.form_submit_button("Add and assess asset", type="primary"):
            data = {
                "asset_id": sanitize_text(new_id), "asset_name": sanitize_text(new_name),
                "asset_type": new_type, "business_domain": sanitize_text(new_domain),
                "environment": new_env, "owner": sanitize_text(new_owner),
                "cryptographic_algorithm": sanitize_text(new_algo), "cryptographic_purpose": new_purpose,
                "protocol": sanitize_text(new_protocol), "certificate_expiry": sanitize_text(new_cert),
                "data_sensitivity": new_sens, "data_retention_years": new_ret,
                "business_criticality": new_crit, "internet_exposed": new_exposed,
                "dependency_count": new_deps, "migration_status": new_status,
                "notes": sanitize_text(new_notes),
            }
            valid, issues = validate_single_asset(data)
            if not valid:
                for issue in issues:
                    st.error(issue)
            else:
                db.upsert_asset(CryptographicAsset.from_dict(data))
                assess_assets([data])
                db.log_activity("Added asset", f"{data['asset_id']}: {data['asset_name']}")
                st.success(f"Added and assessed {data['asset_id']}")
                st.rerun()

with tab_edit:
    asset_ids = filtered["asset_id"].tolist()
    if not asset_ids:
        st.info("No filtered assets are available to edit.")
    else:
        edit_id = st.selectbox("Select asset", asset_ids, format_func=lambda asset_id: f"{asset_id} — {filtered[filtered['asset_id'] == asset_id]['asset_name'].iloc[0]}")
        existing = db.get_asset(edit_id)
        if existing:
            with st.form("edit_asset_form"):
                edit_col1, edit_col2 = st.columns(2)
                with edit_col1:
                    ed_name = st.text_input("Name", value=existing.get("asset_name", ""))
                    ed_algo = st.text_input("Algorithm", value=existing.get("cryptographic_algorithm", ""))
                    ed_sens = st.selectbox("Data sensitivity", [entry.value for entry in DataSensitivity], index=[entry.value for entry in DataSensitivity].index(existing.get("data_sensitivity", "Internal")))
                    ed_crit = st.selectbox("Business criticality", [entry.value for entry in BusinessCriticality], index=[entry.value for entry in BusinessCriticality].index(existing.get("business_criticality", "Medium")))
                with edit_col2:
                    statuses = [entry.value for entry in MigrationStatus]
                    current_status = existing.get("migration_status", "Not Started")
                    ed_status = st.selectbox("Migration status", statuses, index=statuses.index(current_status) if current_status in statuses else 0)
                    ed_notes = st.text_area("Notes", value=existing.get("notes", ""))
                    ed_exposed = st.checkbox("Internet exposed", value=bool(existing.get("internet_exposed")))
                    ed_deps = st.number_input("Dependencies", 0, 100, int(existing.get("dependency_count", 0)))
                if st.form_submit_button("Save and reassess", type="primary"):
                    existing.update({
                        "asset_name": sanitize_text(ed_name), "cryptographic_algorithm": sanitize_text(ed_algo),
                        "data_sensitivity": ed_sens, "business_criticality": ed_crit, "migration_status": ed_status,
                        "notes": sanitize_text(ed_notes), "internet_exposed": ed_exposed, "dependency_count": ed_deps,
                    })
                    db.upsert_asset(CryptographicAsset.from_dict(existing))
                    assess_assets([existing])
                    db.log_activity("Updated asset", edit_id)
                    st.success(f"Updated and reassessed {edit_id}")
                    st.rerun()

with tab_delete:
    delete_ids = filtered["asset_id"].tolist()
    if not delete_ids:
        st.info("No filtered assets are available to delete.")
    else:
        delete_id = st.selectbox("Select asset to delete", delete_ids, key="delete_asset_select")
        st.warning(f"Deleting **{delete_id}** also deletes its assessment result.")
        if st.button("Delete selected asset", type="primary"):
            db.delete_asset(delete_id)
            db.log_activity("Deleted asset", delete_id)
            st.success(f"Deleted {delete_id}")
            st.rerun()

with st.expander("Data management", expanded=False):
    st.caption(f"{db.asset_count()} assets are stored locally.")
    if st.button("Clear all inventory", type="secondary"):
        st.session_state["confirm_clear_inventory"] = True
    if st.session_state.get("confirm_clear_inventory"):
        st.warning("This permanently deletes every asset and assessment in the local database.")
        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            if st.button("Confirm clear inventory", type="primary"):
                deleted = db.delete_all_assets()
                db.log_activity("Cleared inventory", f"Deleted {deleted} assets")
                st.session_state["confirm_clear_inventory"] = False
                st.success(f"Cleared {deleted} assets")
                st.rerun()
        with cancel_col:
            if st.button("Cancel clear"):
                st.session_state["confirm_clear_inventory"] = False
                st.rerun()
