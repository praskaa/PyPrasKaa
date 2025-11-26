# Wall Plan Generator - Complete Workflow Diagram

## 🎯 High-Level Process Flow

```mermaid
graph TD
    A[Start Wall Plan Generator] --> B[User Selects Walls]
    B --> C[Validate Wall Selection]
    C --> D{Valid Walls?}
    D -->|No| E[Show Error: No Walls Selected]
    D -->|Yes| F[Extract Wall Classifications]

    F --> G[Group Walls by Classification]
    G --> H[Show Classification Summary]
    H --> I[User Selects Target Levels]
    I --> J{Levels Selected?}
    J -->|No| K[Show Error: No Levels Selected]
    J -->|Yes| L[Validate Level Selection]

    L --> M{Valid Levels?}
    M -->|No| N[Show Error: Invalid Levels]
    M -->|Yes| O[Initialize Plan Generator]

    O --> P[Start Transaction]
    P --> Q[Initialize Progress Bar]
    Q --> R[For Each Classification]
    R --> S[For Each Target Level]
    S --> T[Calculate Wall Mid-Height]
    T --> U[Calculate Group Bounding Box]
    U --> V[Generate Unique View Name]
    V --> W[Create Plan View at Elevation]
    W --> X[Set View Crop Box]
    X --> Y[Apply View Template]
    Y --> Z[Record Result]
    Z --> AA{More Levels?}
    AA -->|Yes| S
    AA -->|No| BB{More Classifications?}
    BB -->|Yes| R
    BB -->|No| CC[Commit Transaction]

    CC --> DD[Display Results Table]
    DD --> EE[End]

    E --> EE
    K --> EE
    N --> EE
```

## 🔍 Detailed Component Workflow

### **1. Wall Selection & Validation Phase**

```mermaid
graph TD
    A[User Initiates Wall Selection] --> B[Create EF_SelectionFilter<br/>for Walls Category]
    B --> C[Show Selection Prompt<br/>'Select walls for plan generation']
    C --> D[User Selects Wall Elements]
    D --> E[Convert References to Elements]
    E --> F{Valid Selection?}
    F -->|Empty| G[Return Empty List]
    F -->|Has Elements| H[Validate Wall Types]
    H --> I{All Valid Walls?}
    I -->|No| J[Filter Invalid Elements<br/>Log Warnings]
    I -->|Yes| K[Return Valid Wall List]
    J --> K

    G --> L[Show Error Message]
    L --> M[Exit Script]
```

### **2. Classification Extraction Phase**

```mermaid
graph TD
    A[Receive Wall List] --> B[Initialize WallClassifier]
    B --> C[Set Classification Parameter<br/>'Wall Scheme Classification']
    C --> D[Initialize Empty Groups Dict]
    D --> E[For Each Wall in List]
    E --> F[Extract Parameter Value<br/>using logic-library]
    F --> G{Parameter Exists?}
    G -->|No| H[Log Unclassified Wall<br/>Skip to Next]
    G -->|Yes| I[Add Wall to Classification Group]
    I --> J{More Walls?}
    J -->|Yes| E
    J -->|No| K[Validate Groups]
    K --> L{Has Valid Groups?}
    L -->|No| M[Show Error: No Valid Classifications]
    L -->|Yes| N[Return Classification Groups]
    M --> O[Exit Script]
```

### **3. Level Selection Phase**

```mermaid
graph TD
    A[Initialize LevelSelector] --> B[Query All Levels from Document]
    B --> C[Create Level Display Dictionary<br/>Name + Elevation]
    C --> D[Show Multi-Select Dialog<br/>'Select target levels']
    D --> E[User Makes Selections]
    E --> F{Valid Selection?}
    F -->|Empty| G[Show Error: No Levels Selected]
    F -->|Has Levels| H[Validate Level Elevations]
    H --> I{Levels Too Close?}
    I -->|Yes| J[Show Warning: Duplicate Elevations]
    I -->|No| K[Return Selected Levels]
    J --> L[Allow Continue or Cancel]
    L --> M{Cancel?}
    M -->|Yes| N[Exit Script]
    M -->|No| K

    G --> N
```

### **4. Plan Generation Core Logic**

```mermaid
graph TD
    A[Start Generation Loop] --> B[For Each Classification Group]
    B --> C[For Each Target Level]
    C --> D[Extract Wall List from Group]
    D --> E[Calculate Representative Mid-Height<br/>from First Wall]
    E --> F[Calculate 2D Bounding Box<br/>for All Walls at Elevation]
    F --> G{Valid Bounding Box?}
    G -->|No| H[Log Error: Invalid Geometry<br/>Skip to Next]
    G -->|Yes| I[Generate View Name<br/>Type-Classification-Level]
    I --> J[Ensure Name Uniqueness]
    J --> K[Find/Create Level at Target Elevation]
    K --> L[Create Plan View<br/>ViewPlan.Create]
    L --> M{View Created Successfully?}
    M -->|No| N[Log Error: View Creation Failed]
    M -->|Yes| O[Set View Crop Box<br/>Focus on Wall Group]
    O --> P[Apply View Template<br/>if specified]
    P --> Q[Record Success Result]
    Q --> R{More Levels?}
    R -->|Yes| C
    R -->|No| S{More Classifications?}
    S -->|Yes| B
    S -->|No| T[Return All Results]

    H --> R
    N --> R
```

### **5. Mid-Height Calculation Algorithm**

