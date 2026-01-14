from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from schemas.project_spec import AgentState
from agents.planner import PlannerAgent
from agents.generator import GeneratorAgent
from agents.verifier import VerifierAgent
from agents.repair import RepairAgent
from agents.modernizer import ModernizerAgent
from agents.integrator import IntegratorAgent
from dotenv import load_dotenv
import os

load_dotenv()

def create_workflow():
    """Build the multi-agent LangGraph workflow"""
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
    
    planner = PlannerAgent(llm)
    generator = GeneratorAgent(llm)
    verifier = VerifierAgent(llm)
    repair = RepairAgent(llm)
    modernizer = ModernizerAgent(llm)
    integrator = IntegratorAgent()
    
    workflow = StateGraph(AgentState)
    
    # Define nodes
    def plan_node(state: AgentState) -> AgentState:
        print("📋 Planning project structure...")
        project_spec = planner.plan(state.user_query)
        state.project_spec = project_spec
        return state
    
    def generate_node(state: AgentState) -> AgentState:
        print("🔨 Generating code files...")
        files = generator.generate_files(state.project_spec)
        state.generated_files = files
        return state
    
    def modernize_node(state: AgentState) -> AgentState:
        print("🔄 Modernizing code to latest patterns...")
        modern_files = modernizer.modernize_files(state.generated_files)
        state.generated_files = modern_files
        return state
    
    def verify_node(state: AgentState) -> AgentState:
        print("✅ Verifying code quality...")
        results, errors = verifier.verify_files(state.generated_files)
        state.verification_results = results
        state.errors = errors
        return state
    
    def repair_node(state: AgentState) -> AgentState:
        print(f"🔧 Repairing errors (attempt {state.iteration_count + 1})...")
        fixed_files = repair.repair_files(state.generated_files, state.errors)
        state.generated_files = fixed_files
        state.iteration_count += 1
        state.errors = []
        return state
    
    def integrate_node(state: AgentState) -> AgentState:
        print("📦 Packaging project...")
        zip_path = integrator.package_project(
            state.project_spec,
            state.generated_files
        )
        state.final_zip_path = zip_path
        return state
    
    def should_repair(state: AgentState) -> str:
        """Decide whether to repair or proceed"""
        if state.errors and state.iteration_count < state.max_iterations:
            return "repair"
        return "integrate"
    
    # Add nodes
    workflow.add_node("plan", plan_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("modernize", modernize_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("repair", repair_node)
    workflow.add_node("integrate", integrate_node)
    
    # Add edges
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "generate")
    workflow.add_edge("generate", "modernize")
    workflow.add_edge("modernize", "verify")
    workflow.add_conditional_edges("verify", should_repair, {
        "repair": "repair",
        "integrate": "integrate"
    })
    workflow.add_edge("repair", "verify")
    workflow.add_edge("integrate", END)
    
    return workflow.compile()