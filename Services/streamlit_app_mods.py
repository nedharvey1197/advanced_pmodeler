# Streamlit App Integration

Here's the code to add to your Streamlit app to integrate the new service modules. These sections should be added to your existing `app.py` file.

## 1. Add Imports

Add these imports at the top of your file:

```python
# Add these imports to the top of your file
from manufacturing_model.services.sales_service import SalesService
from manufacturing_model.services.ga_service import GeneralAdministrativeService
from manufacturing_model.services.assumptions_service import AssumptionsService
```

## 2. Update Sidebar Navigation

Update your `render_sidebar` function to include the new sections:

```python
def render_sidebar():
    st.sidebar.title("Manufacturing Expansion Planner")
    
    # Navigation
    st.sidebar.header("Navigation")
    return st.sidebar.radio(
        "Select Section", 
        [
            "Dashboard", 
            "Manage Scenarios", 
            "Equipment Management", 
            "Product Management", 
            "Sales Planning",     # New section
            "G&A Planning",       # New section
            "Financial Analysis", 
            "Capacity Planning",
            "Assumptions"         # New section
        ]
    )
```

## 3. Add New Render Functions

Add these new functions to render the additional sections:

```python
def render_sales_planning(active_scenario_id):
    st.title("Sales Planning")
    
    if active_scenario_id is None:
        st.info("Please select or create a scenario first.")
        return
    
    # Get active scenario
    scenario = get_scenario(active_scenario_id)
    st.subheader(f"Sales Planning for: {scenario['name']}")
    
    # Get products for this scenario
    products_df = get_products(active_scenario_id)
    
    if products_df.empty:
        st.warning("No products added yet. Please add products first.")
        return
    
    # Year range for planning
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("Start Year", min_value=0, value=0)
    with col2:
        end_year = st.number_input("End Year", min_value=start_year, value=5)
    
    # Market-driven vs. operations-driven selection
    st.subheader("Sales Approach by Year")
    
    # Create a dictionary to store approach by year
    market_driven = {}
    years = list(range(start_year, end_year + 1))
    
    # Create a form for approach selection
    with st.form("sales_approach_form"):
        st.write("Select sales approach for each year:")
        
        # Default to operations-driven in years 0-1, transitioning to market-driven by year 3
        for year in years:
            default_market = year >= start_year + 2
            market_driven[year] = st.checkbox(
                f"Year {year}: Market-Driven (vs. Operations-Driven)", 
                value=default_market,
                key=f"market_driven_{year}"
            )
        
        # Submit button
        submitted = st.form_submit_button("Update Sales Approach")
    
    # Sales pipeline parameters
    st.subheader("Sales Pipeline Parameters")
    
    with st.form("sales_pipeline_form"):
        col1, col2 = st.columns(2)
        with col1:
            prospect_to_lead = st.slider("Prospect to Lead Conversion (%)", min_value=1.0, max_value=30.0, value=10.0) / 100
            lead_to_opportunity = st.slider("Lead to Opportunity Conversion (%)", min_value=5.0, max_value=50.0, value=25.0) / 100
        
        with col2:
            opportunity_to_sale = st.slider("Opportunity to Sale Conversion (%)", min_value=5.0, max_value=50.0, value=20.0) / 100
            avg_deal_size = st.number_input("Average Deal Size ($)", min_value=1000.0, value=50000.0)
        
        # Submit button
        pipeline_submitted = st.form_submit_button("Update Pipeline Parameters")
    
    # Sales team parameters
    st.subheader("Sales Team Parameters")
    
    with st.form("sales_team_form"):
        col1, col2 = st.columns(2)
        with col1:
            revenue_per_rep = st.number_input("Annual Revenue per Sales Rep ($)", min_value=100000.0, value=1000000.0)
            leads_per_marketing = st.number_input("Annual Leads per Marketing Staff", min_value=100, value=500)
        
        with col2:
            sales_rep_cost = st.number_input("Fully Loaded Cost per Sales Rep ($)", min_value=50000.0, value=120000.0)
            marketing_staff_cost = st.number_input("Fully Loaded Cost per Marketing Staff ($)", min_value=50000.0, value=90000.0)
        
        # Submit button
        team_submitted = st.form_submit_button("Update Team Parameters")
    
    # Run sales forecast calculation
    if st.button("Calculate Sales Forecast"):
        with st.spinner("Calculating sales forecast..."):
            # Here we would call the SalesService
            # For now, we'll simulate the response
            
            # Initialize SalesService
            session = get_session()
            sales_service = SalesService(session)
            
            # Convert market_driven dict to list for the service function
            market_driven_list = [market_driven[year] for year in years]
            
            # Calculate sales forecast
            forecast = sales_service.calculate_sales_forecast(
                active_scenario_id, start_year, end_year, market_driven_list
            )
            
            if "error" in forecast:
                st.error(forecast["error"])
            else:
                # Store in session state to display results
                st.session_state.sales_forecast = forecast
                st.success("Sales forecast calculated!")
                st.experimental_rerun()
    
    # Display sales forecast results if available
    if hasattr(st.session_state, 'sales_forecast'):
        forecast = st.session_state.sales_forecast
        
        # Display revenue forecast
        st.subheader("Revenue Forecast")
        
        # Create dataframe for revenue
        revenue_data = []
        for year in years:
            if year in forecast["yearly_data"]:
                data = forecast["yearly_data"][year]
                revenue_data.append({
                    "Year": year,
                    "Total Revenue": data["total_revenue"],
                    "Sales Approach": "Market-Driven" if market_driven[year] else "Operations-Driven"
                })
        
        if revenue_data:
            revenue_df = pd.DataFrame(revenue_data)
            st.dataframe(revenue_df.style.format({
                "Total Revenue": "${:,.0f}"
            }))
            
            # Plot revenue forecast
            fig, ax = plt.subplots(figsize=(10, 6))
            
            market_years = [row["Year"] for row in revenue_data if row["Sales Approach"] == "Market-Driven"]
            market_revenue = [row["Total Revenue"] for row in revenue_data if row["Sales Approach"] == "Market-Driven"]
            
            ops_years = [row["Year"] for row in revenue_data if row["Sales Approach"] == "Operations-Driven"]
            ops_revenue = [row["Total Revenue"] for row in revenue_data if row["Sales Approach"] == "Operations-Driven"]
            
            if market_years:
                ax.bar(market_years, market_revenue, alpha=0.7, label="Market-Driven", color="blue")
            
            if ops_years:
                ax.bar(ops_years, ops_revenue, alpha=0.7, label="Operations-Driven", color="green")
            
            ax.set_xlabel("Year")
            ax.set_ylabel("Revenue ($)")
            ax.set_title("Revenue Forecast by Year and Approach")
            ax.legend()
            
            st.pyplot(fig)
            plt.close()
        
        # Display sales pipeline
        st.subheader("Sales Pipeline Analysis")
        
        for year in years:
            if year in forecast["sales_pipeline"]:
                pipeline = forecast["sales_pipeline"][year]
                
                with st.expander(f"Year {year} Pipeline"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Prospects Needed", f"{pipeline['prospects_needed']:,.0f}")
                        st.metric("Leads Needed", f"{pipeline['leads_needed']:,.0f}")
                    
                    with col2:
                        st.metric("Opportunities Needed", f"{pipeline['opportunities_needed']:,.0f}")
                        st.metric("Deals Needed", f"{pipeline['deals_needed']:,.0f}")
                    
                    with col3:
                        st.metric("Avg Deal Size", f"${pipeline['avg_deal_size']:,.0f}")
                        st.metric("Sales Cycle", f"{pipeline['sales_cycle_days']} days")
        
        # Display staffing requirements
        st.subheader("Sales & Marketing Staff Requirements")
        
        # Create dataframe for staffing
        staff_data = []
        for year in years:
            if year in forecast["staff_requirements"]:
                staff = forecast["staff_requirements"][year]
                staff_data.append({
                    "Year": year,
                    "Sales Reps": staff["sales_representatives"],
                    "Sales Managers": staff["sales_managers"],
                    "Marketing Staff": staff["marketing_staff"],
                    "Sales Operations": staff["sales_operations"],
                    "Total Headcount": staff["total_headcount"],
                    "Total Cost": staff["total_cost"]
                })
        
        if staff_data:
            staff_df = pd.DataFrame(staff_data)
            st.dataframe(staff_df.style.format({
                "Sales Reps": "{:.1f}",
                "Sales Managers": "{:.1f}",
                "Marketing Staff": "{:.1f}",
                "Sales Operations": "{:.1f}",
                "Total Headcount": "{:.1f}",
                "Total Cost": "${:,.0f}"
            }))
            
            # Plot staffing trend
            fig, ax = plt.subplots(figsize=(10, 6))
            
            years = [row["Year"] for row in staff_data]
            sales_reps = [row["Sales Reps"] for row in staff_data]
            marketing = [row["Marketing Staff"] for row in staff_data]
            managers = [row["Sales Managers"] for row in staff_data]
            ops = [row["Sales Operations"] for row in staff_data]
            
            ax.stackplot(years, 
                       sales_reps, marketing, managers, ops,
                       labels=["Sales Reps", "Marketing", "Managers", "Operations"],
                       alpha=0.7)
            
            ax.set_xlabel("Year")
            ax.set_ylabel("Headcount")
            ax.set_title("Sales & Marketing Headcount by Year")
            ax.legend(loc="upper left")
            
            st.pyplot(fig)
            plt.close()
        
        # Display channel distribution
        st.subheader("Sales Channel Distribution")
        
        # Create dataframe for channel distribution
        channel_data = []
        for year in years:
            if year in forecast["channel_distribution"]:
                channels = forecast["channel_distribution"][year]
                channel_data.append({
                    "Year": year,
                    "Direct Sales": channels["direct_sales"]["revenue"],
                    "Channel Partners": channels["channel_partners"]["revenue"],
                    "Online": channels["online"]["revenue"]
                })
        
        if channel_data:
            channel_df = pd.DataFrame(channel_data)
            st.dataframe(channel_df.style.format({
                "Direct Sales": "${:,.0f}",
                "Channel Partners": "${:,.0f}",
                "Online": "${:,.0f}"
            }))
            
            # Plot channel distribution
            fig, ax = plt.subplots(figsize=(10, 6))
            
            years = [row["Year"] for row in channel_data]
            direct = [row["Direct Sales"] for row in channel_data]
            partners = [row["Channel Partners"] for row in channel_data]
            online = [row["Online"] for row in channel_data]
            
            ax.stackplot(years, 
                       direct, partners, online,
                       labels=["Direct Sales", "Channel Partners", "Online"],
                       alpha=0.7)
            
            ax.set_xlabel("Year")
            ax.set_ylabel("Revenue ($)")
            ax.set_title("Revenue by Sales Channel")
            ax.legend(loc="upper left")
            
            st.pyplot(fig)
            plt.close()

def render_ga_planning(active_scenario_id):
    st.title("G&A Planning")
    
    if active_scenario_id is None:
        st.info("Please select or create a scenario first.")
        return
    
    # Get active scenario
    scenario = get_scenario(active_scenario_id)
    st.subheader(f"G&A Planning for: {scenario['name']}")
    
    # Year range for planning
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("Start Year", min_value=0, value=0)
    with col2:
        end_year = st.number_input("End Year", min_value=start_year, value=5)
    
    # G&A parameters
    st.subheader("G&A Parameters")
    
    with st.form("ga_parameters_form"):
        col1, col2 = st.columns(2)
        with col1:
            executive_percent = st.slider("Executive Team (% of Revenue)", min_value=1.0, max_value=10.0, value=3.0)
            hr_per_employee = st.number_input("HR Cost per Employee ($)", min_value=500.0, value=2000.0)
        
        with col2:
            finance_percent = st.slider("Finance/Accounting (% of Revenue)", min_value=1.0, max_value=5.0, value=3.0)
            legal_percent = st.slider("Legal (% of Revenue)", min_value=0.5, max_value=3.0, value=2.0)
        
        # Submit button
        ga_submitted = st.form_submit_button("Update G&A Parameters")
    
    # Run G&A calculation
    if st.button("Calculate G&A Expenses"):
        with st.spinner("Calculating G&A expenses..."):
            # Initialize G&A Service
            session = get_session()
            ga_service = GeneralAdministrativeService(session)
            
            # Calculate G&A expenses
            ga_expenses = ga_service.calculate_ga_expenses(
                active_scenario_id, start_year, end_year
            )
            
            if "error" in ga_expenses:
                st.error(ga_expenses["error"])
            else:
                # Store in session state to display results
                st.session_state.ga_expenses = ga_expenses
                st.success("G&A expenses calculated!")
                st.experimental_rerun()
    
    # Display G&A results if available
    if hasattr(st.session_state, 'ga_expenses'):
        expenses = st.session_state.ga_expenses
        
        # Display total G&A expenses
        st.subheader("G&A Expenses")
        
        # Create dataframe for total expenses
        ga_data = []
        years = list(range(start_year, end_year + 1))
        
        for year in years:
            if year in expenses["yearly_data"]:
                data = expenses["yearly_data"][year]
                ga_data.append({
                    "Year": year,
                    "Total G&A": data["total"],
                    "% of Revenue": data["percent_of_revenue"],
                    "G&A Headcount": data["headcount"]
                })
        
        if ga_data:
            ga_df = pd.DataFrame(ga_data)
            st.dataframe(ga_df.style.format({
                "Total G&A": "${:,.0f}",
                "% of Revenue": "{:.1f}%",
                "G&A Headcount": "{:.1f}"
            }))
            
            # Plot G&A expenses
            fig, ax1 = plt.subplots(figsize=(10, 6))
            
            years = [row["Year"] for row in ga_data]
            total_ga = [row["Total G&A"] for row in ga_data]
            
            ax1.bar(years, total_ga, alpha=0.7, color="purple")
            ax1.set_xlabel("Year")
            ax1.set_ylabel("G&A Expenses ($)")
            
            # Add secondary axis for percentage
            ax2 = ax1.twinx()
            pct_revenue = [row["% of Revenue"] for row in ga_data]
            ax2.plot(years, pct_revenue, color="red", marker="o", linestyle="-", linewidth=2)
            ax2.set_ylabel("% of Revenue")
            
            plt.title("G&A Expenses by Year")
            
            st.pyplot(fig)
            plt.close()
        
        # Display G&A by category
        st.subheader("G&A by Category")
        
        # Create dataframe for G&A categories
        categories = set()
        for year_data in expenses["yearly_data"].values():
            categories.update(year_data["categories"].keys())
        
        # Sort categories
        categories = sorted(categories)
        
        # Create data for each category
        category_data = []
        for category in categories:
            row = {"Category": category.replace("_", " ").title()}
            
            for year in years:
                if year in expenses["yearly_data"]:
                    row[f"Year {year}"] = expenses["yearly_data"][year]["categories"].get(category, 0)
            
            category_data.append(row)
        
        if category_data:
            cat_df = pd.DataFrame(category_data)
            
            # Format columns for display
            format_dict = {f"Year {year}": "${:,.0f}" for year in years}
            st.dataframe(cat_df.style.format(format_dict))
            
            # Plot G&A by category
            fig, ax = plt.subplots(figsize=(12, 8))
            
            bottom = np.zeros(len(years))
            
            for category in categories:
                values = [expenses["yearly_data"].get(year, {}).get("categories", {}).get(category, 0) for year in years]
                ax.bar(years, values, bottom=bottom, label=category.replace("_", " ").title(), alpha=0.7)
                bottom += np.array(values)
            
            ax.set_xlabel("Year")
            ax.set_ylabel("Expenses ($)")
            ax.set_title("G&A Expenses by Category")
            ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        
        # Display headcount planning
        st.subheader("G&A Headcount Planning")
        
        # Plot headcount
        fig, ax = plt.subplots(figsize=(10, 6))
        
        years = [row["Year"] for row in ga_data]
        headcount = [row["G&A Headcount"] for row in ga_data]
        
        ax.plot(years, headcount, marker="o", linestyle="-", linewidth=2, color="green")
        ax.set_xlabel("Year")
        ax.set_ylabel("G&A Headcount")
        ax.set_title("G&A Headcount by Year")
        
        # Add labels to points
        for i, txt in enumerate(headcount):
            ax.annotate(f"{txt:.1f}", (years[i], headcount[i]), 
                       textcoords="offset points", xytext=(0, 10), ha='center')
        
        st.pyplot(fig)
        plt.close()

def render_assumptions(active_scenario_id):
    st.title("Scenario Assumptions")
    
    if active_scenario_id is None:
        st.info("Please select or create a scenario first.")
        return
    
    # Get active scenario
    scenario = get_scenario(active_scenario_id)
    st.subheader(f"Assumptions for: {scenario['name']}")
    
    # Initialize Assumptions Service
    session = get_session()
    assumptions_service = AssumptionsService(session)
    
    # Get all assumptions for this scenario
    all_assumptions = assumptions_service.get_scenario_assumptions(active_scenario_id)
    
    if "error" in all_assumptions:
        st.error(all_assumptions["error"])
        return
    
    # Get industry standards for comparison
    industry_standards = assumptions_service.get_industry_standards()
    
    # Display tabs for different assumption categories
    tabs = st.tabs(["Financial", "Operations", "Sales", "G&A", "Outsourcing"])
    
    # Financial assumptions
    with tabs[0]:
        st.subheader("Financial Assumptions")
        
        financial_assumptions = all_assumptions.get("financial", {})
        
        if financial_assumptions:
            # Create a dataframe with comparison to industry standards
            financial_data = []
            
            for param, value in financial_assumptions.items():
                # Skip derived fields
                if "_standard" in param or "_min" in param or "_max" in param or "_deviation" in param:
                    continue
                
                row = {
                    "Parameter": param.replace("_", " ").title(),
                    "Current Value": value
                }
                
                # Add standard values if available
                std_value = financial_assumptions.get(f"{param}_standard")
                if std_value is not None:
                    row["Industry Standard"] = std_value
                    
                    min_value = financial_assumptions.get(f"{param}_min")
                    max_value = financial_assumptions.get(f"{param}_max")
                    if min_value is not None and max_value is not None:
                        row["Min"] = min_value
                        row["Max"] = max_value
                    
                    deviation = financial_assumptions.get(f"{param}_deviation")
                    if deviation is not None:
                        row["Deviation (%)"] = deviation
                
                financial_data.append(row)
            
            if financial_data:
                fin_df = pd.DataFrame(financial_data)
                
                # Format columns
                format_dict = {}
                if "Current Value" in fin_df.columns:
                    format_dict["Current Value"] = "{:.2f}" if "rate" in fin_df.columns[0].lower() else "{:.2f}"
                if "Industry Standard" in fin_df.columns:
                    format_dict["Industry Standard"] = "{:.2f}"
                if "Min" in fin_df.columns:
                    format_dict["Min"] = "{:.2f}"
                if "Max" in fin_df.columns:
                    format_dict["Max"] = "{:.2f}"
                if "Deviation (%)" in fin_df.columns:
                    format_dict["Deviation (%)"] = "{:.2f}%"
                
                st.dataframe(fin_df.style.format(format_dict))
                
                # Plot comparison to standards
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Prepare data
                params = [row["Parameter"] for row in financial_data if "Industry Standard" in row]
                current = [row["Current Value"] for row in financial_data if "Industry Standard" in row]
                standard = [row["Industry Standard"] for row in financial_data if "Industry Standard" in row]
                min_vals = [row["Min"] for row in financial_data if "Min" in row]
                max_vals = [row["Max"] for row in financial_data if "Max" in row]
                
                x = range(len(params))
                
                # Plot bars
                ax.bar([i - 0.2 for i in x], current, width=0.4, label="Current Value", alpha=0.7, color="blue")
                ax.bar([i + 0.2 for i in x], standard, width=0.4, label="Industry Standard", alpha=0.7, color="green")
                
                # Plot min/max ranges
                for i, (min_val, max_val) in enumerate(zip(min_vals, max_vals)):
                    ax.plot([i, i], [min_val, max_val], color="red", alpha=0.7)
                    ax.plot([i-0.2, i+0.2], [min_val, min_val], color="red", alpha=0.7)
                    ax.plot([i-0.2, i+0.2], [max_val, max_val], color="red", alpha=0.7)
                
                ax.set_xlabel("Parameter")
                ax.set_ylabel("Value")
                ax.set_title("Financial Assumptions vs. Industry Standards")
                ax.set_xticks(x)
                ax.set_xticklabels(params, rotation=45, ha="right")
                ax.legend()
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
        else:
            st.info("No financial assumptions available.")
    
    # Operations assumptions
    with tabs[1]:
        st.subheader("Operational Assumptions")
        
        operations_assumptions = all_assumptions.get("operations", {})
        
        if operations_assumptions:
            # Create a dataframe with comparison to industry standards
            operations_data = []
            
            for param, value in operations_assumptions.items():
                # Skip derived fields
                if "_standard" in param or "_min" in param or "_max" in param or "_deviation" in param:
                    continue
                
                row = {
                    "Parameter": param.replace("_", " ").title(),
                    "Current Value": value
                }
                
                # Add standard values if available
                std_value = operations_assumptions.get(f"{param}_standard")
                if std_value is not None:
                    row["Industry Standard"] = std_value
                    
                    min_value = operations_assumptions.get(f"{param}_min")
                    max_value = operations_assumptions.get(f"{param}_max")
                    if min_value is not None and max_value is not None:
                        row["Min"] = min_value
                        row["Max"] = max_value
                    
                    deviation = operations_assumptions.get(f"{param}_deviation")
                    if deviation is not None:
                        row["Deviation (%)"] = deviation
                
                operations_data.append(row)
            
            if operations_data:
                ops_df = pd.DataFrame(operations_data)
                
                # Format columns
                format_dict = {}
                if "Current Value" in ops_df.columns:
                    format_dict["Current Value"] = "{:.2f}" if "rate" in ops_df.columns[0].lower() else "{:.2f}"
                if "Industry Standard" in ops_df.columns:
                    format_dict["Industry Standard"] = "{:.2f}"
                if "Min" in ops_df.columns:
                    format_dict["Min"] = "{:.2f}"
                if "Max" in ops_df.columns:
                    format_dict["Max"] = "{:.2f}"
                if "Deviation (%)" in ops_df.columns:
                    format_dict["Deviation (%)"] = "{:.2f}%"
                
                st.dataframe(ops_df.style.format(format_dict))
                
                # Plot comparison to standards (similar to financial plot)
                # (Code would be similar to financial plot)
        else:
            st.info("No operational assumptions available.")
    
    # Sales assumptions
    with tabs[2]:
        st.subheader("Sales Assumptions")
        
        sales_assumptions = all_assumptions.get("sales", {})
        
        if sales_assumptions:
            # Similar display logic as above
            st.dataframe(pd.DataFrame(sales_assumptions.items(), columns=["Parameter", "Value"]))
        else:
            st.info("No sales assumptions available.")
    
    # G&A assumptions
    with tabs[3]:
        st.subheader("G&A Assumptions")
        
        ga_assumptions = all_assumptions.get("g_and_a", {})
        
        if ga_assumptions:
            # Similar display logic as above
            st.dataframe(pd.DataFrame(ga_assumptions.items(), columns=["Parameter", "Value"]))
        else:
            st.info("No G&A assumptions available.")
    
    # Outsourcing assumptions
    with tabs[4]:
        st.subheader("Outsourcing Assumptions")
        
        outsourcing_assumptions = all_assumptions.get("outsourcing", {})
        
        if outsourcing_assumptions:
            # Similar display logic as above
            st.dataframe(pd.DataFrame(outsourcing_assumptions.items(), columns=["Parameter", "Value"]))
        else:
            st.info("No outsourcing assumptions available.")
    
    # Validate assumptions
    st.subheader("Validate Assumptions")
    
    if st.button("Check Assumptions Against Industry Standards"):
        # Collect all parameters to validate
        parameters_to_validate = {}
        
        # Add financial parameters
        for param, value in financial_assumptions.items():
            if not any(suffix in param for suffix in ["_standard", "_min", "_max", "_deviation"]):
                parameters_to_validate[param] = value
        
        # Add operations parameters
        for param, value in operations_assumptions.items():
            if not any(suffix in param for suffix in ["_standard", "_min", "_max", "_deviation"]):
                parameters_to_validate[param] = value
        
        # Similar for other categories
        
        # Validate parameters
        validation_results = assumptions_service.validate_scenario_parameters(
            active_scenario_id, parameters_to_validate
        )
        
        if "error" in validation_results:
            st.error(validation_results["error"])
        else:
            # Display validation results
            if validation_results["valid"]:
                st.success("All assumptions are within industry standard bounds.")
            else:
                st.warning("Some assumptions are outside industry standard bounds.")
            
            # Show out of bounds parameters
            if validation_results["out_of_bounds"]:
                st.subheader("Parameters Outside Bounds")
                
                out_of_bounds_data = []
                for param in validation_results["out_of_bounds"]:
                    out_of_bounds_data.append({
                        "Parameter": param["parameter"].replace("_", " ").title(),
                        "Category": param["category"].title(),
                        "Current Value": param["value"],
                        "Min": param["min"],
                        "Max": param["max"],
                        "Description": param["description"]
                    })
                
                st.dataframe(pd.DataFrame(out_of_bounds_data))
            
            # Show warnings
            if validation_results["warnings"]:
                st.subheader("Parameters Near Bounds")
                
                warnings_data = []
                for param in validation_results["warnings"]:
                    warnings_data.append({
                        "Parameter": param["parameter"].replace("_", " ").title(),
                        "Category": param["category"].title(),
                        "Current Value": param["value"],
                        "Standard Value": param["standard_value"],
                        "Description": param["description"],
                        "Message": param["message"]
                    })
                
                st.dataframe(pd.DataFrame(warnings_data))

# Update the main function to include the new sections
def main():
    # Initialize database if needed
    init_database()
    
    # Initialize session state
    if 'active_scenario_id' not in st.session_state:
        # Check if we have any scenarios
        scenarios_df = get_scenarios()
        if not scenarios_df.empty:
            # Use the first scenario as active by default
            st.session_state.active_scenario_id = scenarios_df.iloc[0]['id']
        else:
            st.session_state.active_scenario_id = None
    
    # Render sidebar for navigation
    section = render_sidebar()
    
    # Render selected section
    if section == "Dashboard":
        render_dashboard(st.session_state.active_scenario_id)
    elif section == "Manage Scenarios":
        render_scenario_management()
    elif section == "Equipment Management":
        render_equipment_management(st.session_state.active_scenario_id)
    elif section == "Product Management":
        render_product_management(st.session_state.active_scenario_id)
    elif section == "Sales Planning":  # New section
        render_sales_planning(st.session_state.active_scenario_id)
    elif section == "G&A Planning":  # New section
        render_ga_planning(st.session_state.active_scenario_id)
    elif section == "Financial Analysis":
        render_financial_analysis(st.session_state.active_scenario_id)
    elif section == "Capacity Planning":
        render_capacity_planning(st.session_state.active_scenario_id)
    elif section == "Assumptions":  # New section
        render_assumptions(st.session_state.active_scenario_id)

# Add to capacity planning section: Code for displaying outsourcing requirements

def render_capacity_planning(active_scenario_id):
    # (existing capacity planning code...)
    
    # Add this section to show outsourcing requirements
    st.subheader("Outsourcing Analysis")
    
    # Select year for outsourcing analysis
    outsourcing_year = st.number_input("Select Year for Outsourcing Analysis", min_value=0, value=2)
    
    if st.button("Analyze Outsourcing Requirements"):
        with st.spinner("Analyzing outsourcing requirements..."):
            # Initialize Sales Service
            session = get_session()
            sales_service = SalesService(session)
            
            # Calculate outsourcing requirements
            outsourcing = sales_service.calculate_outsourcing_requirements(
                active_scenario_id, outsourcing_year
            )
            
            if "error" in outsourcing:
                st.error(outsourcing["error"])
            else:
                # Store in session state to display results
                st.session_state.outsourcing = outsourcing
                st.success("Outsourcing analysis completed!")
                st.experimental_rerun()
    
    # Display outsourcing results if available
    if hasattr(st.session_state, 'outsourcing'):
        outsourcing = st.session_state.outsourcing
        
        if outsourcing["required"]:
            st.warning(f"Outsourcing is recommended for year {outsourcing_year} due to capacity constraints.")
            
            # Show bottlenecks
            if outsourcing["bottlenecks"]:
                st.subheader("Capacity Bottlenecks")
                
                bottlenecks_data = []
                for bottleneck in outsourcing["bottlenecks"]:
                    bottlenecks_data.append({
                        "Equipment": bottleneck["equipment_name"],
                        "Utilization": bottleneck["utilization_pct"],
                        "Severity": bottleneck["severity"].title()
                    })
                
                st.dataframe(pd.DataFrame(bottlenecks_data).style.format({
                    "Utilization": "{:.1f}%"
                }))
            
            # Show outsourcing recommendations by product
            st.subheader("Outsourcing Recommendations by Product")
            
            products_data = []
            for prod_id, data in outsourcing["by_product"].items():
                products_data.append({
                    "Product": data["product_name"],
                    "Internal Capacity": data["internal_capacity_units"],
                    "Market Demand": data["market_demand_units"],
                    "Units to Outsource": data["units_to_outsource"],
                    "Outsourcing Cost": data["outsourcing_cost"]
                })
            
            if products_data:
                st.dataframe(pd.DataFrame(products_data).style.format({
                    "Internal Capacity": "{:,.0f}",
                    "Market Demand": "{:,.0f}",
                    "Units to Outsource": "{:,.0f}",
                    "Outsourcing Cost": "${:,.2f}"
                }))
                
                # Plot outsourcing needs
                fig, ax = plt.subplots(figsize=(10, 6))
                
                products = [data["Product"] for data in products_data]
                internal = [data["Internal Capacity"] for data in products_data]
                outsource = [data["Units to Outsource"] for data in products_data]
                
                x = range(len(products))
                
                ax.bar(x, internal, label="Internal Capacity", alpha=0.7, color="blue")
                ax.bar(x, outsource, bottom=internal, label="Outsourcing Needed", alpha=0.7, color="red")
                
                ax.set_title(f"Production Capacity vs. Market Demand (Year {outsourcing_year})")
                ax.set_xlabel("Product")
                ax.set_ylabel("Units")
                ax.set_xticks(x)
                ax.set_xticklabels(products)
                ax.legend()
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
                
                # Show total outsourcing cost
                st.metric("Total Outsourcing Cost", f"${outsourcing['total_outsourcing_cost']:,.2f}")
        else:
            st.success(f"No outsourcing needed for year {outsourcing_year}. All market demand can be met with internal capacity.")