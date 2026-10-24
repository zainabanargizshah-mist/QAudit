"""
Q-Shield — Asset Inventory Page

Manage cryptographic assets: upload, browse, filter, add, edit, delete, export.
"""

import streamlit as st
import pandas as pd
import io
import json

from qshield.database import Database
from qshield.inventory import (
    load_demo_assets, import_assets_to_db, get_assets_dataframe,
    export_assets_csv,
)
from qshield.validation import (
    validate_file_upload, validate_dataframe, validate_single_asset,
    sanitize_text, MAX_UPLOAD_MB,
)
from qshield.models import (
    ASSET_FIELDS, CryptographicAsset,
    AssetType, DataSensitivity, BusinessCriticality,
    MigrationStatus, Environment, CryptoPurpose,
)
from qshield.detection import analyze_asset
from qshield.risk_engine import compute_risk_score


st.set_page_config(
    page_title="Asset Inventory — Q-Shield",
    page_icon="📋",
    layout="wide",
)

# ── Shared CSS (minimal repeat for page) ─────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a1f36; }
    [data-testid="stSidebar"] * { color: #e0e4ef !important; }
    .demo-badge {
        display: inline-block; background-color: #f59e0b;
        color: #1a1f36 !important; padding: 3px 10px; border-radius: 4px;
        font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_database():
    return Database()

db = get_database()


# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ Q-Shield")
    st.markdown("*Quantum-Readiness Intelligence*")
    st.markdown("---")
    st.page_link("app.py", label="📊 Overview")
    st.page_link("pages/1_Asset_Inventory.py", label="📋 Asset Inventory")
    st.page_link("pages/2_Risk_Assessment.py", label="⚡ Risk Assessment")
    st.page_link("pages/3_Migration_Planner.py", label="🗺️ Migration Planner")
    st.page_link("pages/4_Reports.py", label="📄 Reports")
    st.page_link("pages/5_Methodology.py", label="📚 Methodology & Standards")


# ── Header ───────────────────────────────────────────────────────────
st.markdown("# 📋 Cryptographic Asset Inventory")
st.markdown("Manage your organization's cryptographic asset catalog.")

load_col, clear_col = st.columns([1, 1])
with load_col:
    if st.button("📥 Load Demo Data", type="primary", help="Load the bundled synthetic dataset into the inventory"):
        demo_assets = load_demo_assets()
        count = import_assets_to_db(db, demo_assets, source="demo_dataset")
        for asset in demo_assets:
            asset_data = asset.to_dict()
            finding = analyze_asset(asset_data)
            score = compute_risk_score(asset_data, finding)
            db.save_assessment(asset_data["asset_id"], finding.to_dict(), score.to_dict())
        db.log_activity("Assessment completed", f"Assessed {count} demo assets", count)
        st.success(f"✅ Loaded and assessed {count} demo assets.")
        st.rerun()

with clear_col:
    if db.asset_count() and st.button("🗑️ Clear Inventory", help="Remove saved assets and assessments"):
        st.session_state["confirm_clear_inventory"] = True

if st.session_state.get("confirm_clear_inventory"):
    st.warning("This removes all saved assets and their assessments. Uploaded files and demo data can be loaded again.")
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("Confirm Clear Inventory", type="primary"):
            db.delete_all_assets()
            db.log_activity("Cleared all assets")
            st.session_state["confirm_clear_inventory"] = False
            st.rerun()
    with cancel_col:
        if st.button("Cancel"):
            st.session_state["confirm_clear_inventory"] = False
            st.rerun()

# ── Upload Section ───────────────────────────────────────────────────
# ── Clear All Banner ─────────────────────────────────────────────────
current_count = db.asset_count()
if current_count > 0:
    clear_col1, clear_col2 = st.columns([4, 1])
    with clear_col1:
        st.info(f"📦 **{current_count} assets** currently in inventory. Clear all before uploading a fresh dataset.")
    with clear_col2:
        if st.button("🗑️ Clear All Inventory", type="primary", use_container_width=True):
            st.session_state["confirm_clear"] = True

    if st.session_state.get("confirm_clear"):
        st.warning("⚠️ This will permanently delete **all assets and assessments**. Are you sure?")
        conf_col1, conf_col2 = st.columns(2)
        with conf_col1:
            if st.button("✅ Yes, Clear Everything", type="primary", use_container_width=True):
                deleted = db.delete_all_assets()
                db.log_activity("Cleared inventory", f"Deleted {deleted} assets")
                st.session_state["confirm_clear"] = False
                st.success(f"✅ Cleared {deleted} assets. Upload your new inventory below.")
                st.rerun()
        with conf_col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state["confirm_clear"] = False
                st.rerun()

st.markdown("---")

with st.expander("📤 Upload Assets (CSV or JSON)", expanded=True):
    st.markdown(f"Upload a CSV or JSON file. Max size: {MAX_UPLOAD_MB} MB.")
    st.warning(
        "⚠️ **Do not upload confidential production inventories to a public demo.** "
        "Use synthetic or sanitized data only."
    )

    replace_existing = st.checkbox(
        "🔄 Replace existing inventory (clear all before import)",
        value=False,
        help="When checked, all current assets will be deleted before importing the new file."
    )

    uploaded = st.file_uploader(
        "Choose file", type=["csv", "json"],
        help="CSV must have headers matching asset fields. JSON: array of objects or {assets: [...]}",
    )

    if uploaded:
        file_bytes = uploaded.read()
        valid, msg, df = validate_file_upload(file_bytes, uploaded.name)

        if not valid:
            st.error(f"❌ {msg}")
        else:
            st.success(f"✅ {msg}")
            assets, errors = validate_dataframe(df)

            if errors:
                st.warning(f"⚠️ {len(errors)} validation issue(s) found:")
                err_df = pd.DataFrame(errors)
                st.dataframe(err_df, use_container_width=True, height=200)

            if assets:
                st.info(f"✅ **{len(assets)} valid assets** ready to import.")
                if replace_existing:
                    st.warning(f"⚠️ This will first delete all {db.asset_count()} existing assets, then import {len(assets)} new ones.")

                if st.button("⬆️ Import & Run Risk Assessment", type="primary"):
                    if replace_existing:
                        deleted = db.delete_all_assets()
                        db.log_activity("Cleared inventory before import", f"Deleted {deleted} assets")

                    count = import_assets_to_db(db, assets, source=uploaded.name)

                    # Auto-run risk assessment on every imported asset
                    progress = st.progress(0, text="Running risk assessment...")
                    for i, asset in enumerate(assets):
                        d = asset.to_dict()
                        finding = analyze_asset(d)
                        score = compute_risk_score(d, finding)
                        db.save_assessment(d["asset_id"], finding.to_dict(), score.to_dict())
                        progress.progress((i + 1) / len(assets), text=f"Assessing {d['asset_id']}...")

                    progress.empty()
                    db.log_activity("Assessment completed", f"Assessed {count} imported assets", count)
                    st.success(f"✅ Imported and assessed **{count} assets**. Go to ⚡ Risk Assessment to view results.")
                    st.rerun()
            elif not errors:
                st.warning("No valid assets found in file.")



# ── Filters ──────────────────────────────────────────────────────────
df = get_assets_dataframe(db)

if df.empty:
    st.info(
        "📭 **No assets in inventory.** Click **Load Demo Data** or upload a CSV/JSON above."
    )
    st.stop()

st.markdown(f"### Inventory ({len(df)} assets)")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    search = st.text_input("🔍 Search", placeholder="Name, ID, algorithm...",
                           help="Filter by asset name, ID, or algorithm")
with filter_col2:
    type_filter = st.multiselect(
        "Asset Type", options=sorted(df["asset_type"].unique()),
    )
with filter_col3:
    algo_filter = st.multiselect(
        "Algorithm", options=sorted(df["cryptographic_algorithm"].unique()),
    )
with filter_col4:
    status_filter = st.multiselect(
        "Migration Status", options=sorted(df["migration_status"].unique()),
    )

filter2_col1, filter2_col2, filter2_col3 = st.columns(3)
with filter2_col1:
    env_filter = st.multiselect(
        "Environment", options=sorted(df["environment"].unique()),
    )
with filter2_col2:
    sens_filter = st.multiselect(
        "Data Sensitivity", options=sorted(df["data_sensitivity"].unique()),
    )
with filter2_col3:
    crit_filter = st.multiselect(
        "Business Criticality", options=sorted(df["business_criticality"].unique()),
    )

# Apply filters
filtered = df.copy()
if search:
    mask = filtered.apply(
        lambda row: search.lower() in " ".join(str(v).lower() for v in row.values),
        axis=1,
    )
    filtered = filtered[mask]
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

st.markdown(f"*Showing {len(filtered)} of {len(df)} assets*")

# ── Asset Table ──────────────────────────────────────────────────────
display_cols = [
    "asset_id", "asset_name", "asset_type", "cryptographic_algorithm",
    "cryptographic_purpose", "environment", "data_sensitivity",
    "business_criticality", "internet_exposed", "migration_status",
]
display = filtered[[c for c in display_cols if c in filtered.columns]]

st.dataframe(
    display,
    use_container_width=True,
    height=400,
    column_config={
        "asset_id": st.column_config.TextColumn("ID", width="small"),
        "asset_name": st.column_config.TextColumn("Name", width="medium"),
        "internet_exposed": st.column_config.CheckboxColumn("Internet", width="small"),
    },
)

# ── Export ────────────────────────────────────────────────────────────
export_col1, export_col2 = st.columns([1, 5])
with export_col1:
    csv_data = filtered.to_csv(index=False)
    st.download_button(
        "📥 Export CSV", csv_data,
        file_name="qshield_inventory.csv",
        mime="text/csv",
    )

st.markdown("---")

# ── Add / Edit / Delete ──────────────────────────────────────────────
tab_add, tab_edit, tab_delete = st.tabs(["➕ Add Asset", "✏️ Edit Asset", "🗑️ Delete Asset"])

with tab_add:
    st.markdown("#### Add New Asset")
    with st.form("add_asset_form"):
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            new_id = st.text_input("Asset ID*", placeholder="ASSET-016")
            new_name = st.text_input("Asset Name*", placeholder="My Service")
            new_type = st.selectbox("Asset Type*", [e.value for e in AssetType])
            new_domain = st.text_input("Business Domain", placeholder="Payments")
            new_env = st.selectbox("Environment", [e.value for e in Environment])
            new_owner = st.text_input("Owner", placeholder="Team Name")
        with ac2:
            new_algo = st.text_input("Algorithm*", placeholder="RSA-2048")
            new_purpose = st.selectbox("Purpose", [e.value for e in CryptoPurpose])
            new_protocol = st.text_input("Protocol", placeholder="TLS 1.3")
            new_cert = st.text_input("Certificate Expiry", placeholder="2027-12-31")
            new_sens = st.selectbox("Data Sensitivity", [e.value for e in DataSensitivity])
            new_ret = st.number_input("Retention (years)", 0, 100, 5)
        with ac3:
            new_crit = st.selectbox("Business Criticality", [e.value for e in BusinessCriticality])
            new_exposed = st.checkbox("Internet Exposed")
            new_deps = st.number_input("Dependencies", 0, 100, 0)
            new_status = st.selectbox("Migration Status", [e.value for e in MigrationStatus])
            new_notes = st.text_area("Notes", height=80)

        if st.form_submit_button("Add Asset", type="primary"):
            data = {
                "asset_id": sanitize_text(new_id),
                "asset_name": sanitize_text(new_name),
                "asset_type": new_type,
                "business_domain": sanitize_text(new_domain),
                "environment": new_env,
                "owner": sanitize_text(new_owner),
                "cryptographic_algorithm": sanitize_text(new_algo),
                "cryptographic_purpose": new_purpose,
                "protocol": sanitize_text(new_protocol),
                "certificate_expiry": sanitize_text(new_cert),
                "data_sensitivity": new_sens,
                "data_retention_years": new_ret,
                "business_criticality": new_crit,
                "internet_exposed": new_exposed,
                "dependency_count": new_deps,
                "migration_status": new_status,
                "notes": sanitize_text(new_notes),
            }
            ok, issues = validate_single_asset(data)
            if not ok:
                for iss in issues:
                    st.error(iss)
            else:
                asset = CryptographicAsset.from_dict(data)
                db.upsert_asset(asset)
                finding = analyze_asset(data)
                score = compute_risk_score(data, finding)
                db.save_assessment(data["asset_id"], finding.to_dict(), score.to_dict())
                db.log_activity("Added asset", f"{data['asset_id']}: {data['asset_name']}")
                st.success(f"✅ Added asset {data['asset_id']}")
                st.rerun()

with tab_edit:
    st.markdown("#### Edit Existing Asset")
    asset_ids = filtered["asset_id"].tolist()
    if not asset_ids:
        st.info("No assets to edit.")
    else:
        edit_id = st.selectbox("Select Asset", asset_ids,
                               format_func=lambda x: f"{x} — {filtered[filtered['asset_id']==x]['asset_name'].iloc[0]}" if len(filtered[filtered['asset_id']==x]) > 0 else x)
        existing = db.get_asset(edit_id)
        if existing:
            with st.form("edit_asset_form"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    ed_name = st.text_input("Name", value=existing.get("asset_name", ""))
                    ed_algo = st.text_input("Algorithm", value=existing.get("cryptographic_algorithm", ""))
                    ed_sens = st.selectbox("Data Sensitivity",
                                          [e.value for e in DataSensitivity],
                                          index=[e.value for e in DataSensitivity].index(existing.get("data_sensitivity", "Internal")) if existing.get("data_sensitivity") in [e.value for e in DataSensitivity] else 1)
                    ed_crit = st.selectbox("Business Criticality",
                                          [e.value for e in BusinessCriticality],
                                          index=[e.value for e in BusinessCriticality].index(existing.get("business_criticality", "Medium")) if existing.get("business_criticality") in [e.value for e in BusinessCriticality] else 1)
                with ec2:
                    all_statuses = [e.value for e in MigrationStatus]
                    current_status = existing.get("migration_status", "Not Started")
                    ed_status = st.selectbox("Migration Status",
                                            all_statuses,
                                            index=all_statuses.index(current_status) if current_status in all_statuses else 0)
                    ed_notes = st.text_area("Notes", value=existing.get("notes", ""))
                    ed_exposed = st.checkbox("Internet Exposed", value=bool(existing.get("internet_exposed")))
                    ed_deps = st.number_input("Dependencies", 0, 100, int(existing.get("dependency_count", 0)))

                if st.form_submit_button("Update Asset", type="primary"):
                    existing["asset_name"] = sanitize_text(ed_name)
                    existing["cryptographic_algorithm"] = sanitize_text(ed_algo)
                    existing["data_sensitivity"] = ed_sens
                    existing["business_criticality"] = ed_crit
                    existing["migration_status"] = ed_status
                    existing["notes"] = sanitize_text(ed_notes)
                    existing["internet_exposed"] = ed_exposed
                    existing["dependency_count"] = ed_deps
                    asset = CryptographicAsset.from_dict(existing)
                    db.upsert_asset(asset)
                    finding = analyze_asset(existing)
                    score = compute_risk_score(existing, finding)
                    db.save_assessment(edit_id, finding.to_dict(), score.to_dict())
                    db.log_activity("Updated asset", f"{edit_id}")
                    st.success(f"✅ Updated {edit_id}")
                    st.rerun()

with tab_delete:
    st.markdown("#### Delete Asset")
    del_ids = filtered["asset_id"].tolist()
    if not del_ids:
        st.info("No assets to delete.")
    else:
        del_id = st.selectbox("Select asset to delete", del_ids, key="del_select",
                              format_func=lambda x: f"{x} — {filtered[filtered['asset_id']==x]['asset_name'].iloc[0]}" if len(filtered[filtered['asset_id']==x]) > 0 else x)
        st.warning(f"⚠️ This will permanently delete **{del_id}** and its assessment.")
        if st.button("🗑️ Delete", type="primary"):
            db.delete_asset(del_id)
            db.log_activity("Deleted asset", del_id)
            st.success(f"Deleted {del_id}")
            st.rerun()
