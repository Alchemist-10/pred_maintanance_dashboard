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

