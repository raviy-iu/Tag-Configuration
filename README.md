# Manufacturing Tag Configuration Dashboard

A comprehensive Streamlit dashboard for configuring real-time streaming tags for various manufacturing industries. This tool allows users to define plant hierarchies, configure tags with detailed parameters, and upload/manage generic tag mappings.

## Features

### 1. Welcome Screen
- Greeting message: "Hey, Infinitian! Welcome"
- Industry cards for: Cement, Aluminium, Steel, Tyre, Paper & Pulp, Oil & Gas, and Automobile
- Select an industry to begin configuration

### 2. Plant Hierarchy Setup
- **Flexible Input Options**: Choose between "Select Existing" or "Add New" for each level
- **Hierarchical Fields** (all required):
  - **Plant Name**: Select existing or create new plant
  - **Area**: Select existing or create new area (filtered by plant)
  - **Equipment**: Select existing or create new equipment (filtered by plant & area)
  - **Asset**: Select existing or create new asset (filtered by plant, area & equipment)
- **Input Validation**: Hierarchy names must contain only uppercase letters (A-Z), numbers (0-9), and underscores (_)
- **Visual Hierarchy Tree**: Right panel displays existing hierarchies in tree format with quick-select buttons
- **Smart Filtering**: Dropdown options are filtered based on parent selections
- "Define Tags & Details" button activates when all fields are filled correctly

### 3. Tags & Details Configuration
- **Breadcrumb Navigation**: Shows current hierarchy path (Plant → Area → Equipment → Asset)
- **Smart Generic Tag Suggestions**: System suggests available generic tags based on uploaded data for the current industry and equipment
- **Two-Section Layout** for efficient tag configuration:

#### Section 1: Basic Tag Information
- **Tag Fields** (Column 1):
  - DCS Tag * (required)
  - Raw Parameter * (required)
  - Generic Tag * (dropdown with custom "+ Add New" option and intelligent suggestions)
  - UOM - Unit of Measurement * (dropdown with custom "+ Add New" option)

- **Limit Fields** (Column 2):
  - Low-Low Limit (numeric)
  - Low Limit (numeric)
  - High Limit (numeric)
  - High-High Limit (numeric)

- **Submit Button**: Validates all required fields and generates UUID and metadata

#### Section 2: Generated Information (Shown After Submit)
- **UUID Field**: Auto-generated unique identifier for each generic tag (read-only)
  - Automatically created when submitting a new generic tag
  - Retrieved from storage when selecting an existing generic tag
  - Persisted in "Available Generic Tags with Metadata"
- **Metadata Field**: Editable text area
  - Auto-populated from available data when selecting existing generic tags
  - Can be manually edited before adding the tag
  - Saved to "Available Generic Tags with Metadata" when tag is added

#### Tag Management Features
- **Clear All Button** (🗑️): Resets entire form to initial state, clears all fields and hides Section 2
- **Add Tag Button**: Saves complete tag configuration including UUID and metadata
- **Section 2 Persistence**: Remains visible after adding a tag for efficient multi-tag entry
- **View Configured Tags**: Expandable cards display all tag details including UUID
- **Delete Functionality**: Remove individual configured tags
- **Generic Tags Mapping**: Automatically tracks which generic tags are used with which equipment and industry with usage counts

### 4. Upload Generic Tags
- **File Upload**: Upload CSV or Excel files with "Generic Tag" and "Metadata" columns
- **Industry & Equipment Mapping**: Associate uploaded tags with specific industry and equipment combinations
- **Flexible Equipment Input**: Select existing equipment or enter new equipment name
- **File Preview**: Preview uploaded data before processing
- **Validation**: System checks for required columns before processing
- **UUID Auto-Generation**: System automatically generates unique UUIDs for each uploaded generic tag
- **Automatic Updates**: Uploaded tags with UUIDs and metadata are added to "Available Generic Tags with Metadata" dataframe
- **Intelligent Storage**: Each generic tag is stored with its UUID, metadata, industry, and equipment association

