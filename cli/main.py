import click
from agents.jira_agent import JiraAgent
from agents.designer_agent import DesignerAgent
from agents.script_gen_agent import ScriptGenAgent
from agents.xray_agent import XRayAgent
from agents.performance_agent import PerformanceAgent
from agents.data_agent import DataAgent
from agents.reporting_agent import ReportingAgent
from agents.security_agent import SecurityAgent
from core.config import Config
from rich.console import Console
import json

console = Console()

@click.group()
def cli():
    """SAINT: Smart AI-driven Integrated Network for Testing"""
    Config.validate()

@cli.command(name="jira-agent")
@click.option('--story', required=True, help='JIRA Story Key')
def jira_cmd(story):
    """Extract and analyze a JIRA story."""
    agent = JiraAgent()
    data = agent.get_story_details(story)
    analysis = agent.analyze_story(data)
    console.print(f"[bold green]JIRA Analysis for {story}:[/bold green]\n{analysis}")

@cli.command(name="testcase-agent")
@click.option('--analysis', required=True, help='Story analysis text')
def testcase_cmd(analysis):
    """Generate Gherkin and test cases from analysis."""
    agent = DesignerAgent()
    gherkin = agent.generate_gherkin(analysis)
    cases = agent.generate_test_cases(gherkin)
    console.print(f"[bold green]Generated Gherkin:[/bold green]\n{gherkin}")
    console.print(f"[bold blue]Generated Test Cases:[/bold blue]\n{cases}")

@cli.command(name="script-agent")
@click.option('--gherkin', required=True, help='Gherkin scenario')
@click.option('--type', default='web', help='Test type (web/api/graphql)')
def script_cmd(gherkin, type):
    """Generate Playwright scripts from Gherkin."""
    agent = ScriptGenAgent()
    script = agent.generate_playwright_script(gherkin, type)
    console.print(f"[bold green]Generated {type} Script:[/bold green]\n{script}")

@cli.command(name="data-agent")
@click.option('--schema', required=True, help='Data schema or description')
@click.option('--count', default=5, help='Number of records')
def data_cmd(schema, count):
    """Generate synthetic test data."""
    agent = DataAgent()
    data = agent.generate_test_data(schema, count)
    console.print(f"[bold green]Generated Test Data:[/bold green]\n{data}")

@cli.command(name="xray-agent")
@click.option('--cases', required=True, help='Test cases text')
def xray_cmd(cases):
    """Map and sync test cases to X-Ray."""
    agent = XRayAgent()
    mapping = agent.map_test_cases_to_xray(cases)
    console.print(f"[bold green]X-Ray Mapping:[/bold green]\n{mapping}")

@cli.command(name="perf-agent")
@click.option('--spec', required=True, help='API Specification')
def perf_cmd(spec):
    """Generate Locust performance scripts."""
    agent = PerformanceAgent()
    script = agent.generate_locust_script(spec)
    console.print(f"[bold green]Generated Performance Script:[/bold green]\n{script}")

@cli.command(name="security-agent")
@click.option('--spec', required=True, help='API Specification')
def security_cmd(spec):
    """Generate security test scenarios."""
    agent = SecurityAgent()
    scenarios = agent.generate_security_scenarios(spec)
    console.print(f"[bold green]Security Scenarios:[/bold green]\n{scenarios}")

@cli.command(name="report-agent")
@click.option('--results', required=True, help='Raw test results')
def report_cmd(results):
    """Generate executive summary report."""
    agent = ReportingAgent()
    summary = agent.generate_executive_summary(results)
    console.print(f"[bold green]Executive Summary:[/bold green]\n{summary}")

@cli.command(name="full-cycle")
@click.option('--story', required=True, help='JIRA Story Key')
def full_cycle(story):
    """Run the complete end-to-end AI testing cycle."""
    # Orchestration logic...
    console.print(f"[bold cyan]Running full SAINT cycle for {story}...[/bold cyan]")
    # (Implementation similar to previous version but calling internal methods)

if __name__ == '__main__':
    cli()