```mermaid
graph TD
    A[Receive Wall Element] --> B[Get Wall Base Constraint Level]
    B --> C{Level Found?}
    C -->|No| D[Use Wall Bounding Box Center]
    C -->|Yes| E[Get Base Level Elevation]
    E --> F[Get Wall Height Parameter<br/>WALL_USER_HEIGHT_PARAM]
    F --> G{Height Available?}
    G -->|No| D
    G -->|Yes| H[Calculate Mid-Height<br/>base_elevation + height/2]
    H --> I[Return Mid-Height Elevation]

    D --> J[Get Wall Bounding Box]
    J --> K[Calculate Center Z Coordinate<br/>Min.Z + Max.Z / 2]
    K --> I
```

### **6. Bounding Box Calculation Algorithm**

```mermaid
graph TD
    A[Receive Wall List + Target Elevation] --> B[Initialize Bounding Box<br/>from First Wall]
    B --> C[Calculate First Wall 2D Footprint<br/>at Target Elevation]
    C --> D{Valid Footprint?}
    D -->|No| E[Skip Wall<br/>Continue to Next]
    D -->|Yes| F[Set Initial BB Bounds<br/>min_x, max_x, min_y, max_y]
    F --> G[For Each Remaining Wall]
    G --> H[Calculate Wall 2D Footprint<br/>at Target Elevation]
    H --> I{Valid Footprint?}
    I -->|No| J[Skip Wall]
    I -->|Yes| K[Expand Bounding Box<br/>Update min/max coordinates]
    K --> L{More Walls?}
    L -->|Yes| G
    L -->|No| M[Add Padding to BB<br/>10% of dimensions]
    M --> N[Return Final Bounding Box<br/>min_x, max_x, min_y, max_y]

    E --> L
    J --> L
```

### **7. Results Processing & Display**

```mermaid
graph TD
    A[Receive Generation Results] --> B[Initialize Output Display]
    B --> C[Calculate Statistics<br/>Success/Failed Counts]
    C --> D[Create Table Data Structure]
    D --> E[For Each Result]
    E --> F[Format Status Icon<br/>✅ Success / ❌ Failed]
    F --> G[Create View Link<br/>if view exists]
    G --> H[Add Row to Table<br/>Classification, Level, Count, Status, Link]
    H --> I{More Results?}
    I -->|Yes| E
    I -->|No| J[Display Summary Header<br/>Total Success/Failed]
    J --> K[Display Results Table<br/>with Interactive Links]
    K --> L[End Display Process]
```

## 🔄 Error Handling Flow

```mermaid
graph TD
    A[Error Occurs] --> B{Error Type?}
    B -->|Parameter Missing| C[Log Warning<br/>Continue Processing]
    B -->|Geometry Invalid| D[Log Warning<br/>Skip Wall/Combination]
    B -->|View Creation Failed| E[Log Error<br/>Record Failed Result]
    B -->|Transaction Failed| F[Rollback Transaction<br/>Show Critical Error]
    B -->|User Cancelled| G[Graceful Exit<br/>Show Cancelled Message]

    C --> H[Continue Loop]
    D --> H
    E --> H
    F --> I[Exit Script]
    G --> I
```

## 📊 Data Flow Architecture

```mermaid
graph TD
    subgraph "Input Data"
        W[Walls List<br/>Element References]
        L[Levels List<br/>Level Objects]
        P[Parameters<br/>Classification Values]
    end

    subgraph "Processing Engine"
        WC[WallClassifier<br/>Groups by Parameter]
        WPG[WallPlanGenerator<br/>Creates Views]
        LS[LevelSelector<br/>Validates Levels]
    end

    subgraph "Output Data"
        V[Views<br/>Plan View Objects]
        R[Results<br/>Success/Failure Data]
        T[Table<br/>Display Data]
    end

    W --> WC
    P --> WC
    WC --> WPG
    L --> LS
    LS --> WPG
    WPG --> V
    WPG --> R
    R --> T
```

## 🎨 User Experience Flow

```mermaid
graph TD
    A[User Clicks Tool] --> B[Wall Selection Dialog<br/>'Select walls and click Finish']
    B --> C[Processing Indicator<br/>'Extracting classifications...']
    C --> D[Classification Summary<br/>'Found 3 groups: W5(5), W10(3), W15(7)']
    D --> E[Level Selection Dialog<br/>Multi-select with elevations]
    E --> F[Confirmation Dialog<br/>'Generate 9 plan views?']
    F --> G[Progress Bar<br/>'Creating plan for W5 at Level 1...']
    G --> H[Results Table<br/>Interactive view links]
    H --> I[Completion Message<br/>'9 views created successfully']
```

## 🔧 Technical Component Interactions

```mermaid
graph TD
    subgraph "UI Layer"
        SD[Selection Dialog]
        LD[Level Dialog]
        PB[Progress Bar]
        RT[Results Table]
    end

    subgraph "Business Logic Layer"
        WF[Wall Filtering]
        CE[Classification Extraction]
        VG[View Generation]
        VC[View Cropping]
    end

    subgraph "Data Access Layer"
        PE[Parameter Extraction<br/>logic-library]
        VE[View Creation<br/>Revit API]
        LE[Level Management<br/>Revit API]
    end

    subgraph "Infrastructure Layer"
        TM[Transaction Management]
        EH[Error Handling]
        NM[Naming Management]
    end

    SD --> WF
    WF --> CE
    CE --> LD
    LD --> VG
    VG --> VC
    VC --> PB
    PB --> RT

    CE --> PE
    VG --> VE
    VG --> LE

    VG --> TM
    CE --> EH
    VG --> EH
    VG --> NM
```

---

*This comprehensive workflow diagram shows the complete Wall Plan Generator process from user interaction to final results display, including error handling and data flow architecture.*