# Created csv file successfully.

![csv_file](screenshots/csv_created.png)

# (The "Actionable" View)

![AfterusingRUL](screenshots/Actionable.png)

## 1. The Actionable View (Prioritization Tool)

By zooming in on the health score axis (excluding zero) and applying conditional coloring based on failure probability, the visualization transforms from a simple list into a Decision Support System.

Core Insight: This view explicitly identifies who to fix and when.

Health vs. Risk Divergence: The bar length represents the current "Component Health Score," while the color represents "Failure Probability."

The Trend: Certain units show a decent health score (long bars) but are colored dark red. This indicates that while current performance is acceptable, the predictive model has detected patterns (vibrations, heat, or pressure sensor anomalies) suggesting a rapid descent toward failure.

Operational Countdown (RUL): The numeric labels at the end of the bars (e.g., $181$, $170$) represent the Remaining Useful Life (RUL).

Example: Unit 69 serves as a critical data point; it may still show a high health score, but its high-risk color combined with the RUL tells maintenance crews exactly how many flight cycles remain before the engine must be pulled from service.

# The "Comparison" View

![comparisonimageAfterfirststep](screenshots/step1.png)

## 2. The Fleet Overview (Comparison View)

This version maintains a zero-based axis and applies initial color gradients to provide a high-level "pulse" of the entire operation.

Core Insight: This view highlights fleet consistency and stability.

Uniformity: The relative equality in bar lengths indicates that the fleet is currently well-managed, with no engines in a state of "total collapse" or immediate structural failure.

The Visualization Challenge (The Nuance):

Scale: When the axis starts at zero, the difference between a $0.55$ and a $0.58$ health score appears negligible to the human eye.

Critical Thresholds: In aerospace engineering, that $0.03$ difference is mathematically massive, representing potentially dozens of flight hours or specific component degradation. This view is excellent for reporting general fleet availability but less effective for tactical maintenance scheduling.

## Key Technical Takeaways

Predictive Coloring: Moving from static blue to a Red-Green diverging palette based on AVG(Failure Probability) allows for instant visual triage.

Axis Optimization: Excluding zero is essential for high-precision sensor data where small variations in decimals translate to significant physical wear.

Data Integration: Combining Health Score (Current State), Failure Prob (Future Risk), and RUL (Timeline) into a single bar chart creates a multi-dimensional scorecard.

# Maintanence Schedule Heat map

![maintanencescheduleheatmap](Screenshots/MAINTANENCE.png)

This heatmap visualizes the degradation of jet engine health as they approach their end-of-life (EOL). The X-axis represents the "Countdown" (Cycles Remaining), while the Y-axis sorts the fleet by their remaining useful life.

## Key Insights:

The Critical Handoff: The transition from Green to Red between the 51-100 and 31-50 buckets identifies the "Threshold of Concern." This is the optimal window for logistics teams to ensure spare parts are on-site.

Degradation Velocity: By observing the intensity of the red in the 0-10 column, we can differentiate between engines that are failing "gracefully" versus those experiencing "rapid collapse."

Operational Planning: This view allows for staggered maintenance. Instead of all engines coming in at once, we can see the spread of the fleet's remaining life, preventing hangar bottlenecks.

## Visual Logic:

Sorting: Units are sorted by AVG(Health Rul) Ascending, placing the most urgent engines at the top.

Color Palette: A Red-Green Diverging palette is used, where Red indicates a critical Component Health Score, mapping perfectly to the urgency of low "Cycles Remaining."
