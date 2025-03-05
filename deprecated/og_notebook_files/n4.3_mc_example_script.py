# Create Monte Carlo simulation for a specific scenario
mc_simulation = scenario_manager.create_monte_carlo_simulation(base_scenario_id)

# Run simulation with default parameters
results = mc_simulation.run_simulation()

# Or customize simulation
custom_config = {
    "iterations": 2000,
    "variables": {
        "annual_revenue_growth": {
            "distribution": "normal",
            "params": {
                "mean": 0.1,  # 10% growth
                "std": 0.05   # 5% standard deviation
            }
        }
    }
}
custom_results = mc_simulation.run_simulation(custom_config=custom_config)