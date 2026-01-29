import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# Page configuration
st.set_page_config(
    page_title="Manufacturing Tag Configuration",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .industry-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.3s;
        color: white;
        font-size: 20px;
        font-weight: bold;
        margin: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .industry-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    .welcome-header {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        margin: 30px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .breadcrumb {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        font-size: 16px;
    }
    .breadcrumb-item {
        display: inline;
        color: #667eea;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "welcome"
if "selected_industry" not in st.session_state:
    st.session_state.selected_industry = None
if "plant_hierarchy" not in st.session_state:
    st.session_state.plant_hierarchy = {
        "plant": "",
        "area": "",
        "equipment": "",
        "asset": "",
    }
if "hierarchy_data" not in st.session_state:
    st.session_state.hierarchy_data = pd.DataFrame(
        columns=["Industry", "Plant", "Area", "Equipment", "Asset"]
    )
if "selected_hierarchy_path" not in st.session_state:
    st.session_state.selected_hierarchy_path = None
if "tags_data" not in st.session_state:
    st.session_state.tags_data = pd.DataFrame(
        columns=[
            "Industry",
            "Plant",
            "Area",
            "Equipment",
            "Asset",
            "DCS_Tag",
            "Raw_Parameter",
            "Generic_Tag",
            "UUID",
            "Metadata",
            "UOM",
            "Low_Low_Limit",
            "Low_Limit",
            "High_Limit",
            "High_High_Limit",
        ]
    )
if "tag_entries" not in st.session_state:
    st.session_state.tag_entries = []
if "generic_tags" not in st.session_state:
    st.session_state.generic_tags = [
        "Temperature",
        "Pressure",
        "Flow",
        "Level",
        "Speed",
        "Current",
        "Voltage",
        "Power",
        "Vibration",
        "pH",
        "Density",
        "Moisture",
    ]
if "uom_list" not in st.session_state:
    st.session_state.uom_list = [
        "°C",
        "°F",
        "K",
        "bar",
        "psi",
        "kPa",
        "MPa",
        "m³/h",
        "L/min",
        "kg/h",
        "m",
        "mm",
        "%",
        "RPM",
        "A",
        "V",
        "kW",
        "MW",
        "mm/s",
        "g",
    ]
# New dataframe to store Generic Tags with Industry and Equipment mapping
if "generic_tags_mapping" not in st.session_state:
    st.session_state.generic_tags_mapping = pd.DataFrame(
        columns=["Generic_Tag", "Industry", "Equipment", "Count", "Last_Updated"]
    )
# New dataframe to store Available Generic Tags with Metadata (from uploads)
if "available_generic_tags" not in st.session_state:
    st.session_state.available_generic_tags = pd.DataFrame(
        columns=["Generic_Tag", "UUID", "Metadata", "Industry", "Equipment"]
    )
# Track if user selected "+ Add New" for generic tag
if "show_new_generic_tag" not in st.session_state:
    st.session_state.show_new_generic_tag = False
# Track if user selected "+ Add New" for UOM
if "show_new_uom" not in st.session_state:
    st.session_state.show_new_uom = False
# Track tag input values for clearing
if "clear_tag_inputs" not in st.session_state:
    st.session_state.clear_tag_inputs = False
# Track the last visited page to detect page changes
if "last_page" not in st.session_state:
    st.session_state.last_page = None
# Track if first section of tag form has been submitted
if "tag_form_submitted" not in st.session_state:
    st.session_state.tag_form_submitted = False

# Industries list
INDUSTRIES = [
    "🏢 Cement",
    "⚙️ Aluminum",
    "🔩 Steel",
    "🛞 Tyre",
    "📄 Paper & Pulp",
    "🛢️ Oil & Gas",
    "🚙 Automobile",
]


def update_generic_tags_mapping(generic_tag, industry, equipment):
    """Update or add generic tag mapping with industry and equipment"""
    from datetime import datetime

    # Check if this combination already exists
    mask = (
        (st.session_state.generic_tags_mapping["Generic_Tag"] == generic_tag)
        & (st.session_state.generic_tags_mapping["Industry"] == industry)
        & (st.session_state.generic_tags_mapping["Equipment"] == equipment)
    )

    if st.session_state.generic_tags_mapping[mask].empty:
        # Add new entry
        new_entry = pd.DataFrame(
            [
                {
                    "Generic_Tag": generic_tag,
                    "Industry": industry,
                    "Equipment": equipment,
                    "Count": 1,
                    "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ]
        )
        st.session_state.generic_tags_mapping = pd.concat(
            [st.session_state.generic_tags_mapping, new_entry], ignore_index=True
        )
    else:
        # Update existing entry
        idx = st.session_state.generic_tags_mapping[mask].index[0]
        st.session_state.generic_tags_mapping.loc[idx, "Count"] += 1
        st.session_state.generic_tags_mapping.loc[idx, "Last_Updated"] = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )


def validate_hierarchy_input(text):
    """Validate that input contains only uppercase letters, numbers, and underscores"""
    import re
    pattern = r'^[A-Z0-9_]*$'
    return re.match(pattern, text) is not None


def get_generic_tags_for_equipment(industry, equipment):
    """Get available generic tags based on industry and equipment from uploaded data"""
    if st.session_state.available_generic_tags.empty:
        return []

    # Filter by industry and equipment
    filtered = st.session_state.available_generic_tags[
        (st.session_state.available_generic_tags["Industry"] == industry)
        & (st.session_state.available_generic_tags["Equipment"] == equipment)
    ]

    if not filtered.empty:
        # Return unique generic tags
        return filtered["Generic_Tag"].unique().tolist()

    # If no exact match, try just industry
    filtered = st.session_state.available_generic_tags[
        st.session_state.available_generic_tags["Industry"] == industry
    ]

    if not filtered.empty:
        return filtered["Generic_Tag"].unique().tolist()

    return []


def get_metadata_for_generic_tag(generic_tag, industry, equipment):
    """Get metadata for a specific generic tag based on industry and equipment"""
    if st.session_state.available_generic_tags.empty or not generic_tag:
        return ""

    # Filter by generic tag, industry, and equipment
    filtered = st.session_state.available_generic_tags[
        (st.session_state.available_generic_tags["Generic_Tag"] == generic_tag)
        & (st.session_state.available_generic_tags["Industry"] == industry)
        & (st.session_state.available_generic_tags["Equipment"] == equipment)
    ]

    if not filtered.empty:
        return filtered.iloc[0]["Metadata"]

    # If no exact match, try with just generic tag and industry
    filtered = st.session_state.available_generic_tags[
        (st.session_state.available_generic_tags["Generic_Tag"] == generic_tag)
        & (st.session_state.available_generic_tags["Industry"] == industry)
    ]

    if not filtered.empty:
        return filtered.iloc[0]["Metadata"]

    return ""


def get_or_create_uuid_for_generic_tag(generic_tag, industry, equipment, metadata=""):
    """Get existing UUID or create a new one for a generic tag"""
    if not generic_tag:
        return ""

    # Check if UUID already exists for this generic tag, industry, and equipment combination
    if not st.session_state.available_generic_tags.empty:
        filtered = st.session_state.available_generic_tags[
            (st.session_state.available_generic_tags["Generic_Tag"] == generic_tag)
            & (st.session_state.available_generic_tags["Industry"] == industry)
            & (st.session_state.available_generic_tags["Equipment"] == equipment)
        ]

        if not filtered.empty:
            return filtered.iloc[0]["UUID"]

        # If no exact match, try with just generic tag and industry
        filtered = st.session_state.available_generic_tags[
            (st.session_state.available_generic_tags["Generic_Tag"] == generic_tag)
            & (st.session_state.available_generic_tags["Industry"] == industry)
        ]

        if not filtered.empty:
            return filtered.iloc[0]["UUID"]

    # Generate new UUID if not found
    new_uuid = str(uuid.uuid4())

    # Add to available_generic_tags if not already present
    new_entry = pd.DataFrame([{
        "Generic_Tag": generic_tag,
        "UUID": new_uuid,
        "Metadata": metadata,
        "Industry": industry,
        "Equipment": equipment,
    }])
    st.session_state.available_generic_tags = pd.concat(
        [st.session_state.available_generic_tags, new_entry],
        ignore_index=True
    )

    return new_uuid


def quick_actions_sidebar():
    """Display expandable quick actions sidebar available on all pages"""
    with st.sidebar:
        st.markdown("### 🚀 Quick Actions")
        st.markdown("---")

        # Navigation buttons
        if st.button("🏠 Home", use_container_width=True, key="qa_home"):
            st.session_state.page = "welcome"
            st.rerun()

        if st.button("🏭 Plant Hierarchy", use_container_width=True, key="qa_hierarchy"):
            st.session_state.page = "hierarchy"
            st.rerun()

        if st.button("📝 Configure Tags", use_container_width=True, key="qa_tags", disabled=(st.session_state.page == "welcome")):
            st.session_state.page = "tags"
            st.rerun()

        if st.button("📊 View Summary", use_container_width=True, key="qa_summary"):
            st.session_state.page = "summary"
            st.rerun()

        st.markdown("---")

        # Upload action
        if st.button("📤 Upload Generic Tags", use_container_width=True, type="primary", key="qa_upload"):
            st.session_state.page = "upload"
            st.rerun()

        st.markdown("---")

        # Statistics (if data available)
        if not st.session_state.tags_data.empty:
            st.markdown("### 📈 Statistics")
            st.metric("Industries", st.session_state.tags_data["Industry"].nunique())
            st.metric("Plants", st.session_state.tags_data["Plant"].nunique())
            st.metric("Total Tags", len(st.session_state.tags_data))
            st.metric("Generic Tags", len(st.session_state.generic_tags))


def welcome_screen():
    """Display welcome screen with industry selection"""
    quick_actions_sidebar()

    # Track current page
    st.session_state.last_page = "welcome"

    st.markdown(
        '<div class="welcome-header">Hey, Infinitian! Welcome 👋</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.subheader("Select Manufacturing Industry")

    # Create industry cards in grid
    cols = st.columns(4)
    for idx, industry in enumerate(INDUSTRIES):
        with cols[idx % 4]:
            if st.button(industry, key=f"ind_{idx}", use_container_width=True):
                st.session_state.selected_industry = industry.split(" ", 1)[
                    1
                ]  # Remove emoji
                st.session_state.page = "hierarchy"
                st.rerun()


def get_unique_values(column_name, industry=None, filters=None):
    """Get unique values from hierarchy data for dropdown with optional filters"""
    if not st.session_state.hierarchy_data.empty:
        df = st.session_state.hierarchy_data

        # Filter by industry
        if industry:
            df = df[df["Industry"] == industry]

        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if value:
                    df = df[df[key] == value]

        if not df.empty:
            return sorted(df[column_name].unique().tolist())
    return []


def plant_hierarchy_screen():
    """Display plant hierarchy setup screen"""
    quick_actions_sidebar()

    st.title(f"Plant Hierarchy Setup - {st.session_state.selected_industry}")

    # Reset to "Select Existing" when entering this page from another page
    if st.session_state.last_page != "hierarchy":
        st.session_state.hierarchy_input_mode = {
            "plant": "Select Existing",
            "area": "Select Existing",
            "equipment": "Select Existing",
            "asset": "Select Existing",
        }
        st.session_state.last_page = "hierarchy"

    # Initialize if not present
    if "hierarchy_input_mode" not in st.session_state:
        st.session_state.hierarchy_input_mode = {
            "plant": "Select Existing",
            "area": "Select Existing",
            "equipment": "Select Existing",
            "asset": "Select Existing",
        }

    if st.button("← Back to Industries"):
        # Reset hierarchy fields
        st.session_state.plant_hierarchy = {
            "plant": "",
            "area": "",
            "equipment": "",
            "asset": "",
        }
        # Reset input modes to Select Existing
        st.session_state.hierarchy_input_mode = {
            "plant": "Select Existing",
            "area": "Select Existing",
            "equipment": "Select Existing",
            "asset": "Select Existing",
        }
        st.session_state.page = "welcome"
        st.rerun()

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Define Plant Hierarchy")

        # Plant Name
        st.markdown("### 🏭 Plant Name")
        plant_options = get_unique_values(
            "Plant", industry=st.session_state.selected_industry
        )

        # Determine default radio selection
        plant_radio_default = (
            0
            if st.session_state.hierarchy_input_mode["plant"] == "Select Existing"
            else 1
        )
        plant_input_type = st.radio(
            "Plant Input",
            ["Select Existing", "Add New"],
            index=plant_radio_default,
            horizontal=True,
            key="plant_radio",
        )
        st.session_state.hierarchy_input_mode["plant"] = plant_input_type

        if plant_input_type == "Select Existing" and plant_options:
            # Get index for select box based on session state
            plant_value = st.session_state.plant_hierarchy.get("plant", "")
            if plant_value in plant_options:
                plant_idx = plant_options.index(plant_value) + 1
            else:
                plant_idx = 0
            plant = st.selectbox(
                "Select Plant",
                [""] + plant_options,
                index=plant_idx,
                key="plant_select",
            )
        else:
            plant = st.text_input(
                "Enter Plant Name",
                value=st.session_state.plant_hierarchy.get("plant", ""),
                key="plant_input",
                help="Only uppercase letters (A-Z), numbers (0-9), and underscores (_) are allowed",
            )
            # Validate input
            if plant and not validate_hierarchy_input(plant):
                st.error("❌ Invalid input! Only uppercase letters (A-Z), numbers (0-9), and underscores (_) are allowed.")
                plant = ""  # Clear invalid input

        st.session_state.plant_hierarchy["plant"] = plant

        # Area
        st.markdown("### 📍 Area")
        area_options = get_unique_values(
            "Area",
            industry=st.session_state.selected_industry,
            filters={"Plant": plant} if plant else None,
        )

        area_radio_default = (
            0
            if st.session_state.hierarchy_input_mode["area"] == "Select Existing"
            else 1
        )
        area_input_type = st.radio(
            "Area Input",
            ["Select Existing", "Add New"],
            index=area_radio_default,
            horizontal=True,
            key="area_radio",
        )
        st.session_state.hierarchy_input_mode["area"] = area_input_type

        if area_input_type == "Select Existing" and area_options:
            area_value = st.session_state.plant_hierarchy.get("area", "")
            if area_value in area_options:
                area_idx = area_options.index(area_value) + 1
            else:
                area_idx = 0
            area = st.selectbox(
                "Select Area", [""] + area_options, index=area_idx, key="area_select"
            )
        else:
            area = st.text_input(
                "Enter Area Name",
                value=st.session_state.plant_hierarchy.get("area", ""),
                key="area_input",
                help="Only uppercase letters (A-Z), numbers (0-9), and underscores (_) are allowed",
            )
            # Validate input
            if area and not validate_hierarchy_input(area):
                st.error("❌ Invalid input! Only uppercase letters (A-Z), numbers (0-9), and underscores (_) are allowed.")
                area = ""  # Clear invalid input

        st.session_state.plant_hierarchy["area"] = area

        # Equipment
        st.markdown("### ⚙️ Equipment")
        equipment_options = get_unique_values(
            "Equipment",
            industry=st.session_state.selected_industry,
            filters={"Plant": plant, "Area": area} if plant and area else None,
        )

        equipment_radio_default = (
            0
            if st.session_state.hierarchy_input_mode["equipment"] == "Select Existing"
            else 1
        )
        equipment_input_type = st.radio(
            "Equipment Input",
            ["Select Existing", "Add New"],
            index=equipment_radio_default,
            horizontal=True,
            key="equipment_radio",
        )
        st.session_state.hierarchy_input_mode["equipment"] = equipment_input_type

        if equipment_input_type == "Select Existing" and equipment_options:
            equipment_value = st.session_state.plant_hierarchy.get("equipment", "")
            if equipment_value in equipment_options:
                equipment_idx = equipment_options.index(equipment_value) + 1
            else:
                equipment_idx = 0
            equipment = st.selectbox(
                "Select Equipment",
                [""] + equipment_options,
                index=equipment_idx,
                key="equipment_select",
            )
        else:
            equipment = st.text_input(
                "Enter Equipment Name",
                value=st.session_state.plant_hierarchy.get("equipment", ""),
                key="equipment_input",
                help="Only uppercase letters (A-Z), numbers (0-9), and underscores (_) are allowed",
            )
            # Validate input
            if equipment and not validate_hierarchy_input(equipment):
                st.error("❌ Invalid input! Only uppercase letters (A-Z), numbers (0-9), and underscores (_) are allowed.")
                equipment = ""  # Clear invalid input

        st.session_state.plant_hierarchy["equipment"] = equipment

        # Asset
        st.markdown("### 🔧 Asset")
        asset_options = get_unique_values(
            "Asset",
            industry=st.session_state.selected_industry,
            filters=(
                {"Plant": plant, "Area": area, "Equipment": equipment}
                if plant and area and equipment
                else None
            ),
        )

        asset_radio_default = (
            0
            if st.session_state.hierarchy_input_mode["asset"] == "Select Existing"
            else 1
        )
        asset_input_type = st.radio(
            "Asset Input",
            ["Select Existing", "Add New"],
            index=asset_radio_default,
            horizontal=True,
            key="asset_radio",
        )
        st.session_state.hierarchy_input_mode["asset"] = asset_input_type

        if asset_input_type == "Select Existing" and asset_options:
            asset_value = st.session_state.plant_hierarchy.get("asset", "")
            if asset_value in asset_options:
                asset_idx = asset_options.index(asset_value) + 1
            else:
                asset_idx = 0
            asset = st.selectbox(
                "Select Asset",
                [""] + asset_options,
                index=asset_idx,
                key="asset_select",
            )
        else:
            asset = st.text_input(
                "Enter Asset Name",
                value=st.session_state.plant_hierarchy.get("asset", ""),
                key="asset_input",
                help="Only uppercase letters (A-Z), numbers (0-9), and underscores (_) are allowed",
            )
            # Validate input
            if asset and not validate_hierarchy_input(asset):
                st.error("❌ Invalid input! Only uppercase letters (A-Z), numbers (0-9), and underscores (_) are allowed.")
                asset = ""  # Clear invalid input

        st.session_state.plant_hierarchy["asset"] = asset

        # Save and Proceed button
        st.markdown("---")
        all_filled = all(
            [
                st.session_state.plant_hierarchy["plant"],
                st.session_state.plant_hierarchy["area"],
                st.session_state.plant_hierarchy["equipment"],
                st.session_state.plant_hierarchy["asset"],
            ]
        )

        if all_filled:
            if st.button(
                "📝 Define Tags & Details →", type="primary", use_container_width=True
            ):
                # Save hierarchy to dataframe
                new_row = pd.DataFrame(
                    [
                        {
                            "Industry": st.session_state.selected_industry,
                            "Plant": st.session_state.plant_hierarchy["plant"],
                            "Area": st.session_state.plant_hierarchy["area"],
                            "Equipment": st.session_state.plant_hierarchy["equipment"],
                            "Asset": st.session_state.plant_hierarchy["asset"],
                        }
                    ]
                )
                st.session_state.hierarchy_data = pd.concat(
                    [st.session_state.hierarchy_data, new_row], ignore_index=True
                )
                st.session_state.hierarchy_data = (
                    st.session_state.hierarchy_data.drop_duplicates()
                )

                st.session_state.page = "tags"
                st.rerun()
        else:
            st.warning("⚠️ Please fill all hierarchy fields to proceed")

    with col2:
        st.subheader("Available Hierarchies")
        st.info("💡 Click on any item below to auto-fill the hierarchy")

        if not st.session_state.hierarchy_data.empty:
            # Filter hierarchy data for current industry
            df = st.session_state.hierarchy_data[
                st.session_state.hierarchy_data["Industry"]
                == st.session_state.selected_industry
            ]

            if not df.empty:
                # Create a list of all hierarchy paths with buttons
                hierarchy_options = []

                for plant in df["Plant"].unique():
                    st.markdown(f"**🏭 {plant}**")
                    plant_data = df[df["Plant"] == plant]

                    for area in plant_data["Area"].unique():
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;├─ 📍 {area}")
                        area_data = plant_data[plant_data["Area"] == area]

                        for equipment in area_data["Equipment"].unique():
                            st.markdown(
                                f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├─ ⚙️ {equipment}"
                            )
                            equipment_data = area_data[
                                area_data["Equipment"] == equipment
                            ]

                            assets = equipment_data["Asset"].unique()
                            for idx, asset in enumerate(assets):
                                tree_symbol = "└─" if idx == len(assets) - 1 else "├─"

                                # Add to options list
                                hierarchy_options.append(
                                    {
                                        "plant": plant,
                                        "area": area,
                                        "equipment": equipment,
                                        "asset": asset,
                                    }
                                )

                                option_idx = len(hierarchy_options) - 1

                                col_tree, col_btn = st.columns([3, 1])
                                with col_tree:
                                    st.markdown(
                                        f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{tree_symbol} 🔧 {asset}"
                                    )
                                with col_btn:
                                    if st.button(
                                        "✓",
                                        key=f"btn_select_{option_idx}",
                                        help=f"Select: {plant} → {area} → {equipment} → {asset}",
                                    ):
                                        # Get the hierarchy data from the options list
                                        selected = hierarchy_options[option_idx]

                                        # Update session state
                                        st.session_state.plant_hierarchy["plant"] = (
                                            selected["plant"]
                                        )
                                        st.session_state.plant_hierarchy["area"] = (
                                            selected["area"]
                                        )
                                        st.session_state.plant_hierarchy[
                                            "equipment"
                                        ] = selected["equipment"]
                                        st.session_state.plant_hierarchy["asset"] = (
                                            selected["asset"]
                                        )

                                        # Set input modes to "Select Existing"
                                        st.session_state.hierarchy_input_mode = {
                                            "plant": "Select Existing",
                                            "area": "Select Existing",
                                            "equipment": "Select Existing",
                                            "asset": "Select Existing",
                                        }
                                        st.rerun()

                    st.markdown("---")
            else:
                st.info(
                    f"No hierarchy data for {st.session_state.selected_industry} yet"
                )
        else:
            st.info("No hierarchy data saved yet")


def tags_configuration_screen():
    """Display tags configuration screen"""
    quick_actions_sidebar()

    # Track current page
    st.session_state.last_page = "tags"

    # Breadcrumb
    hierarchy = st.session_state.plant_hierarchy
    breadcrumb_html = f"""
    <div class="breadcrumb">
        <span class="breadcrumb-item">🏭 {hierarchy['plant']}</span> → 
        <span class="breadcrumb-item">📍 {hierarchy['area']}</span> → 
        <span class="breadcrumb-item">⚙️ {hierarchy['equipment']}</span> → 
        <span class="breadcrumb-item">🔧 {hierarchy['asset']}</span>
    </div>
    """
    st.markdown(breadcrumb_html, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Tags & Details Configuration")
    with col2:
        if st.button("← Back to Hierarchy"):
            # Reset tag input values
            st.session_state.tag_input_values = {
                "dcs_tag": "",
                "raw_parameter": "",
                "generic_tag_select": "",
                "new_generic_tag": "",
                "uuid": "",
                "metadata": "",
                "uom_select": "",
                "new_uom": "",
                "low_low_limit": 0.0,
                "low_limit": 0.0,
                "high_limit": 0.0,
                "high_high_limit": 0.0,
            }
            # Reset show flags
            st.session_state.show_new_generic_tag = False
            st.session_state.show_new_uom = False
            st.session_state.page = "hierarchy"
            st.rerun()

    st.markdown("---")

    # Get suggested generic tags for this equipment and industry
    suggested_tags = get_generic_tags_for_equipment(
        st.session_state.selected_industry, hierarchy["equipment"]
    )

    if suggested_tags:
        st.info(
            f"💡 Suggested Generic Tags for {hierarchy['equipment']}: {', '.join(suggested_tags[:5])}"
        )

    # Add Tag Entry Section with Clear All button
    col_title, col_clear = st.columns([3, 1])
    with col_title:
        st.subheader("➕ Add New Tag")
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True, key="clear_all_button"):
            # Reset all form values to initial state
            st.session_state.tag_input_values = {
                "dcs_tag": "",
                "raw_parameter": "",
                "generic_tag_select": "",
                "new_generic_tag": "",
                "uuid": "",
                "metadata": "",
                "uom_select": "",
                "new_uom": "",
                "low_low_limit": 0.0,
                "low_limit": 0.0,
                "high_limit": 0.0,
                "high_high_limit": 0.0,
            }
            # Clear widget states
            widget_keys = [
                "dcs_tag_input", "raw_param_input", "generic_tag_select",
                "new_generic_tag", "uom_select", "new_uom",
                "low_low_input", "low_input", "high_input", "high_high_input",
                "uuid_display", "metadata_input"
            ]
            for key in widget_keys:
                if key in st.session_state:
                    del st.session_state[key]

            # Reset the show flags
            st.session_state.show_new_generic_tag = False
            st.session_state.show_new_uom = False
            # Reset form submission to hide Section 2
            st.session_state.tag_form_submitted = False
            # Reset last selected generic tag
            st.session_state.last_selected_generic_tag = ""
            st.success("✅ Form cleared successfully!")
            st.rerun()

    # Initialize input values in session state if they don't exist or need to be cleared
    if "tag_input_values" not in st.session_state:
        st.session_state.tag_input_values = {
            "dcs_tag": "",
            "raw_parameter": "",
            "generic_tag_select": "",
            "new_generic_tag": "",
            "uuid": "",
            "metadata": "",
            "uom_select": "",
            "new_uom": "",
            "low_low_limit": 0.0,
            "low_limit": 0.0,
            "high_limit": 0.0,
            "high_high_limit": 0.0,
        }

    # Ensure uuid key exists (for backward compatibility with existing sessions)
    if "uuid" not in st.session_state.tag_input_values:
        st.session_state.tag_input_values["uuid"] = ""

    # Track last selected generic tag to detect changes
    if "last_selected_generic_tag" not in st.session_state:
        st.session_state.last_selected_generic_tag = ""

    # Section 1: Basic Tag Information
    st.markdown("### 📝 Section 1: Basic Tag Information")
    col1, col2 = st.columns(2)

    with col1:
        dcs_tag = st.text_input(
            "DCS Tag *",
            placeholder="e.g., TI-101",
            value=st.session_state.tag_input_values["dcs_tag"],
            key="dcs_tag_input",
        )
        raw_parameter = st.text_input(
            "Raw Parameter *",
            placeholder="e.g., Kiln Temperature",
            value=st.session_state.tag_input_values["raw_parameter"],
            key="raw_param_input",
        )

        # Generic Tag with custom option - show suggested tags first if available
        if suggested_tags:
            combined_tags = (
                suggested_tags
                + [
                    tag
                    for tag in st.session_state.generic_tags
                    if tag not in suggested_tags
                ]
                + ["+ Add New"]
            )
        else:
            combined_tags = st.session_state.generic_tags + ["+ Add New"]

        # Get the index for the selectbox
        if st.session_state.tag_input_values["generic_tag_select"] in combined_tags:
            generic_tag_index = (
                combined_tags.index(
                    st.session_state.tag_input_values["generic_tag_select"]
                )
                + 1
            )
        else:
            generic_tag_index = 0

        generic_tag_option = st.selectbox(
            "Generic Tag *",
            [""] + combined_tags,
            index=generic_tag_index,
            key="generic_tag_select",
        )

        # Update session state when "+ Add New" is selected
        if generic_tag_option == "+ Add New":
            st.session_state.show_new_generic_tag = True
            # Reset form submission when changing generic tag
            st.session_state.tag_form_submitted = False
        else:
            st.session_state.show_new_generic_tag = False

        # Show text input immediately when "+ Add New" is selected
        if st.session_state.show_new_generic_tag:
            generic_tag = st.text_input(
                "Enter New Generic Tag",
                value=st.session_state.tag_input_values["new_generic_tag"],
                key="new_generic_tag",
            )
        else:
            generic_tag = generic_tag_option

        # UOM with custom option
        # Get the index for the selectbox
        if st.session_state.tag_input_values["uom_select"] in st.session_state.uom_list:
            uom_index = (
                st.session_state.uom_list.index(
                    st.session_state.tag_input_values["uom_select"]
                )
                + 1
            )
        else:
            uom_index = 0

        uom_option = st.selectbox(
            "UOM (Unit of Measurement) *",
            [""] + st.session_state.uom_list + ["+ Add New"],
            index=uom_index,
            key="uom_select",
        )

        # Update session state when "+ Add New" is selected
        if uom_option == "+ Add New":
            st.session_state.show_new_uom = True
        else:
            st.session_state.show_new_uom = False

        # Show text input immediately when "+ Add New" is selected
        if st.session_state.show_new_uom:
            uom = st.text_input(
                "Enter New UOM",
                value=st.session_state.tag_input_values["new_uom"],
                key="new_uom",
            )
        else:
            uom = uom_option

    with col2:
        low_low_limit = st.number_input(
            "Low-Low Limit",
            value=st.session_state.tag_input_values["low_low_limit"],
            format="%.2f",
            key="low_low_input",
        )
        low_limit = st.number_input(
            "Low Limit",
            value=st.session_state.tag_input_values["low_limit"],
            format="%.2f",
            key="low_input",
        )
        high_limit = st.number_input(
            "High Limit",
            value=st.session_state.tag_input_values["high_limit"],
            format="%.2f",
            key="high_input",
        )
        high_high_limit = st.number_input(
            "High-High Limit",
            value=st.session_state.tag_input_values["high_high_limit"],
            format="%.2f",
            key="high_high_input",
        )

    # Submit button for Section 1
    st.markdown("---")
    submit_col1, submit_col2, submit_col3 = st.columns([1, 1, 1])
    with submit_col2:
        if st.button("✅ Submit", type="primary", use_container_width=True, key="submit_section1"):
            if dcs_tag and raw_parameter and generic_tag and uom:
                # Store all form values in session state
                st.session_state.tag_input_values["dcs_tag"] = dcs_tag
                st.session_state.tag_input_values["raw_parameter"] = raw_parameter
                st.session_state.tag_input_values["generic_tag_select"] = generic_tag
                st.session_state.tag_input_values["uom_select"] = uom
                st.session_state.tag_input_values["low_low_limit"] = low_low_limit
                st.session_state.tag_input_values["low_limit"] = low_limit
                st.session_state.tag_input_values["high_limit"] = high_limit
                st.session_state.tag_input_values["high_high_limit"] = high_high_limit

                # Update metadata and UUID when form is submitted
                auto_metadata = get_metadata_for_generic_tag(
                    generic_tag,
                    st.session_state.selected_industry,
                    hierarchy["equipment"]
                )
                auto_uuid = get_or_create_uuid_for_generic_tag(
                    generic_tag,
                    st.session_state.selected_industry,
                    hierarchy["equipment"],
                    auto_metadata
                )
                st.session_state.tag_input_values["metadata"] = auto_metadata
                st.session_state.tag_input_values["uuid"] = auto_uuid
                st.session_state.tag_form_submitted = True
                st.rerun()
            else:
                st.error("⚠️ Please fill all required fields (marked with *) before submitting")

    # Section 2: UUID and Metadata (shown only after Submit)
    if st.session_state.tag_form_submitted:
        st.markdown("---")
        st.markdown("### 📋 Section 2: Generated Information")

        col1, col2 = st.columns(2)

        with col1:
            # Display UUID field (read-only)
            st.text_input(
                "UUID (Auto-generated)",
                value=st.session_state.tag_input_values["uuid"],
                key="uuid_display",
                disabled=True,
                help="Automatically generated unique identifier for this generic tag"
            )

        with col2:
            metadata = st.text_area(
                "Metadata",
                placeholder="Additional information",
                value=st.session_state.tag_input_values["metadata"],
                height=100,
                key="metadata_input",
            )

            # Update session state with current metadata value (user may have edited it)
            if metadata != st.session_state.tag_input_values["metadata"]:
                st.session_state.tag_input_values["metadata"] = metadata

        # Add Tag button (shown only after Submit)
        st.markdown("---")
        add_tag_col1, add_tag_col2, add_tag_col3 = st.columns([1, 1, 1])
        with add_tag_col2:
            if st.button("➕ Add Tag", type="primary", use_container_width=True):
                # Get all values from session state
                dcs_tag = st.session_state.tag_input_values["dcs_tag"]
                raw_parameter = st.session_state.tag_input_values["raw_parameter"]
                generic_tag = st.session_state.tag_input_values["generic_tag_select"]
                uom = st.session_state.tag_input_values["uom_select"]
                low_low_limit = st.session_state.tag_input_values["low_low_limit"]
                low_limit = st.session_state.tag_input_values["low_limit"]
                high_limit = st.session_state.tag_input_values["high_limit"]
                high_high_limit = st.session_state.tag_input_values["high_high_limit"]
                metadata = st.session_state.tag_input_values["metadata"]
                tag_uuid = st.session_state.tag_input_values["uuid"]

                # Add new generic tag to list if custom
                if (
                    st.session_state.show_new_generic_tag
                    and generic_tag
                    and generic_tag not in st.session_state.generic_tags
                ):
                    st.session_state.generic_tags.append(generic_tag)
                    st.session_state.generic_tags.sort()

                # Update or add metadata to available_generic_tags
                # Check if entry already exists for this generic tag, industry, equipment combination
                existing_mask = (
                    (st.session_state.available_generic_tags["Generic_Tag"] == generic_tag)
                    & (st.session_state.available_generic_tags["Industry"] == st.session_state.selected_industry)
                    & (st.session_state.available_generic_tags["Equipment"] == hierarchy["equipment"])
                )

                if not st.session_state.available_generic_tags.empty and existing_mask.any():
                    # Update existing entry with potentially edited metadata
                    idx = st.session_state.available_generic_tags[existing_mask].index[0]
                    st.session_state.available_generic_tags.loc[idx, "Metadata"] = metadata
                else:
                    # Entry doesn't exist, add it (this shouldn't happen normally as it was created on Submit)
                    new_entry = pd.DataFrame([{
                        "Generic_Tag": generic_tag,
                        "UUID": tag_uuid,
                        "Metadata": metadata,
                        "Industry": st.session_state.selected_industry,
                        "Equipment": hierarchy["equipment"],
                    }])
                    st.session_state.available_generic_tags = pd.concat(
                        [st.session_state.available_generic_tags, new_entry],
                        ignore_index=True
                    )

                # Update generic tags mapping
                update_generic_tags_mapping(
                    generic_tag, st.session_state.selected_industry, hierarchy["equipment"]
                )

                # Add new UOM to list if custom
                if (
                    st.session_state.show_new_uom
                    and uom
                    and uom not in st.session_state.uom_list
                ):
                    st.session_state.uom_list.append(uom)
                    st.session_state.uom_list.sort()

                # Create tag entry
                tag_entry = {
                    "Industry": st.session_state.selected_industry,
                    "Plant": hierarchy["plant"],
                    "Area": hierarchy["area"],
                    "Equipment": hierarchy["equipment"],
                    "Asset": hierarchy["asset"],
                    "DCS_Tag": dcs_tag,
                    "Raw_Parameter": raw_parameter,
                    "Generic_Tag": generic_tag,
                    "UUID": tag_uuid,
                    "Metadata": metadata,
                    "UOM": uom,
                    "Low_Low_Limit": low_low_limit,
                    "Low_Limit": low_limit,
                    "High_Limit": high_limit,
                    "High_High_Limit": high_high_limit,
                }

                st.session_state.tag_entries.append(tag_entry)

                # Clear all input values but keep Section 2 visible
                st.session_state.tag_input_values = {
                    "dcs_tag": "",
                    "raw_parameter": "",
                    "generic_tag_select": "",
                    "new_generic_tag": "",
                    "uuid": "",
                    "metadata": "",
                    "uom_select": "",
                    "new_uom": "",
                    "low_low_limit": 0.0,
                    "low_limit": 0.0,
                    "high_limit": 0.0,
                    "high_high_limit": 0.0,
                }

                # Reset the show flags
                st.session_state.show_new_generic_tag = False
                st.session_state.show_new_uom = False
                # Keep tag_form_submitted as True to keep Section 2 visible

                # Reset last selected generic tag
                st.session_state.last_selected_generic_tag = ""

                st.success(f"✅ Tag '{dcs_tag}' added successfully!")
                st.rerun()

    # Display current tags
    st.markdown("---")
    st.subheader(f"📋 Configured Tags ({len(st.session_state.tag_entries)})")

    if st.session_state.tag_entries:
        # Convert to dataframe for display
        tags_df = pd.DataFrame(st.session_state.tag_entries)

        # Ensure UUID column exists (for backward compatibility)
        if "UUID" not in tags_df.columns:
            tags_df["UUID"] = ""

        # Display with option to delete
        for idx, row in tags_df.iterrows():
            with st.expander(
                f"🏷️ {row['DCS_Tag']} - {row['Raw_Parameter']}", expanded=False
            ):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**Generic Tag:** {row['Generic_Tag']}")
                    st.write(f"**UUID:** {row['UUID'] if row['UUID'] else 'N/A'}")
                    st.write(f"**UOM:** {row['UOM']}")
                    st.write(
                        f"**Metadata:** {row['Metadata'] if row['Metadata'] else 'N/A'}"
                    )

                with col2:
                    st.write(f"**Low-Low Limit:** {row['Low_Low_Limit']}")
                    st.write(f"**Low Limit:** {row['Low_Limit']}")
                    st.write(f"**High Limit:** {row['High_Limit']}")
                    st.write(f"**High-High Limit:** {row['High_High_Limit']}")

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{idx}"):
                        st.session_state.tag_entries.pop(idx)
                        st.rerun()

        # Finish button
        st.markdown("---")
        if st.button(
            "✅ Finish Configuration", type="primary", use_container_width=True
        ):
            # Save all tags to main dataframe
            new_tags_df = pd.DataFrame(st.session_state.tag_entries)
            st.session_state.tags_data = pd.concat(
                [st.session_state.tags_data, new_tags_df], ignore_index=True
            )
            # Clear tag entries after adding to prevent duplicates
            st.session_state.tag_entries = []
            st.session_state.page = "summary"
            st.rerun()
    else:
        st.info("No tags configured yet. Add your first tag above!")


def upload_generic_tags_screen():
    """Display upload page for generic tags mapping"""
    quick_actions_sidebar()

    # Track current page
    st.session_state.last_page = "upload"

    st.title("📤 Upload Generic Tags Mapping")

    if st.button("← Back to Summary"):
        st.session_state.page = "summary"
        st.rerun()

    st.markdown("---")

    st.info("💡 Upload a CSV or Excel file with 'Generic Tag' and 'Metadata' columns for a specific Industry and Equipment combination.")

    # Industry and Equipment selection
    col1, col2 = st.columns(2)

    with col1:
        # Get list of industries without emojis
        industries_clean = [ind.split(" ", 1)[1] for ind in INDUSTRIES]
        selected_industry = st.selectbox(
            "🏭 Select Industry *",
            [""] + industries_clean,
            key="upload_industry_select"
        )

    with col2:
        # Get existing equipment options from tags_data for selected industry
        if selected_industry and not st.session_state.tags_data.empty:
            equipment_options = sorted(
                st.session_state.tags_data[
                    st.session_state.tags_data["Industry"] == selected_industry
                ]["Equipment"].unique().tolist()
            )
        else:
            equipment_options = []

        # Allow both selecting existing or entering new equipment
        equipment_input_type = st.radio(
            "Equipment Input",
            ["Select Existing", "Enter New"],
            horizontal=True,
            key="upload_equipment_radio"
        )

        if equipment_input_type == "Select Existing" and equipment_options:
            selected_equipment = st.selectbox(
                "⚙️ Select Equipment *",
                [""] + equipment_options,
                key="upload_equipment_select"
            )
        else:
            selected_equipment = st.text_input(
                "⚙️ Enter Equipment Name *",
                key="upload_equipment_input"
            )

    st.markdown("---")

    # File upload section
    st.subheader("📁 Upload File")

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="File should contain at least 'Generic Tag' and 'Metadata' columns"
    )

    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")

        # Preview the file
        try:
            if uploaded_file.name.endswith('.csv'):
                df_preview = pd.read_csv(uploaded_file)
            else:
                df_preview = pd.read_excel(uploaded_file)

            st.subheader("📋 File Preview")
            st.dataframe(df_preview.head(10), use_container_width=True, hide_index=True)

            # Check if required columns exist
            required_columns = ['Generic Tag', 'Metadata']
            missing_columns = [col for col in required_columns if col not in df_preview.columns]

            if missing_columns:
                st.error(f"⚠️ Missing required columns: {', '.join(missing_columns)}")
                st.info(f"Available columns: {', '.join(df_preview.columns.tolist())}")
            else:
                st.success("✅ File contains all required columns!")

                # Upload button
                if selected_industry and selected_equipment:
                    if st.button("📤 Upload and Process", type="primary", use_container_width=True):
                        # Process the file and add to available_generic_tags
                        new_rows = []
                        for _, row in df_preview.iterrows():
                            generic_tag = row['Generic Tag']
                            metadata = row.get('Metadata', '')

                            # Generate UUID for this generic tag
                            tag_uuid = str(uuid.uuid4())

                            # Update generic tags mapping
                            update_generic_tags_mapping(
                                generic_tag,
                                selected_industry,
                                selected_equipment
                            )

                            # Add to generic tags list if not already present
                            if generic_tag not in st.session_state.generic_tags:
                                st.session_state.generic_tags.append(generic_tag)
                                st.session_state.generic_tags.sort()

                            # Create entry for available_generic_tags
                            new_entry = {
                                "Generic_Tag": generic_tag,
                                "UUID": tag_uuid,
                                "Metadata": metadata,
                                "Industry": selected_industry,
                                "Equipment": selected_equipment,
                            }
                            new_rows.append(new_entry)

                        # Add all new entries to available_generic_tags
                        if new_rows:
                            new_tags_df = pd.DataFrame(new_rows)
                            st.session_state.available_generic_tags = pd.concat(
                                [st.session_state.available_generic_tags, new_tags_df], ignore_index=True
                            )

                        st.success(f"✅ Successfully uploaded {len(df_preview)} generic tags for {selected_industry} - {selected_equipment}!")
                        st.balloons()

                        # Redirect to summary page after short delay
                        st.info("Redirecting to summary page...")
                        st.session_state.page = "summary"
                        st.rerun()
                else:
                    st.warning("⚠️ Please select both Industry and Equipment to proceed with upload")

        except Exception as e:
            st.error(f"⚠️ Error reading file: {str(e)}")
    else:
        st.info("📂 Please upload a file to continue")


def summary_screen():
    """Display final summary with all configured data"""
    quick_actions_sidebar()

    # Track current page
    st.session_state.last_page = "summary"

    st.title("📊 Configuration Summary")
    st.markdown("---")

    # Tabs for different dataframes
    tab1, tab2 = st.tabs(["📋 Tags Configured", "🏷️ Available Generic Tags with Metadata"])

    with tab1:
        # Display complete dataframe
        if not st.session_state.tags_data.empty:
            st.subheader("Complete Tags Configuration")

            # Ensure UUID column exists (for backward compatibility)
            if "UUID" not in st.session_state.tags_data.columns:
                st.session_state.tags_data.insert(8, "UUID", "")

            st.dataframe(
                st.session_state.tags_data, use_container_width=True, hide_index=True
            )

            # Export options
            st.markdown("---")
            st.subheader("💾 Export Tags Data")

            col1, col2, col3 = st.columns(3)

            with col1:
                csv = st.session_state.tags_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"tags_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with col2:
                excel_buffer = pd.ExcelWriter("tags_config.xlsx", engine="openpyxl")
                st.session_state.tags_data.to_excel(
                    excel_buffer, index=False, sheet_name="Tags"
                )
                excel_buffer.close()

                with open("tags_config.xlsx", "rb") as f:
                    st.download_button(
                        label="📥 Download Excel",
                        data=f,
                        file_name=f"tags_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

            with col3:
                json_data = st.session_state.tags_data.to_json(
                    orient="records", indent=2
                )
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"tags_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )
        else:
            st.info("No configuration data available yet.")

    with tab2:
        # Display Available Generic Tags with Metadata
        if not st.session_state.available_generic_tags.empty:
            st.subheader("Available Generic Tags by Industry & Equipment")

            # Filter section
            col1, col2 = st.columns(2)

            with col1:
                # Get all unique industries from available_generic_tags
                available_industries = sorted(
                    st.session_state.available_generic_tags["Industry"].unique().tolist()
                )
                selected_industry_filter = st.selectbox(
                    "🏭 Select Industry",
                    [""] + available_industries,
                    key="industry_filter_select",
                )

            with col2:
                # Get equipment options based on selected industry
                if selected_industry_filter:
                    equipment_options = sorted(
                        st.session_state.available_generic_tags[
                            st.session_state.available_generic_tags["Industry"]
                            == selected_industry_filter
                        ]["Equipment"]
                        .unique()
                        .tolist()
                    )
                else:
                    equipment_options = []

                selected_equipment_filter = st.selectbox(
                    "⚙️ Select Equipment",
                    [""] + equipment_options if equipment_options else [""],
                    key="equipment_filter_select",
                )

            st.markdown("---")

            # Display filtered results
            if selected_industry_filter and selected_equipment_filter:
                # Filter available_generic_tags based on selections
                filtered_data = st.session_state.available_generic_tags[
                    (st.session_state.available_generic_tags["Industry"] == selected_industry_filter)
                    & (
                        st.session_state.available_generic_tags["Equipment"]
                        == selected_equipment_filter
                    )
                ]

                if not filtered_data.empty:
                    # Create a dataframe with Generic_Tag, UUID, and Metadata columns
                    result_df = filtered_data[["Generic_Tag", "UUID", "Metadata"]].copy()

                    # Display the filtered dataframe
                    st.dataframe(result_df, use_container_width=True, hide_index=True)

                    # Export filtered data
                    st.markdown("---")
                    st.subheader("💾 Export Filtered Data")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        csv = result_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"generic_tags_{selected_industry_filter}_{selected_equipment_filter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )

                    with col2:
                        excel_buffer = pd.ExcelWriter(
                            "filtered_generic_tags.xlsx", engine="openpyxl"
                        )
                        result_df.to_excel(
                            excel_buffer, index=False, sheet_name="Generic Tags"
                        )
                        excel_buffer.close()

                        with open("filtered_generic_tags.xlsx", "rb") as f:
                            st.download_button(
                                label="📥 Download Excel",
                                data=f,
                                file_name=f"generic_tags_{selected_industry_filter}_{selected_equipment_filter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                            )

                    with col3:
                        json_data = result_df.to_json(orient="records", indent=2)
                        st.download_button(
                            label="📥 Download JSON",
                            data=json_data,
                            file_name=f"generic_tags_{selected_industry_filter}_{selected_equipment_filter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True,
                        )
                else:
                    st.warning(
                        f"⚠️ No tags found for {selected_industry_filter} - {selected_equipment_filter}"
                    )
            elif selected_industry_filter:
                st.info(
                    "💡 Please select an equipment to view generic tags and metadata"
                )
            else:
                st.info(
                    "💡 Please select an industry and equipment to view generic tags and metadata"
                )

            # Export Available Generic Tags
            st.markdown("---")
            st.subheader("💾 Export Available Generic Tags")

            col1, col2, col3 = st.columns(3)

            with col1:
                csv = st.session_state.available_generic_tags.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"available_generic_tags_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with col2:
                excel_buffer = pd.ExcelWriter(
                    "available_generic_tags.xlsx", engine="openpyxl"
                )
                st.session_state.available_generic_tags.to_excel(
                    excel_buffer, index=False, sheet_name="Generic Tags"
                )
                excel_buffer.close()

                with open("available_generic_tags.xlsx", "rb") as f:
                    st.download_button(
                        label="📥 Download Excel",
                        data=f,
                        file_name=f"available_generic_tags_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

            with col3:
                json_data = st.session_state.available_generic_tags.to_json(
                    orient="records", indent=2
                )
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"available_generic_tags_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )
        else:
            st.info(
                "No available generic tags data yet. Upload generic tags to build this dataset."
            )


# Main app logic
def main():
    if st.session_state.page == "welcome":
        welcome_screen()
    elif st.session_state.page == "hierarchy":
        plant_hierarchy_screen()
    elif st.session_state.page == "tags":
        tags_configuration_screen()
    elif st.session_state.page == "summary":
        summary_screen()
    elif st.session_state.page == "upload":
        upload_generic_tags_screen()


if __name__ == "__main__":
    main()