### 5. Summary Screen
- **Dual Tab View**:
  - **Tags Configured Tab**: All configured tags with full hierarchy, UUID, and parameter details
  - **Available Generic Tags with Metadata Tab**: Filterable view showing Generic Tag, UUID, and Metadata by industry and equipment
- **Advanced Filtering**: Filter available generic tags by industry and equipment to see relevant tags with their UUIDs
- **Statistics Dashboard** (in Quick Actions sidebar):
  - Total Industries
  - Total Plants
  - Total Tags
  - Generic Tags count
- **Export Options** for all dataframes (includes UUID column):
  - CSV format
  - Excel format
  - JSON format
  - Timestamped filenames for version tracking
- **Comprehensive Data View**: All exported data includes UUID for traceability and data integrity

### 6. Quick Actions Sidebar
- **Always Available Navigation**:
  - Home (Welcome screen)
  - Plant Hierarchy
  - Configure Tags
  - View Summary
  - Upload Generic Tags
- **Real-time Statistics**: Shows key metrics when data is available

## Key Features

### UUID (Unique Identifier) System
Each generic tag is assigned a unique UUID that provides:
- **Traceability**: Track each generic tag across the system
- **Data Integrity**: Prevent duplicate entries and ensure consistency
- **Auto-Generation**: UUIDs are automatically created when:
  - Uploading generic tags via CSV/Excel files
  - Creating new generic tags in the Configure Tags page
  - Submitting Section 1 of the tag configuration form
- **Persistence**: UUIDs are stored in "Available Generic Tags with Metadata" and linked to industry-equipment combinations
- **Reusability**: Selecting an existing generic tag automatically retrieves its UUID and metadata

### Data Persistence & Management
- **Available Generic Tags with Metadata**: Central repository storing all generic tags with their UUIDs, metadata, industry, and equipment associations
- **Smart Retrieval**: System automatically finds and displays relevant generic tags based on current industry and equipment selection
- **Metadata Updates**: When adding a tag, any edited metadata is saved back to the repository
- **Export Capability**: All data exports include UUID for complete traceability

## Installation

### Prerequisites
- Python 3.8 or higher
- pip or uv package manager

### Setup Instructions

#### Option 1: Using pip
```bash
pip install streamlit pandas openpyxl
```

#### Option 2: Using uv (if pyproject.toml exists)
```bash
uv sync
```

## Usage

### Running the Application

```bash
streamlit run manufacturing_tag_config.py
```

The application will automatically open in your default web browser at `http://localhost:8501`

### Workflow Steps

1. **Select Industry**: Choose from 7 manufacturing industries on the welcome screen
2. **Define Hierarchy**: Set up Plant → Area → Equipment → Asset structure
   - Use "Select Existing" to reuse previously entered values
   - Use "Add New" to create new hierarchy entries
   - Quick-select from the visual tree on the right panel
3. **Upload Generic Tags** (Optional): Upload CSV/Excel files with predefined generic tags and metadata
   - System auto-generates UUIDs for each generic tag
   - Tags are stored with industry-equipment association
4. **Configure Tags**: Two-section workflow for efficient tag entry

   **Section 1 - Basic Information:**
   - Enter DCS Tag, Raw Parameter, Generic Tag, and UOM
   - Set all four limit values (Low-Low, Low, High, High-High)
   - Click **Submit** button to proceed

   **Section 2 - Generated Information:**
   - Review auto-generated UUID (unique identifier)
   - Review/edit auto-populated metadata
   - Click **Add Tag** to save complete configuration

   **Additional Features:**
   - Use **Clear All** button to reset the entire form
   - Section 2 remains visible after adding tags for quick multi-tag entry
   - New generic tags and their metadata are automatically saved to the system

5. **Finish & Export**: Review all configurations in Summary screen
   - View configured tags with UUIDs
   - Filter and view available generic tags with metadata
   - Export in CSV, Excel, or JSON format (all include UUIDs)