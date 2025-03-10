import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import os

class MonteCarloSimulation:
    def __init__(self, scenario_manager, scenario_id):
        """
        Initialize Monte Carlo Simulation for a specific scenario
        
        :param scenario_manager: ScenarioManager instance
        :param scenario_id: ID of the base scenario to simulate
        """
        self.scenario_manager = scenario_manager
        self.scenario_id = scenario_id
        self.base_scenario = scenario_manager.session.query(Scenario).filter(Scenario.id == scenario_id).first()
        
        if not self.base_scenario:
            raise ValueError(f"Scenario with ID {scenario_id} not found.")
        
        # Default simulation parameters
        self.simulation_config = {
            "iterations": 1000,
            "variables": {
                "annual_revenue_growth": {
                    "distribution": "normal",
                    "params": {
                        "mean": self.base_scenario.annual_revenue_growth,
                        "std": 0.1  # 10% standard deviation
                    }
                },
                "annual_cost_growth": {
                    "distribution": "normal",
                    "params": {
                        "mean": self.base_scenario.annual_cost_growth,
                        "std": 0.1  # 10% standard deviation
                    }
                },
                "interest_rate": {
                    "distribution": "normal",
                    "params": {
                        "mean": self.base_scenario.interest_rate,
                        "std": 0.02  # 2% standard deviation
                    }
                }
            }
        }
    
    def _generate_variable_samples(self, iterations):
        """
        Generate random samples for simulation variables
        
        :param iterations: Number of simulation iterations
        :return: Dictionary of variable samples
        """
        samples = {}
        for var, config in self.simulation_config["variables"].items():
            distribution = config["distribution"]
            params = config["params"]
            
            if distribution == "normal":
                samples[var] = np.random.normal(
                    loc=params["mean"], 
                    scale=params["std"], 
                    size=iterations
                )
            elif distribution == "uniform":
                samples[var] = np.random.uniform(
                    low=params["min"], 
                    high=params["max"], 
                    size=iterations
                )
            elif distribution == "triangular":
                samples[var] = np.random.triangular(
                    left=params["min"], 
                    mode=params["mode"], 
                    right=params["max"], 
                    size=iterations
                )
            else:
                raise ValueError(f"Unsupported distribution: {distribution}")
        
        return samples
    
    def run_simulation(self, iterations=None, custom_config=None):
        """
        Run Monte Carlo simulation
        
        :param iterations: Number of simulation iterations (optional)
        :param custom_config: Custom simulation configuration (optional)
        :return: Dictionary with simulation results
        """
        # Update configuration if provided
        if iterations:
            self.simulation_config["iterations"] = iterations
        if custom_config:
            self._update_simulation_config(custom_config)
        
        # Get number of iterations
        num_iterations = self.simulation_config["iterations"]
        
        # Generate variable samples
        variable_samples = self._generate_variable_samples(num_iterations)
        
        # Prepare results storage
        simulation_results = {
            "iterations": num_iterations,
            "key_metrics": {
                "net_income": [],
                "roi": [],
                "payback_period": []
            },
            "variable_samples": variable_samples
        }
        
        # Run simulation iterations
        for i in range(num_iterations):
            # Create a temporary scenario variant for each iteration
            variant_name = f"MC Simulation Variant {i+1}"
            variant_description = f"Monte Carlo simulation iteration {i+1}"
            
            # Clone base scenario for each iteration
            variant_scenario = self.scenario_manager.clone_scenario(
                self.scenario_id, 
                variant_name, 
                variant_description
            )
            
            # Update scenario variables with sampled values
            for var, samples in variable_samples.items():
                if hasattr(variant_scenario, var):
                    setattr(variant_scenario, var, samples[i])
            
            # Commit changes
            self.scenario_manager.session.commit()
            
            # Recalculate financial projections
            try:
                from .financial_service import calculate_financial_projections, calculate_key_financial_metrics
                
                # Recalculate projections
                calculate_financial_projections(variant_scenario.id)
                
                # Collect key metrics
                metrics = calculate_key_financial_metrics(variant_scenario.id)
                
                # Store metrics if calculation was successful
                if not isinstance(metrics, dict) or "error" not in metrics:
                    simulation_results["key_metrics"]["net_income"].append(
                        metrics.get("net_income", [0])[-1] if isinstance(metrics.get("net_income"), list) else 0
                    )
                    simulation_results["key_metrics"]["roi"].append(
                        metrics.get("roi", 0)
                    )
                    simulation_results["key_metrics"]["payback_period"].append(
                        metrics.get("payback_period", 0)
                    )
                
                # Optionally delete temporary variant to save database space
                self.scenario_manager.delete_scenario(variant_scenario.id)
            
            except Exception as e:
                print(f"Error in simulation iteration {i+1}: {e}")
                # Cleanup variant scenario
                self.scenario_manager.delete_scenario(variant_scenario.id)
        
        return self._analyze_simulation_results(simulation_results)
    
    def _update_simulation_config(self, custom_config):
        """
        Update simulation configuration
        
        :param custom_config: Dictionary with configuration updates
        """
        # Deep update of configuration
        for key, value in custom_config.items():
            if key == "variables":
                for var, var_config in value.items():
                    if var in self.simulation_config["variables"]:
                        self.simulation_config["variables"][var].update(var_config)
            else:
                self.simulation_config[key] = value
    
    def _analyze_simulation_results(self, simulation_results):
        """
        Analyze and summarize simulation results
        
        :param simulation_results: Dictionary of simulation results
        :return: Analyzed results dictionary
        """
        analysis = {
            "summary_statistics": {},
            "probability_distributions": {},
            "confidence_intervals": {}
        }
        
        # Analyze each key metric
        for metric, values in simulation_results["key_metrics"].items():
            if not values:
                continue
            
            # Summary statistics
            analysis["summary_statistics"][metric] = {
                "mean": np.mean(values),
                "median": np.median(values),
                "std_dev": np.std(values),
                "min": np.min(values),
                "max": np.max(values)
            }
            
            # 90% Confidence Interval
            analysis["confidence_intervals"][metric] = {
                "lower": np.percentile(values, 5),
                "upper": np.percentile(values, 95)
            }
        
        # Visualize results
        self._plot_simulation_results(simulation_results)
        
        return {
            "raw_results": simulation_results,
            "analysis": analysis
        }
    
    def _plot_simulation_results(self, simulation_results):
        """
        Create visualizations of simulation results
        
        :param simulation_results: Dictionary of simulation results
        """
        # Create output directory if it doesn't exist
        output_dir = "monte_carlo_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # Plot key metrics distributions
        for metric, values in simulation_results["key_metrics"].items():
            if not values:
                continue
            
            plt.figure(figsize=(10, 6))
            plt.hist(values, bins=50, edgecolor='black', alpha=0.7)
            plt.title(f"Distribution of {metric.replace('_', ' ').title()}")
            plt.xlabel(metric.replace('_', ' ').title())
            plt.ylabel("Frequency")
            
            # Add vertical lines for key statistics
            mean = np.mean(values)
            median = np.median(values)
            plt.axvline(mean, color='r', linestyle='dashed', linewidth=2, label=f'Mean: {mean:.2f}')
            plt.axvline(median, color='g', linestyle='dashed', linewidth=2, label=f'Median: {median:.2f}')
            
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"{metric}_distribution.png"))
            plt.close()
        
        # Plot input variable correlations
        var_values = list(simulation_results["variable_samples"].values())
        var_names = list(simulation_results["variable_samples"].keys())
        
        plt.figure(figsize=(10, 8))
        correlation_matrix = np.corrcoef(var_values)
        plt.imshow(correlation_matrix, cmap='coolwarm', interpolation='nearest')
        plt.colorbar()
        plt.xticks(range(len(var_names)), var_names, rotation=45)
        plt.yticks(range(len(var_names)), var_names)
        plt.title("Correlation of Simulation Input Variables")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "variable_correlations.png"))
        plt.close()

# Extension method for ScenarioManager to create Monte Carlo simulation
def create_monte_carlo_simulation(self, scenario_id):
    """
    Create a Monte Carlo simulation for a given scenario
    
    :param scenario_id: ID of the scenario to simulate
    :return: MonteCarloSimulation instance
    """
    return MonteCarloSimulation(self, scenario_id)

# Attach the method to ScenarioManager
ScenarioManager.create_monte_carlo_simulation = create_monte_carlo_simulation